import re
from anthropic import AsyncAnthropic, APIStatusError, APIConnectionError, RateLimitError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import ClaudeAPIError, AnalysisError
from app.models.paper import PaperAnalysis, ImplementationDifficulty
from app.models.generation import GeneratedCode, GenerationStrategy

logger = get_logger(__name__)
settings = get_settings()

# ─── System prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior ML engineer who specialises in translating research \
papers into clean, production-quality Python code.

Your implementations are:
- Self-contained: all logic in one function or class, no external files needed
- Well-commented: every non-obvious line references the paper section it implements
- Honest: you clearly state what is and isn't implemented vs the full paper
- Runnable: the code executes without errors given correctly-shaped inputs

You never hallucinate API calls or import packages that don't exist.
You never claim to implement something you haven't actually implemented.

Return ONLY a JSON object. No markdown fencing. No explanation outside the JSON."""

# ─── Prompt templates ──────────────────────────────────────────────────────

# For easy/medium papers — full implementation attempt
FULL_PROMPT = """A research paper has been analyzed. Generate a complete Python implementation.

PAPER ANALYSIS:
Title: {title}
Key Algorithm: {key_algorithm}
Problem: {problem_statement}
Method: {proposed_method}
Novelty: {novelty}
Dependencies: {dependencies}
Difficulty: {difficulty}
Reproducibility notes: {reproducibility_notes}

Return a JSON object with exactly these fields:
{{
  "strategy": "full",
  "language": "python",
  "code": "complete Python implementation as a single string with \\n for newlines",
  "explanation": "2-3 sentences: what this code implements and its main entry point",
  "usage_example": "minimal 5-10 line example showing how to call the implementation",
  "install_command": "pip install package1 package2 ...",
  "limitations": "bullet points of what is NOT implemented vs the full paper",
  "estimated_lines": 0
}}

Rules for the code field:
- Implement the core algorithm as described in the paper
- Use a clean function signature: def run_{snake_name}(df=None, **kwargs) -> dict
- Include a if __name__ == "__main__": block with a minimal smoke test
- Add comments like: # Section 3.2: Scaled dot-product attention
- Use only these packages: {dependencies}
- estimated_lines should be the actual line count of your code

Return ONLY the JSON. No markdown, no preamble."""

# For hard papers — core mechanism only
CORE_PROMPT = """A research paper describes a complex algorithm rated as HARD to implement.
Generate a focused implementation of the CORE MECHANISM ONLY — not the full training pipeline.

PAPER ANALYSIS:
Title: {title}
Key Algorithm: {key_algorithm}
Problem: {problem_statement}
Method: {proposed_method}
Dependencies: {dependencies}
Reproducibility notes: {reproducibility_notes}

For a HARD paper, implement only the mathematically defined core operation.
Example: for a Transformer paper, implement the attention mechanism — not the full training loop.
Example: for a diffusion model, implement the forward/reverse process — not the U-Net backbone.

Return a JSON object with exactly these fields:
{{
  "strategy": "core",
  "language": "python",
  "code": "focused Python implementation of the core mechanism only",
  "explanation": "2-3 sentences: exactly what core operation is implemented and what is excluded",
  "usage_example": "minimal example showing the core mechanism in action",
  "install_command": "pip install package1 package2 ...",
  "limitations": "explicit list of what is NOT implemented: training loop, full architecture, etc.",
  "estimated_lines": 0
}}

Rules:
- Focus: implement ONE well-defined mathematical operation from the paper
- The function should be callable standalone without a GPU or large dataset
- estimated_lines should be the actual line count of your code

Return ONLY the JSON. No markdown, no preamble."""

# For non-implementable papers
SKELETON_PROMPT = """A research paper has been flagged as difficult to implement directly
(theoretical, survey, or missing key details).

Generate a well-documented Python SKELETON — class/function stubs with docstrings
that describe what each component should do, based on the paper's description.

PAPER ANALYSIS:
Title: {title}
Key Algorithm: {key_algorithm}
Problem: {problem_statement}
Method: {proposed_method}
Reproducibility notes: {reproducibility_notes}

Return a JSON object with exactly these fields:
{{
  "strategy": "skeleton",
  "language": "python",
  "code": "documented skeleton with stubs and detailed docstrings",
  "explanation": "why a full implementation isn't possible and what the skeleton provides",
  "usage_example": "# This is a skeleton — fill in the TODOs to implement",
  "install_command": "pip install numpy",
  "limitations": "this is a skeleton only — all methods raise NotImplementedError",
  "estimated_lines": 0
}}

Return ONLY the JSON. No markdown, no preamble."""


# ─── Generator service ─────────────────────────────────────────────────────


def _snake(name: str) -> str:
    """Convert algorithm name to snake_case function name."""
    name = re.sub(r"[^\w\s]", "", name.lower())
    return re.sub(r"\s+", "_", name.strip())[:40]


def _select_strategy(analysis: PaperAnalysis) -> GenerationStrategy:
    if not analysis.is_implementable:
        return GenerationStrategy.SKELETON
    if analysis.implementation_difficulty == ImplementationDifficulty.HARD:
        return GenerationStrategy.CORE
    return GenerationStrategy.FULL


def _build_prompt(analysis: PaperAnalysis, strategy: GenerationStrategy) -> str:
    deps = ", ".join(analysis.dependencies) if analysis.dependencies else "numpy"
    common = dict(
        title=analysis.title,
        key_algorithm=analysis.key_algorithm,
        problem_statement=analysis.problem_statement,
        proposed_method=analysis.proposed_method,
        novelty=analysis.novelty,
        dependencies=deps,
        difficulty=analysis.implementation_difficulty.value,
        reproducibility_notes=analysis.reproducibility_notes,
        snake_name=_snake(analysis.key_algorithm),
    )
    if strategy == GenerationStrategy.SKELETON:
        return SKELETON_PROMPT.format(**common)
    if strategy == GenerationStrategy.CORE:
        return CORE_PROMPT.format(**common)
    return FULL_PROMPT.format(**common)


def _parse_response(raw: str, arxiv_id: str | None) -> GeneratedCode:
    cleaned = re.sub(r"^```(?:json|python)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    import json
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(
            "Generator got invalid JSON | arxiv_id=%s raw=%s", arxiv_id, raw[:400]
        )
        raise AnalysisError(
            f"Code generation returned malformed JSON. Please retry. Error: {exc}"
        ) from exc

    # Compute actual line count if model returned 0
    code = data.get("code", "")
    if data.get("estimated_lines", 0) == 0 and code:
        data["estimated_lines"] = len(code.split("\n"))

    try:
        return GeneratedCode(**data)
    except Exception as exc:
        raise AnalysisError(f"Generated code validation failed: {exc}") from exc


class CodeGenerator:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(
        self, analysis: PaperAnalysis, arxiv_id: str | None = None
    ) -> tuple[GeneratedCode, int]:
        """
        Generate Python implementation from a PaperAnalysis.
        Returns (GeneratedCode, tokens_used).
        Strategy is chosen automatically based on difficulty and implementability.
        """
        strategy = _select_strategy(analysis)
        prompt = _build_prompt(analysis, strategy)

        logger.info(
            "Generating code | strategy=%s difficulty=%s arxiv_id=%s",
            strategy.value,
            analysis.implementation_difficulty.value,
            arxiv_id or "upload",
        )

        try:
            response = await self._client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.claude_max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except RateLimitError as exc:
            raise ClaudeAPIError(
                "Claude API rate limit hit. Please wait 60 seconds and retry."
            ) from exc
        except APIConnectionError as exc:
            raise ClaudeAPIError(f"Could not connect to Claude API: {exc}") from exc
        except APIStatusError as exc:
            raise ClaudeAPIError(
                f"Claude API error {exc.status_code}: {exc.message}"
            ) from exc

        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        raw = response.content[0].text

        logger.info(
            "Code generation complete | tokens=%d strategy=%s arxiv_id=%s",
            tokens_used,
            strategy.value,
            arxiv_id or "upload",
        )

        code = _parse_response(raw, arxiv_id)
        return code, tokens_used


# Singleton
_generator: CodeGenerator | None = None


def get_generator() -> CodeGenerator:
    global _generator
    if _generator is None:
        _generator = CodeGenerator()
    return _generator
