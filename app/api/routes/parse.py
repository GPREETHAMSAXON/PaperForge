from fastapi import APIRouter, UploadFile, File
from app.models.paper import ParseArxivRequest, ParseResponse, PaperSource
from app.services.parser import fetch_arxiv_paper, parse_uploaded_pdf
from app.core.exceptions import (
    PaperFetchError, PaperParseError, PaperTooLargeError, InvalidArxivIdError,
    http_bad_request, http_not_found, http_payload_too_large,
    http_service_unavailable, http_unprocessable,
)
from app.core.logging import get_logger

router = APIRouter(prefix="/parse", tags=["parse"])
logger = get_logger(__name__)


@router.post("/arxiv", response_model=ParseResponse)
async def parse_arxiv(request: ParseArxivRequest) -> ParseResponse:
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
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        raise http_service_unavailable("An unexpected error occurred.")
    return ParseResponse(
        arxiv_id=paper.arxiv_id, title=paper.title, authors=paper.authors,
        abstract=paper.abstract, page_count=paper.page_count,
        word_count=paper.word_count, source=PaperSource.ARXIV_URL,
    )


@router.post("/upload", response_model=ParseResponse)
async def parse_upload(file: UploadFile = File(...)) -> ParseResponse:
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
    return ParseResponse(
        arxiv_id=paper.arxiv_id, title=paper.title, authors=paper.authors,
        abstract=paper.abstract, page_count=paper.page_count,
        word_count=paper.word_count, source=PaperSource.PDF_UPLOAD,
    )