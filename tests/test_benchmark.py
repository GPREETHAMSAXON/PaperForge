import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.paper import PaperAnalysis, ImplementationDifficulty
from app.models.benchmark import BenchmarkResult, BenchmarkStatus, MetricResult
from app.services.benchmarker import Benchmarker


@pytest.fixture
def client():
    return TestClient(app)


def make_analysis():
    return PaperAnalysis(
        title="Test Paper", problem_statement="Test problem.",
        proposed_method="Test method.", key_algorithm="TestAlgo",
        novelty="Novel.", datasets_used=["Iris"], evaluation_metrics=["accuracy"],
        reported_results={"accuracy": "95%"}, implementation_difficulty=ImplementationDifficulty.EASY,
        dependencies=["numpy", "sklearn"], reproducibility_notes="Reproducible.",
        paper_type="empirical", is_implementable=True,
    )


SAMPLE_CSV = "sepal_length,sepal_width,petal_length,petal_width,species\n5.1,3.5,1.4,0.2,setosa\n4.9,3.0,1.4,0.2,setosa\n6.3,3.3,4.7,1.6,versicolor\n"
SAMPLE_CODE = """
import numpy as np
from sklearn.dummy import DummyClassifier

def run_testalgo(df=None, **kwargs):
    if df is not None and 'species' in df.columns:
        X = df.drop('species', axis=1).values
        y = df['species'].values
        clf = DummyClassifier(strategy='most_frequent')
        clf.fit(X, y)
        predictions = clf.predict(X)
        accuracy = float((predictions == y).mean())
        return {'accuracy': accuracy}
    return {'accuracy': 0.5}

if __name__ == '__main__':
    print(run_testalgo())
"""


class TestBenchmarkerService:
    def test_csv_meta_correct(self):
        b = Benchmarker()
        rows, cols = b._csv_meta(SAMPLE_CSV)
        assert rows == 3
        assert cols == 5

    def test_csv_truncation(self):
        b = Benchmarker()
        big_csv = "col1,col2\n" + "\n".join(f"{i},{i*2}" for i in range(1000))
        truncated = b._truncate_csv(big_csv, max_rows=100)
        lines = truncated.strip().split("\n")
        assert len(lines) == 101  # header + 100 rows

    def test_extract_func_name_from_code(self):
        b = Benchmarker()
        code = "def run_my_algorithm(df=None):\n    pass"
        assert b._extract_func_name(code, "anything") == "my_algorithm"

    def test_extract_func_name_fallback(self):
        b = Benchmarker()
        code = "def some_other_func():\n    pass"
        result = b._extract_func_name(code, "XGBoost Classifier")
        assert "xgboost" in result

    def test_higher_is_better_accuracy(self):
        b = Benchmarker()
        assert b._higher_is_better("accuracy") is True
        assert b._higher_is_better("f1_score") is True

    def test_higher_is_better_loss(self):
        b = Benchmarker()
        assert b._higher_is_better("loss") is False
        assert b._higher_is_better("mse") is False
        assert b._higher_is_better("rmse") is False

    def test_parse_metrics_valid(self):
        b = Benchmarker()
        stdout = 'METRICS: {"accuracy": 0.92, "f1": 0.89}'
        reported = {"accuracy": "95%", "F1": "91%"}
        metrics = b._parse_metrics(stdout, reported)
        assert len(metrics) == 2
        names = [m.name for m in metrics]
        assert "accuracy" in names
        assert "f1" in names

    def test_parse_metrics_gap_calculation(self):
        b = Benchmarker()
        stdout = 'METRICS: {"accuracy": 0.90}'
        reported = {"accuracy": "95%"}
        metrics = b._parse_metrics(stdout, reported)
        assert len(metrics) == 1
        assert metrics[0].gap_pct is not None
        assert metrics[0].gap_pct < 0  # 90% < 95% = negative gap

    def test_parse_metrics_no_metrics_line(self):
        b = Benchmarker()
        stdout = "some output without metrics\nDATASET_INFO: rows=100"
        metrics = b._parse_metrics(stdout, {})
        assert metrics == []

    def test_find_paper_metric_exact(self):
        b = Benchmarker()
        reported = {"BLEU score": "28.4", "accuracy": "92%"}
        assert b._find_paper_metric("bleu_score", reported) == "28.4"
        assert b._find_paper_metric("accuracy", reported) == "92%"

    def test_find_paper_metric_missing(self):
        b = Benchmarker()
        assert b._find_paper_metric("nonexistent", {"accuracy": "90%"}) is None


class TestBenchmarkModels:
    def test_metric_result_valid(self):
        m = MetricResult(name="accuracy", your_value=0.92, paper_value="95%", gap_pct=-3.2)
        assert m.name == "accuracy"
        assert m.your_value == 0.92
        assert m.gap_pct == -3.2

    def test_benchmark_result_success(self):
        r = BenchmarkResult(
            status=BenchmarkStatus.SUCCESS, dataset_name="iris.csv",
            dataset_rows=150, dataset_cols=5,
            metrics=[MetricResult(name="accuracy", your_value=0.92)],
            interpretation="Results are close to paper.",
        )
        assert r.status == BenchmarkStatus.SUCCESS
        assert len(r.metrics) == 1

    def test_benchmark_result_timeout(self):
        r = BenchmarkResult(
            status=BenchmarkStatus.TIMEOUT, dataset_name="big.csv",
            dataset_rows=10000, dataset_cols=50,
            error_message="Timed out after 45s",
        )
        assert r.status == BenchmarkStatus.TIMEOUT
        assert r.error_message is not None


class TestBenchmarkEndpoint:
    def test_invalid_file_type_rejected(self, client):
        response = client.post(
            "/api/v1/benchmark/run",
            data={
                "analysis_json": '{"title":"T","problem_statement":"P","proposed_method":"M","key_algorithm":"K","novelty":"N","datasets_used":[],"evaluation_metrics":[],"reported_results":{},"implementation_difficulty":"easy","dependencies":[],"reproducibility_notes":"R","paper_type":"empirical","is_implementable":true}',
                "generated_code": "def run_k(df=None): return {}",
            },
            files={"csv_file": ("data.txt", b"not a csv", "text/plain")},
        )
        assert response.status_code == 400

    def test_empty_csv_rejected(self, client):
        response = client.post(
            "/api/v1/benchmark/run",
            data={
                "analysis_json": '{"title":"T","problem_statement":"P","proposed_method":"M","key_algorithm":"K","novelty":"N","datasets_used":[],"evaluation_metrics":[],"reported_results":{},"implementation_difficulty":"easy","dependencies":[],"reproducibility_notes":"R","paper_type":"empirical","is_implementable":true}',
                "generated_code": "def run_k(df=None): return {}",
            },
            files={"csv_file": ("data.csv", b"", "text/csv")},
        )
        assert response.status_code == 400

    def test_invalid_analysis_rejected(self, client):
        response = client.post(
            "/api/v1/benchmark/run",
            data={"analysis_json": '{"bad": "data"}', "generated_code": "pass"},
            files={"csv_file": ("data.csv", SAMPLE_CSV.encode(), "text/csv")},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_benchmark_runs_with_mock_e2b(self, client):
        mock_result = BenchmarkResult(
            status=BenchmarkStatus.SUCCESS, dataset_name="iris.csv",
            dataset_rows=3, dataset_cols=5,
            metrics=[MetricResult(name="accuracy", your_value=0.92, paper_value="95%")],
            interpretation="Close to paper results.",
        )
        mock_benchmarker = MagicMock()
        mock_benchmarker.run = AsyncMock(return_value=(mock_result, 150))

        analysis = make_analysis()

        with patch("app.api.routes.benchmark.get_benchmarker", return_value=mock_benchmarker):
            import json
            response = client.post(
                "/api/v1/benchmark/run",
                data={
                    "analysis_json": analysis.model_dump_json(),
                    "generated_code": SAMPLE_CODE,
                    "arxiv_id": "test.12345",
                    "paper_title": "Test Paper",
                    "key_algorithm": "TestAlgo",
                },
                files={"csv_file": ("iris.csv", SAMPLE_CSV.encode(), "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["benchmark"]["status"] == "success"
        assert len(data["benchmark"]["metrics"]) == 1
        assert data["benchmark"]["metrics"][0]["name"] == "accuracy"
