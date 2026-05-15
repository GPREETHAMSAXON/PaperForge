import io
import httpx
import fitz  # PyMuPDF
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import (
    PaperFetchError,
    PaperParseError,
    PaperTooLargeError,
    InvalidArxivIdError,
)
from app.models.paper import ParsedPaper, PaperSource
from app.utils.arxiv import extract_arxiv_id, build_pdf_url
from app.utils.text import clean_pdf_text, extract_abstract, count_words

logger = get_logger(__name__)
settings = get_settings()


# ─── PDF parsing core ──────────────────────────────────────────────────────


def parse_pdf_bytes(
    pdf_bytes: bytes,
    source: PaperSource,
    arxiv_id: str | None = None,
    pdf_url: str | None = None,
) -> ParsedPaper:
    """
    Parse raw PDF bytes into a ParsedPaper.
    Raises PaperParseError if the PDF yields no usable text.
    """
    if len(pdf_bytes) > settings.max_pdf_size_bytes:
        raise PaperTooLargeError(
            f"PDF exceeds {settings.max_pdf_size_mb}MB limit "
            f"({len(pdf_bytes) / 1024 / 1024:.1f}MB received)"
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise PaperParseError(f"PyMuPDF could not open PDF: {exc}") from exc

    page_count = len(doc)
    if page_count == 0:
        raise PaperParseError("PDF has no pages")

    # Extract text page by page; fitz handles most encodings
    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text())

    raw_text = "\n".join(pages_text)
    doc.close()

    if not raw_text.strip():
        raise PaperParseError(
            "PDF text extraction yielded no content. "
            "The PDF may be scanned/image-only. "
            "Try the ar5iv.org version of this paper."
        )

    full_text = clean_pdf_text(raw_text)
    abstract = extract_abstract(full_text)

    # Pull title and authors from first ~500 chars (heuristic — Claude refines later)
    title, authors = _heuristic_title_authors(full_text)

    logger.info(
        "Parsed PDF | pages=%d words=%d arxiv_id=%s",
        page_count,
        count_words(full_text),
        arxiv_id or "upload",
    )

    return ParsedPaper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        full_text=full_text,
        page_count=page_count,
        word_count=count_words(full_text),
        source=source,
        pdf_url=pdf_url,
    )


def _heuristic_title_authors(text: str) -> tuple[str, list[str]]:
    """
    Rough heuristic extraction of title/authors from first lines.
    Claude analysis will produce accurate values — this is just a fast placeholder.
    """
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    title = lines[0] if lines else "Unknown"

    # Authors are typically on line 1-3, shorter than title, contain commas
    authors: list[str] = []
    for line in lines[1:5]:
        if "," in line and len(line) < 200 and not any(
            kw in line.lower() for kw in ["abstract", "university", "department", "@"]
        ):
            authors = [a.strip() for a in line.split(",")]
            break

    return title[:200], authors[:10]


# ─── ArXiv fetch ───────────────────────────────────────────────────────────


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(httpx.TransportError),
    reraise=True,
)
async def fetch_arxiv_paper(url_or_id: str) -> ParsedPaper:
    """
    Fetch and parse a paper from arXiv given a URL or ID.
    Retries up to 3 times on network errors with exponential backoff.
    """
    try:
        arxiv_id = extract_arxiv_id(url_or_id)
    except InvalidArxivIdError:
        raise

    pdf_url = build_pdf_url(arxiv_id)
    logger.info("Fetching arXiv paper | id=%s url=%s", arxiv_id, pdf_url)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=settings.arxiv_request_timeout,
        headers={
            "User-Agent": "PaperForge/0.1 (research tool; contact@paperforge.dev)"
        },
    ) as client:
        try:
            response = await client.get(pdf_url)
        except httpx.TimeoutException as exc:
            raise PaperFetchError(
                f"Request to arXiv timed out after {settings.arxiv_request_timeout}s. "
                "Try again or upload the PDF directly."
            ) from exc
        except httpx.TransportError as exc:
            raise PaperFetchError(f"Network error fetching paper: {exc}") from exc

        if response.status_code == 404:
            raise PaperFetchError(
                f"Paper not found on arXiv (404). Check the ID: {arxiv_id}"
            )
        if response.status_code == 403:
            raise PaperFetchError(
                "arXiv returned 403 (rate limited). Wait 60 seconds and retry."
            )
        if response.status_code != 200:
            raise PaperFetchError(
                f"arXiv returned HTTP {response.status_code} for ID {arxiv_id}"
            )

        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type and "octet-stream" not in content_type:
            # arXiv sometimes redirects non-PDF — try ar5iv fallback
            logger.warning(
                "Unexpected content-type from arXiv: %s — may not be a PDF", content_type
            )

        pdf_bytes = response.content

    return parse_pdf_bytes(
        pdf_bytes=pdf_bytes,
        source=PaperSource.ARXIV_URL,
        arxiv_id=arxiv_id,
        pdf_url=pdf_url,
    )


async def parse_uploaded_pdf(pdf_bytes: bytes, filename: str) -> ParsedPaper:
    """Parse a user-uploaded PDF file."""
    logger.info("Parsing uploaded PDF | filename=%s size=%d", filename, len(pdf_bytes))
    return parse_pdf_bytes(
        pdf_bytes=pdf_bytes,
        source=PaperSource.PDF_UPLOAD,
        arxiv_id=None,
        pdf_url=None,
    )
