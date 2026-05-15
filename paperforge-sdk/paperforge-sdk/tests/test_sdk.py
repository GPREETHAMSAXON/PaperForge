"""Tests for the PaperForge SDK."""
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import httpx

from paperforge import PaperForge, PaperAnalysis, GeneratedCode, BenchmarkResult
from paperforge.exceptions import (
    PaperNotFoundError, InvalidArxivURLError, TimeoutError,
    ConnectionError, APIError,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────

MOCK_ANALYSIS_RESPONSE = {
    "success": True,
    "arxiv_id": "1706.03762",
    "tokens_used": 3500,
    "analysis": {
        "title": "Attention Is All You Need",
        "problem_statement": "RNNs limit parallelization.",
        "proposed_method": "Transformer uses only attention.",
        "key_algorithm": "Transformer",
        "novelty": "No recurrence or convolutions.",
        "datasets_used": ["WMT 2014 English-German"],
        "evaluation_metrics": ["BLEU"],
        "reported_results": {"BLEU EN-DE": "28.4"},
        "implementation_difficulty": "hard",
        "dependencies": ["torch", "numpy"],
        "reproducibility_notes": "Full details in appendix.",
        "paper_type": "empirical",
        "is_implementable": True,
    },
}

MOCK_GENERATE_RESPONSE = {
    "success": True,
    "arxiv_id": "1706.03762",
    "tokens_used": 2100,
    "paper_title": "Attention Is All You Need",
    "key_algorithm": "Transformer",
    "implementation_difficulty": "hard",
    "generated_code": {
        "strategy": "core",
        "code": "import torch\nimport torch.nn as nn\n\nclass MultiHeadAttention(nn.Module):\n    pass\n\ndef run_transformer(df=None, **kwargs):\n    return {'result': 'ok'}\n",
        "explanation": "Implements multi-head attention mechanism.",
        "usage_example": "attn = MultiHeadAttention(512, 8)\noutput, weights = attn(x, x, x)",
        "install_command": "pip install torch",
        "limitations": "No full training loop.",
        "estimated_lines": 67,
    },
}

MOCK_BENCHMARK_RESPONSE = {
    "success": True,
    "arxiv_id": "1603.02754",
    "paper_title": "XGBoost",
    "key_algorithm": "XGBoost",
    "tokens_used": 150,
    "benchmark": {
        "status": "success",
        "dataset_name": "iris.csv",
        "dataset_rows": 15,
        "dataset_cols": 5,
        "metrics": [
            {
                "name": "accuracy",
                "your_value": 0.92,
                "paper_value": "95%",
                "unit": "",
                "higher_is_better": True,
                "gap_pct": -3.2,
            }
        ],
        "interpretation": "Results are close to paper.",
        "stdout": "Smoke test passed!",
        "execution_time_ms": 6690,
        "error_message": None,
    },
}


def make_mock_response(data: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        content=json.dumps(data).encode(),
        headers={"content-type": "application/json"},
    )


# ─── Client initialization ─────────────────────────────────────────────────

class TestClientInit:
    def test_default_base_url(self):
        pf = PaperForge()
        assert "paperforge" in pf.base_url or "localhost" in pf.base_url

    def test_custom_base_url(self):
        pf = PaperForge(base_url="http://localhost:8000")
        assert pf.base_url == "http://localhost:8000"

    def test_trailing_slash_stripped(self):
        pf = PaperForge(base_url="http://localhost:8000/")
        assert pf.base_url == "http://localhost:8000"

    def test_repr(self):
        pf = PaperForge(base_url="http://localhost:8000")
        assert "localhost:8000" in repr(pf)

    def test_context_manager(self):
        with PaperForge(base_url="http://localhost:8000") as pf:
            assert pf.base_url == "http://localhost:8000"


# ─── Health ────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_dict(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response({"status": "ok", "version": "0.1.0", "environment": "test"})
        with patch.object(pf._client, "get", return_value=mock_resp):
            result = pf.health()
        assert result["status"] == "ok"
        assert "version" in result


# ─── Analyze ───────────────────────────────────────────────────────────────

class TestAnalyze:
    def test_analyze_returns_paper_analysis(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response(MOCK_ANALYSIS_RESPONSE)
        with patch.object(pf._client, "post", return_value=mock_resp):
            result = pf.analyze("https://arxiv.org/abs/1706.03762")
        assert isinstance(result, PaperAnalysis)
        assert result.title == "Attention Is All You Need"
        assert result.key_algorithm == "Transformer"
        assert result.implementation_difficulty == "hard"
        assert result.arxiv_id == "1706.03762"
        assert result.tokens_used == 3500

    def test_analyze_is_hard_property(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response(MOCK_ANALYSIS_RESPONSE)
        with patch.object(pf._client, "post", return_value=mock_resp):
            result = pf.analyze("1706.03762")
        assert result.is_hard is True
        assert result.is_easy is False

    def test_analyze_reported_results(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response(MOCK_ANALYSIS_RESPONSE)
        with patch.object(pf._client, "post", return_value=mock_resp):
            result = pf.analyze("1706.03762")
        assert "BLEU EN-DE" in result.reported_results
        assert result.reported_results["BLEU EN-DE"] == "28.4"

    def test_analyze_404_raises_paper_not_found(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response({"detail": "Paper not found"}, status_code=404)
        with patch.object(pf._client, "post", return_value=mock_resp):
            with pytest.raises(PaperNotFoundError):
                pf.analyze("9999.99999")

    def test_analyze_timeout_raises_timeout_error(self):
        pf = PaperForge(base_url="http://localhost:8000")
        with patch.object(pf._client, "post", side_effect=httpx.TimeoutException("timeout")):
            with pytest.raises(TimeoutError):
                pf.analyze("1706.03762")

    def test_analyze_connection_error(self):
        pf = PaperForge(base_url="http://localhost:9999")
        with patch.object(pf._client, "post", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(ConnectionError):
                pf.analyze("1706.03762")


# ─── Generate ──────────────────────────────────────────────────────────────

class TestGenerate:
    def test_generate_returns_generated_code(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response(MOCK_GENERATE_RESPONSE)
        with patch.object(pf._client, "post", return_value=mock_resp):
            result = pf.generate("1706.03762")
        assert isinstance(result, GeneratedCode)
        assert result.strategy == "core"
        assert result.estimated_lines == 67
        assert "torch" in result.code or "def " in result.code
        assert result.tokens_used == 2100

    def test_generate_from_analysis(self):
        pf = PaperForge(base_url="http://localhost:8000")
        mock_resp = make_mock_response(MOCK_GENERATE_RESPONSE)
        analysis = PaperAnalysis(
            title="Test", problem_statement="P", proposed_method="M",
            key_algorithm="Transformer", novelty="N", datasets_used=[],
            evaluation_metrics=[], reported_results={},
            implementation_difficulty="hard", dependencies=["torch"],
            reproducibility_notes="", paper_type="empirical",
            is_implementable=True, arxiv_id="1706.03762",
        )
        with patch.object(pf._client, "post", return_value=mock_resp):
            result = pf.generate_from_analysis(analysis)
        assert isinstance(result, GeneratedCode)

    def test_code_save_to_file(self, tmp_path):
        code = GeneratedCode(
            strategy="core", code="def run_transformer(): pass",
            explanation="Test", usage_example="run_transformer()",
            install_command="pip install torch", limitations="None",
            estimated_lines=1, arxiv_id="1706.03762",
        )
        saved = code.save(tmp_path / "test.py")
        assert saved.exists()
        content = saved.read_text()
        assert "def run_transformer" in content
        assert "1706.03762" in content

    def test_code_save_to_directory(self, tmp_path):
        code = GeneratedCode(
            strategy="full", code="def run_algo(): pass",
            explanation="Test", usage_example="run_algo()",
            install_command="pip install numpy", limitations="None",
            estimated_lines=1,
        )
        saved = code.save(tmp_path)
        assert saved.name == "paperforge_implementation.py"
        assert saved.exists()


# ─── Paper (full pipeline) ─────────────────────────────────────────────────

class TestPaperPipeline:
    def test_paper_returns_paper_result(self):
        pf = PaperForge(base_url="http://localhost:8000")
        responses = [
            make_mock_response(MOCK_ANALYSIS_RESPONSE),
            make_mock_response(MOCK_GENERATE_RESPONSE),
        ]
        with patch.object(pf._client, "post", side_effect=responses):
            result = pf.paper("1706.03762")
        assert result.arxiv_id == "1706.03762"
        assert result.analysis.key_algorithm == "Transformer"
        assert result.code.strategy == "core"
        assert result.total_tokens == 3500 + 2100

    def test_paper_save_code(self, tmp_path):
        pf = PaperForge(base_url="http://localhost:8000")
        responses = [
            make_mock_response(MOCK_ANALYSIS_RESPONSE),
            make_mock_response(MOCK_GENERATE_RESPONSE),
        ]
        with patch.object(pf._client, "post", side_effect=responses):
            result = pf.paper("1706.03762")
        saved = result.save_code(tmp_path)
        assert saved.exists()


# ─── Benchmark ─────────────────────────────────────────────────────────────

class TestBenchmark:
    def test_benchmark_returns_result(self, tmp_path):
        pf = PaperForge(base_url="http://localhost:8000")
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2,target\n1,2,0\n3,4,1\n")

        analysis = PaperAnalysis(
            title="XGBoost", problem_statement="P", proposed_method="M",
            key_algorithm="XGBoost", novelty="N", datasets_used=[],
            evaluation_metrics=[], reported_results={"accuracy": "95%"},
            implementation_difficulty="easy", dependencies=["sklearn"],
            reproducibility_notes="", paper_type="empirical",
            is_implementable=True, arxiv_id="1603.02754",
        )
        code = GeneratedCode(
            strategy="full", code="def run_xgboost(df=None): return {'accuracy': 0.9}",
            explanation="Test", usage_example="", install_command="pip install sklearn",
            limitations="None", estimated_lines=1,
        )
        mock_resp = make_mock_response(MOCK_BENCHMARK_RESPONSE)
        with patch.object(pf._client, "post", return_value=mock_resp):
            result = pf.benchmark(csv_file, analysis, code)

        assert isinstance(result, BenchmarkResult)
        assert result.status == "success"
        assert result.succeeded is True
        assert len(result.metrics) == 1
        assert result.metrics[0].name == "accuracy"
        assert result.metrics[0].your_value == 0.92
        assert result.metrics[0].gap_pct == -3.2
        assert result.metrics[0].beat_paper is False

    def test_benchmark_missing_csv_raises(self):
        pf = PaperForge(base_url="http://localhost:8000")
        analysis = PaperAnalysis(
            title="T", problem_statement="P", proposed_method="M",
            key_algorithm="K", novelty="N", datasets_used=[],
            evaluation_metrics=[], reported_results={},
            implementation_difficulty="easy", dependencies=[],
            reproducibility_notes="", paper_type="empirical",
            is_implementable=True,
        )
        code = GeneratedCode(
            strategy="full", code="pass", explanation="",
            usage_example="", install_command="", limitations="", estimated_lines=0,
        )
        with pytest.raises(FileNotFoundError):
            pf.benchmark("/nonexistent/file.csv", analysis, code)


# ─── Models ────────────────────────────────────────────────────────────────

class TestModels:
    def test_metric_result_beat_paper_positive_gap(self):
        from paperforge.models import MetricResult
        m = MetricResult(name="accuracy", your_value=0.97, paper_value="95%", gap_pct=2.1)
        assert m.beat_paper is True

    def test_metric_result_beat_paper_negative_gap(self):
        from paperforge.models import MetricResult
        m = MetricResult(name="accuracy", your_value=0.90, paper_value="95%", gap_pct=-5.3)
        assert m.beat_paper is False

    def test_metric_result_loss_inverted(self):
        from paperforge.models import MetricResult
        m = MetricResult(name="loss", your_value=0.1, paper_value="0.2", gap_pct=-50.0, higher_is_better=False)
        assert m.beat_paper is True  # lower loss is better

    def test_benchmark_result_succeeded(self):
        r = BenchmarkResult(
            status="success", dataset_name="test.csv",
            dataset_rows=100, dataset_cols=5,
        )
        assert r.succeeded is True

    def test_benchmark_result_error_not_succeeded(self):
        r = BenchmarkResult(
            status="error", dataset_name="test.csv",
            dataset_rows=0, dataset_cols=0,
            error_message="Execution failed",
        )
        assert r.succeeded is False
