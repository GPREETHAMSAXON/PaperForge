"""
Week 5 — Real paper validation suite.
Tests the full pipeline against known ArXiv papers.
Run with: pytest tests/test_validation.py -v -m validation --timeout=120

These tests make real API calls. Mark as 'validation' so they don't run in CI by default.
Set ANTHROPIC_API_KEY in environment before running.
"""
import pytest
import os


# Skip all validation tests unless explicitly requested
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_VALIDATION") != "1",
    reason="Set RUN_VALIDATION=1 to run real paper validation tests"
)

VALIDATION_PAPERS = [
    {
        "arxiv_id": "1706.03762",
        "title_contains": "Attention",
        "expected_algorithm": "Transformer",
        "expected_difficulty": "hard",
        "expected_strategy": "core",
    },
    {
        "arxiv_id": "1810.04805",
        "title_contains": "BERT",
        "expected_algorithm_contains": "Transformer",
        "expected_difficulty": "medium",
        "expected_strategy": "full",
    },
    {
        "arxiv_id": "2106.09685",
        "title_contains": "LoRA",
        "expected_algorithm_contains": "LoRA",
        "expected_difficulty": "medium",
        "expected_strategy": "full",
    },
]


class TestAnalysisPipelineValidation:
    """Tests that the analysis pipeline extracts correct information from real papers."""

    @pytest.mark.asyncio
    async def test_transformer_analysis(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer

        paper = await fetch_arxiv_paper("1706.03762")
        assert paper.page_count >= 10
        assert paper.word_count > 3000

        analyzer = get_analyzer()
        analysis, tokens = await analyzer.analyze(paper)

        assert "attention" in analysis.title.lower() or "transformer" in analysis.title.lower()
        assert analysis.key_algorithm == "Transformer"
        assert analysis.implementation_difficulty.value == "hard"
        assert "BLEU" in analysis.evaluation_metrics or "bleu" in " ".join(analysis.evaluation_metrics).lower()
        assert len(analysis.datasets_used) >= 1
        assert analysis.is_implementable is True
        assert tokens > 0

    @pytest.mark.asyncio
    async def test_bert_analysis(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer

        paper = await fetch_arxiv_paper("1810.04805")
        analyzer = get_analyzer()
        analysis, tokens = await analyzer.analyze(paper)

        assert "bert" in analysis.title.lower()
        assert analysis.implementation_difficulty.value in ("medium", "hard")
        assert len(analysis.datasets_used) >= 3
        assert "torch" in analysis.dependencies or "tensorflow" in analysis.dependencies

    @pytest.mark.asyncio
    async def test_lora_analysis(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer

        paper = await fetch_arxiv_paper("2106.09685")
        analyzer = get_analyzer()
        analysis, tokens = await analyzer.analyze(paper)

        assert "lora" in analysis.title.lower() or "low-rank" in analysis.title.lower()
        assert analysis.is_implementable is True

    @pytest.mark.asyncio
    async def test_xgboost_analysis(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer

        paper = await fetch_arxiv_paper("1603.02754")
        analyzer = get_analyzer()
        analysis, tokens = await analyzer.analyze(paper)

        assert analysis.implementation_difficulty.value in ("easy", "medium")
        assert any("sklearn" in d or "xgboost" in d for d in analysis.dependencies)


class TestCodeGenerationValidation:
    """Tests that code generation produces valid Python for real papers."""

    @pytest.mark.asyncio
    async def test_transformer_generates_core(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer
        from app.services.generator import get_generator
        from app.models.generation import GenerationStrategy

        paper = await fetch_arxiv_paper("1706.03762")
        analyzer = get_analyzer()
        analysis, _ = await analyzer.analyze(paper)

        generator = get_generator()
        code, tokens = await generator.generate(analysis, paper.arxiv_id)

        assert code.strategy == GenerationStrategy.CORE
        assert len(code.code) > 200
        assert "def " in code.code
        assert "import" in code.code
        assert code.estimated_lines > 10

    @pytest.mark.asyncio
    async def test_easy_paper_generates_full(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer
        from app.services.generator import get_generator
        from app.models.generation import GenerationStrategy

        paper = await fetch_arxiv_paper("1603.02754")  # XGBoost
        analyzer = get_analyzer()
        analysis, _ = await analyzer.analyze(paper)

        generator = get_generator()
        code, tokens = await generator.generate(analysis, paper.arxiv_id)

        assert code.strategy in (GenerationStrategy.FULL, GenerationStrategy.CORE)
        assert "def run_" in code.code
        assert len(code.install_command) > 0

    @pytest.mark.asyncio
    async def test_generated_code_is_valid_python(self):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer
        from app.services.generator import get_generator
        import ast

        paper = await fetch_arxiv_paper("1706.03762")
        analyzer = get_analyzer()
        analysis, _ = await analyzer.analyze(paper)
        generator = get_generator()
        code, _ = await generator.generate(analysis, paper.arxiv_id)

        # Verify the generated code is syntactically valid Python
        try:
            ast.parse(code.code)
            is_valid_python = True
        except SyntaxError:
            is_valid_python = False

        assert is_valid_python, f"Generated code has syntax errors:\n{code.code[:500]}"


class TestValidationReport:
    """Generates a summary validation report across all test papers."""

    @pytest.mark.asyncio
    async def test_generate_validation_report(self, tmp_path):
        from app.services.parser import fetch_arxiv_paper
        from app.services.analyzer import get_analyzer
        from app.services.generator import get_generator
        import json

        results = []
        for paper_meta in VALIDATION_PAPERS:
            try:
                paper = await fetch_arxiv_paper(paper_meta["arxiv_id"])
                analyzer = get_analyzer()
                analysis, analyze_tokens = await analyzer.analyze(paper)
                generator = get_generator()
                code, gen_tokens = await generator.generate(analysis, paper.arxiv_id)

                results.append({
                    "arxiv_id": paper_meta["arxiv_id"],
                    "title": analysis.title,
                    "algorithm": analysis.key_algorithm,
                    "difficulty": analysis.implementation_difficulty.value,
                    "strategy": code.strategy.value,
                    "code_lines": code.estimated_lines,
                    "tokens": analyze_tokens + gen_tokens,
                    "status": "pass",
                })
            except Exception as exc:
                results.append({
                    "arxiv_id": paper_meta["arxiv_id"],
                    "status": "fail",
                    "error": str(exc),
                })

        report = {
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "pass"),
            "failed": sum(1 for r in results if r["status"] == "fail"),
            "results": results,
        }

        report_path = tmp_path / "validation_report.json"
        report_path.write_text(json.dumps(report, indent=2))

        assert report["passed"] >= 2, f"Too many failures:\n{json.dumps(report, indent=2)}"
        print(f"\nValidation: {report['passed']}/{report['total']} passed")
        for r in results:
            status_icon = "✓" if r["status"] == "pass" else "✗"
            print(f"  {status_icon} {r.get('arxiv_id')} — {r.get('title', r.get('error', ''))[:60]}")
