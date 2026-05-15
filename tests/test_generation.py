import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.paper import PaperAnalysis, ImplementationDifficulty
from app.models.generation import (
    GeneratedCode, GenerationStrategy, SandboxResult, SandboxStatus
)
from app.services.generator import _select_strategy, _snake, _build_prompt


@pytest.fixture
def client():
    return TestClient(app)


# ─── Helper factories ──────────────────────────────────────────────────────


def make_analysis(difficulty: ImplementationDifficulty, implementable: bool = True) -> PaperAnalysis:
    return PaperAnalysis(
        title="Test Paper",
        problem_statement="Testing problem.",
        proposed_method="Testing method.",
        key_algorithm="TestAlgo",
        novelty="Novel testing approach.",
        datasets_used=["TestDataset"],
        evaluation_metrics=["accuracy"],
        reported_results={"accuracy": "95%"},
        implementation_difficulty=difficulty,
        dependencies=["numpy", "sklearn"],
        reproducibility_notes="Fully reproducible.",
        paper_type="empirical",
        is_implementable=implementable,
    )


def make_generated_code(strategy: GenerationStrategy = GenerationStrategy.FULL) -> GeneratedCode:
    return GeneratedCode(
        strategy=strategy,
        language="python",
        code="import numpy as np\n\ndef run_test_algo(df=None, **kwargs):\n    return {'result': 42}\n\nif __name__ == '__main__':\n    print(run_test_algo())",
        explanation="Implements TestAlgo core logic.",
        usage_example="result = run_test_algo()\nprint(result)",
        install_command="pip install numpy sklearn",
        limitations="Does not implement training loop.",
        estimated_lines=6,
    )


# ─── Strategy selection ────────────────────────────────────────────────────


class TestStrategySelection:
    def test_easy_paper_gets_full_strategy(self):
        analysis = make_analysis(ImplementationDifficulty.EASY)
        assert _select_strategy(analysis) == GenerationStrategy.FULL

    def test_medium_paper_gets_full_strategy(self):
        analysis = make_analysis(ImplementationDifficulty.MEDIUM)
        assert _select_strategy(analysis) == GenerationStrategy.FULL

    def test_hard_paper_gets_core_strategy(self):
        analysis = make_analysis(ImplementationDifficulty.HARD)
        assert _select_strategy(analysis) == GenerationStrategy.CORE

    def test_non_implementable_gets_skeleton(self):
        analysis = make_analysis(ImplementationDifficulty.EASY, implementable=False)
        assert _select_strategy(analysis) == GenerationStrategy.SKELETON

    def test_hard_non_implementable_gets_skeleton(self):
        # non-implementable takes priority over difficulty
        analysis = make_analysis(ImplementationDifficulty.HARD, implementable=False)
        assert _select_strategy(analysis) == GenerationStrategy.SKELETON


# ─── Snake case helper ─────────────────────────────────────────────────────


class TestSnakeCase:
    def test_simple_name(self):
        assert _snake("Transformer") == "transformer"

    def test_multi_word(self):
        assert _snake("Attention Is All You Need") == "attention_is_all_you_need"

    def test_special_chars_stripped(self):
        result = _snake("BERT-base (uncased)")
        assert "-" not in result
        assert "(" not in result

    def test_max_length_40(self):
        long_name = "this is a very long algorithm name that exceeds forty characters"
        assert len(_snake(long_name)) <= 40


# ─── Prompt building ───────────────────────────────────────────────────────


class TestPromptBuilding:
    def test_full_prompt_contains_title(self):
        analysis = make_analysis(ImplementationDifficulty.EASY)
        prompt = _build_prompt(analysis, GenerationStrategy.FULL)
        assert "Test Paper" in prompt

    def test_core_prompt_contains_algorithm(self):
        analysis = make_analysis(ImplementationDifficulty.HARD)
        prompt = _build_prompt(analysis, GenerationStrategy.CORE)
        assert "TestAlgo" in prompt

    def test_skeleton_prompt_contains_title(self):
        analysis = make_analysis(ImplementationDifficulty.EASY, implementable=False)
        prompt = _build_prompt(analysis, GenerationStrategy.SKELETON)
        assert "Test Paper" in prompt

    def test_dependencies_in_prompt(self):
        analysis = make_analysis(ImplementationDifficulty.EASY)
        prompt = _build_prompt(analysis, GenerationStrategy.FULL)
        assert "numpy" in prompt


# ─── Generate /from-analysis endpoint ─────────────────────────────────────


class TestGenerateFromAnalysis:
    def _analysis_json(self, difficulty="easy", implementable=True):
        return {
            "title": "Attention Is All You Need",
            "problem_statement": "RNNs are slow.",
            "proposed_method": "Use attention only.",
            "key_algorithm": "Transformer",
            "novelty": "No recurrence.",
            "datasets_used": ["WMT 2014"],
            "evaluation_metrics": ["BLEU"],
            "reported_results": {"BLEU": "28.4"},
            "implementation_difficulty": difficulty,
            "dependencies": ["torch", "numpy"],
            "reproducibility_notes": "Full details in appendix.",
            "paper_type": "empirical",
            "is_implementable": implementable,
        }

    def test_generate_from_analysis_success(self, client):
        mock_code = make_generated_code(GenerationStrategy.CORE)
        mock_gen = MagicMock()
        mock_gen.generate = AsyncMock(return_value=(mock_code, 2500))

        with patch("app.api.routes.generate.get_generator", return_value=mock_gen):
            response = client.post(
                "/api/v1/generate/from-analysis",
                json={
                    "arxiv_id": "1706.03762",
                    "analysis": self._analysis_json(difficulty="hard"),
                    "include_sandbox_test": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["key_algorithm"] == "Transformer"
        assert data["implementation_difficulty"] == "hard"
        assert data["generated_code"]["strategy"] == "core"
        assert data["tokens_used"] == 2500
        assert data["sandbox_result"] is None

    def test_generate_easy_paper_gets_full_strategy(self, client):
        mock_code = make_generated_code(GenerationStrategy.FULL)
        mock_gen = MagicMock()
        mock_gen.generate = AsyncMock(return_value=(mock_code, 1800))

        with patch("app.api.routes.generate.get_generator", return_value=mock_gen):
            response = client.post(
                "/api/v1/generate/from-analysis",
                json={
                    "analysis": self._analysis_json(difficulty="easy"),
                    "include_sandbox_test": False,
                },
            )

        assert response.status_code == 200
        assert response.json()["generated_code"]["strategy"] == "full"

    def test_invalid_analysis_returns_400(self, client):
        response = client.post(
            "/api/v1/generate/from-analysis",
            json={"analysis": {"bad": "data"}},
        )
        assert response.status_code == 400

    def test_missing_analysis_field_returns_422(self, client):
        response = client.post("/api/v1/generate/from-analysis", json={})
        assert response.status_code == 422


# ─── Generate /arxiv endpoint ──────────────────────────────────────────────


class TestGenerateArxiv:
    def test_full_pipeline_success(self, client):
        from tests.test_api import make_mock_paper, make_mock_analysis

        mock_paper = make_mock_paper()
        mock_analysis = make_mock_analysis()
        mock_code = make_generated_code(GenerationStrategy.CORE)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=(mock_analysis, 3500))

        mock_gen = MagicMock()
        mock_gen.generate = AsyncMock(return_value=(mock_code, 2500))

        with patch("app.api.routes.generate.fetch_arxiv_paper", AsyncMock(return_value=mock_paper)):
            with patch("app.api.routes.generate.get_analyzer", return_value=mock_analyzer):
                with patch("app.api.routes.generate.get_generator", return_value=mock_gen):
                    response = client.post(
                        "/api/v1/generate/arxiv",
                        json={"url": "1706.03762", "include_sandbox_test": False},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tokens_used"] == 6000  # 3500 + 2500
        assert "code" in data["generated_code"]

    def test_sandbox_skipped_when_not_requested(self, client):
        from tests.test_api import make_mock_paper, make_mock_analysis

        mock_paper = make_mock_paper()
        mock_analysis = make_mock_analysis()
        mock_code = make_generated_code()

        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=(mock_analysis, 3500))
        mock_gen = MagicMock()
        mock_gen.generate = AsyncMock(return_value=(mock_code, 2000))

        with patch("app.api.routes.generate.fetch_arxiv_paper", AsyncMock(return_value=mock_paper)):
            with patch("app.api.routes.generate.get_analyzer", return_value=mock_analyzer):
                with patch("app.api.routes.generate.get_generator", return_value=mock_gen):
                    response = client.post(
                        "/api/v1/generate/arxiv",
                        json={"url": "1706.03762", "include_sandbox_test": False},
                    )

        assert response.json()["sandbox_result"] is None


# ─── Sandbox service ───────────────────────────────────────────────────────


class TestSandboxService:
    @pytest.mark.asyncio
    async def test_sandbox_skipped_when_e2b_not_installed(self):
        from app.services.sandbox import run_in_sandbox
        with patch.dict("sys.modules", {"e2b_code_interpreter": None}):
            result = await run_in_sandbox("print('hello')", "pip install numpy")
        assert result.status == SandboxStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_sandbox_skipped_when_no_api_key(self):
        from app.services.sandbox import run_in_sandbox
        mock_sandbox_module = MagicMock()
        with patch.dict("sys.modules", {"e2b_code_interpreter": mock_sandbox_module}):
            with patch("app.services.sandbox.settings") as mock_settings:
                mock_settings.e2b_api_key = ""
                result = await run_in_sandbox("print('hello')", "pip install numpy")
        assert result.status == SandboxStatus.SKIPPED


# ─── Generated code model ──────────────────────────────────────────────────


class TestGeneratedCodeModel:
    def test_valid_generated_code(self):
        code = GeneratedCode(
            strategy=GenerationStrategy.FULL,
            language="python",
            code="def run(): pass",
            explanation="Implements X.",
            usage_example="run()",
            install_command="pip install numpy",
            limitations="No GPU support.",
            estimated_lines=1,
        )
        assert code.strategy == GenerationStrategy.FULL
        assert code.language == "python"

    def test_all_strategies_valid(self):
        for strategy in GenerationStrategy:
            code = GeneratedCode(
                strategy=strategy,
                language="python",
                code="pass",
                explanation="test",
                usage_example="pass",
                install_command="pip install numpy",
                limitations="none",
                estimated_lines=1,
            )
            assert code.strategy == strategy
