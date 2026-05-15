import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.paper import ParsedPaper, PaperSource, PaperAnalysis, ImplementationDifficulty
from app.core.exceptions import PaperFetchError, PaperParseError, InvalidArxivIdError


@pytest.fixture
def client():
    return TestClient(app)


def make_mock_paper(arxiv_id="2301.07041") -> ParsedPaper:
    return ParsedPaper(
        arxiv_id=arxiv_id,
        title="Attention Is All You Need",
        authors=["Vaswani et al."],
        abstract="We propose the Transformer architecture.",
        full_text="Abstract\n\nWe propose the Transformer." + " text " * 500,
        page_count=15,
        word_count=8000,
        source=PaperSource.ARXIV_URL,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
    )


def make_mock_analysis() -> PaperAnalysis:
    return PaperAnalysis(
        title="Attention Is All You Need",
        problem_statement="Sequential computation limits parallelization in RNNs.",
        proposed_method="The Transformer uses only attention mechanisms, enabling full parallelization.",
        key_algorithm="Transformer",
        novelty="First model relying entirely on self-attention, no recurrence or convolutions.",
        datasets_used=["WMT 2014 English-German", "WMT 2014 English-French"],
        evaluation_metrics=["BLEU"],
        reported_results={"BLEU EN-DE": "28.4", "BLEU EN-FR": "41.0"},
        implementation_difficulty=ImplementationDifficulty.MEDIUM,
        dependencies=["torch", "numpy"],
        reproducibility_notes="Hyperparameters fully specified in paper appendix.",
        paper_type="empirical",
        is_implementable=True,
    )


# ─── Health ────────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data

    def test_root_returns_service_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["service"] == "PaperForge API"


# ─── Parse /arxiv ──────────────────────────────────────────────────────────


class TestParseArxiv:
    def test_valid_arxiv_url_success(self, client):
        mock_paper = make_mock_paper()
        with patch(
            "app.api.routes.parse.fetch_arxiv_paper",
            new_callable=AsyncMock,
            return_value=mock_paper,
        ):
            response = client.post(
                "/api/v1/parse/arxiv",
                json={"url": "https://arxiv.org/abs/2301.07041"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["arxiv_id"] == "2301.07041"
        assert data["title"] == "Attention Is All You Need"
        assert data["page_count"] == 15
        assert data["success"] is True

    def test_invalid_url_returns_422(self, client):
        # Pydantic validator raises ValidationError → FastAPI returns 422
        response = client.post(
            "/api/v1/parse/arxiv",
            json={"url": "https://google.com"},
        )
        assert response.status_code == 422

    def test_paper_not_found_returns_404(self, client):
        with patch(
            "app.api.routes.parse.fetch_arxiv_paper",
            new_callable=AsyncMock,
            side_effect=PaperFetchError("Paper not found"),
        ):
            response = client.post(
                "/api/v1/parse/arxiv",
                json={"url": "https://arxiv.org/abs/9999.99999"},
            )
        assert response.status_code == 404

    def test_parse_error_returns_422(self, client):
        with patch(
            "app.api.routes.parse.fetch_arxiv_paper",
            new_callable=AsyncMock,
            side_effect=PaperParseError("No text extracted"),
        ):
            response = client.post(
                "/api/v1/parse/arxiv",
                json={"url": "https://arxiv.org/abs/2301.07041"},
            )
        assert response.status_code == 422

    def test_missing_url_field_returns_422(self, client):
        response = client.post("/api/v1/parse/arxiv", json={})
        assert response.status_code == 422


# ─── Parse /upload ─────────────────────────────────────────────────────────


class TestParseUpload:
    def test_valid_pdf_upload_success(self, client):
        mock_paper = make_mock_paper()
        mock_paper.arxiv_id = None
        mock_paper.source = PaperSource.PDF_UPLOAD
        with patch(
            "app.api.routes.parse.parse_uploaded_pdf",
            new_callable=AsyncMock,
            return_value=mock_paper,
        ):
            response = client.post(
                "/api/v1/parse/upload",
                files={"file": ("paper.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == "pdf_upload"

    def test_non_pdf_file_returns_400(self, client):
        response = client.post(
            "/api/v1/parse/upload",
            files={"file": ("paper.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400


# ─── Analyze /arxiv ────────────────────────────────────────────────────────


class TestAnalyzeArxiv:
    def test_full_pipeline_success(self, client):
        mock_paper = make_mock_paper()
        mock_analysis = make_mock_analysis()

        with patch(
            "app.api.routes.analyze.fetch_arxiv_paper",
            new_callable=AsyncMock,
            return_value=mock_paper,
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=(mock_analysis, 3500))
            with patch(
                "app.api.routes.analyze.get_analyzer",
                return_value=mock_analyzer,
            ):
                response = client.post(
                    "/api/v1/analyze/arxiv",
                    json={"url": "https://arxiv.org/abs/2301.07041"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["analysis"]["key_algorithm"] == "Transformer"
        assert data["analysis"]["implementation_difficulty"] == "medium"
        assert data["tokens_used"] == 3500
        assert data["analysis"]["is_implementable"] is True

    def test_analysis_returns_datasets(self, client):
        mock_paper = make_mock_paper()
        mock_analysis = make_mock_analysis()

        with patch(
            "app.api.routes.analyze.fetch_arxiv_paper",
            new_callable=AsyncMock,
            return_value=mock_paper,
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=(mock_analysis, 3500))
            with patch("app.api.routes.analyze.get_analyzer", return_value=mock_analyzer):
                response = client.post(
                    "/api/v1/analyze/arxiv",
                    json={"url": "2301.07041"},
                )

        data = response.json()
        assert "WMT 2014 English-German" in data["analysis"]["datasets_used"]

    def test_invalid_url_returns_422(self, client):
        # Pydantic validator raises ValidationError → FastAPI returns 422
        response = client.post(
            "/api/v1/analyze/arxiv",
            json={"url": "not-valid"},
        )
        assert response.status_code == 422
