import json
import re
from anthropic import AsyncAnthropic, APIStatusError, APIConnectionError, RateLimitError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import AnalysisError, ClaudeAPIError
from app.models.paper import ParsedPaper, PaperAnalysis
from app.utils.text import truncate_for_claude

logger = get_logger(__name__)
settings = get_settings()

# ─── System prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert ML research engineer and technical paper analyst.

Your job is to analyze machine learning and computer science research papers and extract 
structured, actionable information for practitioners who want to understand and implement 
the paper's core contributions.

You are rigorous, precise, and honest. If information is unclear or missing from the paper, 
say so explicitly — do not hallucinate details.

Always respond with valid JSON only. No preamble, no markdown fencing, no explanation outside 
the JSON object."""

# ─── User prompt template ──────────────────────────────────────────────────

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following research paper and return a JSON object 
with exactly these fields:

{{
  "title": "exact paper title",
  "problem_statement": "1-2 sentences: what specific problem does this paper address?",
  "proposed_method": "3-5 sentences: what is the proposed approach or method?",
  "key_algorithm": "name of the core algorithm, architecture, or technique (e.g. Transformer, DDPM, XGBoost)",
  "novelty": "what is specifically new vs prior work? Be precise.",
  "datasets_used": ["list", "of", "datasets", "mentioned"],
  "evaluation_metrics": ["list", "of", "metrics", "used", "e.g. accuracy, F1, BLEU"],
  "reported_results": {{
    "metric_name": "value with units if applicable",
    "another_metric": "value"
  }},
  "implementation_difficulty": "easy|medium|hard",
  "dependencies": ["python", "packages", "needed", "e.g. torch, sklearn, numpy"],
  "reproducibility_notes": "any gaps, missing hyperparameters, private datasets, or warnings for someone trying to reproduce this",
  "paper_type": "one of: empirical, theoretical, survey, system, dataset, position",
  "is_implementable": true
}}

Rules:
- implementation_difficulty: easy = standard sklearn/numpy pipeline; medium = custom training loop or novel architecture; hard = requires significant ML infra or proprietary data
- is_implementable: false if the paper is purely theoretical, a survey, or lacks enough detail to write code
- reported_results: include the headline numbers the paper claims (accuracy, benchmark scores, speedup, etc.)
- dependencies: only include Python packages; do not include CUDA, datasets, or system deps
- All fields are required. Use empty arrays [] or empty objects {{}} if no data is available.
- Return ONLY the JSON object. No markdown, no explanation.

---
PAPER TEXT:
{paper_text}"""


# ─── Analyzer service ──────────────────────────────────────────────────────


class PaperAnalyzer:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def analyze(self, paper: ParsedPaper) -> tuple[PaperAnalysis, int]:
        """
        Analyze a parsed paper using Claude.
        Returns (PaperAnalysis, tokens_used).
        Raises AnalysisError or ClaudeAPIError on failure.
        """
        paper_text = truncate_for_claude(paper.full_text)

        # Inject abstract at top if available — most information-dense section
        if paper.abstract:
            paper_text = f"ABSTRACT:\n{paper.abstract}\n\nFULL TEXT:\n{paper_text}"

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(paper_text=paper_text)

        logger.info(
            "Sending to Claude | model=%s arxiv_id=%s chars=%d",
            settings.claude_model,
            paper.arxiv_id or "upload",
            len(paper_text),
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
            raise ClaudeAPIError(
                f"Could not connect to Claude API: {exc}"
            ) from exc
        except APIStatusError as exc:
            raise ClaudeAPIError(
                f"Claude API error {exc.status_code}: {exc.message}"
            ) from exc

        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        raw_content = response.content[0].text

        logger.info(
            "Claude response received | tokens=%d arxiv_id=%s",
            tokens_used,
            paper.arxiv_id or "upload",
        )

        analysis = self._parse_claude_response(raw_content, paper.arxiv_id)
        return analysis, tokens_used

    def _parse_claude_response(
        self, raw: str, arxiv_id: str | None
    ) -> PaperAnalysis:
        """
        Parse and validate Claude's JSON response into a PaperAnalysis model.
        Handles common formatting issues (extra whitespace, partial fencing).
        """
        # Strip any accidental markdown fencing
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(
                "Claude returned invalid JSON | arxiv_id=%s raw=%s",
                arxiv_id,
                raw[:500],
            )
            raise AnalysisError(
                f"Claude returned malformed JSON. This is rare — please retry. "
                f"Parse error: {exc}"
            ) from exc

        try:
            analysis = PaperAnalysis(**data)
        except Exception as exc:
            logger.error(
                "PaperAnalysis validation failed | arxiv_id=%s error=%s data=%s",
                arxiv_id,
                exc,
                str(data)[:500],
            )
            raise AnalysisError(
                f"Analysis data failed validation: {exc}. "
                "The paper may be in an unusual format — try a different paper."
            ) from exc

        return analysis


# Singleton — reuse across requests (AsyncAnthropic client is safe to share)
_analyzer: PaperAnalyzer | None = None


def get_analyzer() -> PaperAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = PaperAnalyzer()
    return _analyzer
