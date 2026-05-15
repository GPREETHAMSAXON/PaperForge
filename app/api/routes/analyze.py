from fastapi import APIRouter, UploadFile, File
from app.models.paper import ParseArxivRequest, AnalyzeResponse
from app.services.parser import fetch_arxiv_paper, parse_uploaded_pdf
from app.services.analyzer import get_analyzer
from app.core.exceptions import (
    PaperFetchError, PaperParseError, PaperTooLargeError, InvalidArxivIdError,
    AnalysisError, ClaudeAPIError,
    http_bad_request, http_not_found, http_payload_too_large,
    http_service_unavailable, http_unprocessable,
)
from app.core.logging import get_logger

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = get_logger(__name__)


@router.post("/arxiv", response_model=AnalyzeResponse)
async def analyze_arxiv(request: ParseArxivRequest) -> AnalyzeResponse:
    try:
        paper = await fetch_arxiv_paper(request.url)
    except InvalidArxivIdError as exc:
        raise http_bad_request(str(exc))
    except PaperFetchError as exc:
        raise http_not_found(str(exc))
    except PaperTooLargeError as exc:
        raise http_payload_too_large(str(exc))
    except PaperParseError as exc:
        raise http_unprocessable(str(exc))
    try:
        analyzer = get_analyzer()
        analysis, tokens_used = await analyzer.analyze(paper)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        raise http_service_unavailable("An unexpected error occurred.")
    return AnalyzeResponse(arxiv_id=paper.arxiv_id, analysis=analysis, tokens_used=tokens_used)


@router.post("/upload", response_model=AnalyzeResponse)
async def analyze_upload(file: UploadFile = File(...)) -> AnalyzeResponse:
    content_type = file.content_type or ''
    if 'pdf' not in content_type and not (file.filename or '').lower().endswith('.pdf'):
        raise http_bad_request(f'Only PDF files accepted. Got: {content_type!r}')
    try:
        pdf_bytes = await file.read()
    except Exception as exc:
        raise http_bad_request(f'Could not read file: {exc}')
    try:
        paper = await parse_uploaded_pdf(pdf_bytes=pdf_bytes, filename=file.filename or 'upload.pdf')
    except PaperTooLargeError as exc:
        raise http_payload_too_large(str(exc))
    except PaperParseError as exc:
        raise http_unprocessable(str(exc))
    try:
        analyzer = get_analyzer()
        analysis, tokens_used = await analyzer.analyze(paper)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))
    return AnalyzeResponse(arxiv_id=paper.arxiv_id, analysis=analysis, tokens_used=tokens_used)