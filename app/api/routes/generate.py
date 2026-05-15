from fastapi import APIRouter, UploadFile, File
from app.models.paper import ParseArxivRequest, PaperAnalysis
from app.models.generation import GenerateRequest, GenerateFromAnalysisRequest, GenerateResponse
from app.services.parser import fetch_arxiv_paper, parse_uploaded_pdf
from app.services.analyzer import get_analyzer
from app.services.generator import get_generator
from app.services.sandbox import run_in_sandbox
from app.core.exceptions import (
    PaperFetchError, PaperParseError, PaperTooLargeError, InvalidArxivIdError,
    AnalysisError, ClaudeAPIError,
    http_bad_request, http_not_found, http_payload_too_large,
    http_service_unavailable, http_unprocessable,
)
from app.core.logging import get_logger

router = APIRouter(prefix="/generate", tags=["generate"])
logger = get_logger(__name__)


@router.post(
    "/arxiv",
    response_model=GenerateResponse,
    summary="Fetch from arXiv, analyze, and generate code",
)
async def generate_arxiv(request: GenerateRequest) -> GenerateResponse:
    """
    Full pipeline: fetch → parse → analyze → generate code.

    Strategy is chosen automatically:
    - easy/medium papers → full implementation
    - hard papers → core mechanism only
    - non-implementable → documented skeleton

    Typical latency: 40–90 seconds (two Claude calls).
    Set include_sandbox_test=true to also execute the code in an E2B sandbox.
    """
    # Step 1: Parse
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

    # Step 2: Analyze
    try:
        analyzer = get_analyzer()
        analysis, analyze_tokens = await analyzer.analyze(paper)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))

    # Step 3: Generate code
    try:
        generator = get_generator()
        generated_code, generate_tokens = await generator.generate(analysis, paper.arxiv_id)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in generate_arxiv: %s", exc)
        raise http_service_unavailable("An unexpected error occurred during code generation.")

    # Step 4: Optionally run in sandbox
    sandbox_result = None
    if request.include_sandbox_test:
        sandbox_result = await run_in_sandbox(
            code=generated_code.code,
            install_command=generated_code.install_command,
        )

    return GenerateResponse(
        arxiv_id=paper.arxiv_id,
        paper_title=analysis.title,
        key_algorithm=analysis.key_algorithm,
        implementation_difficulty=analysis.implementation_difficulty.value,
        generated_code=generated_code,
        sandbox_result=sandbox_result,
        tokens_used=analyze_tokens + generate_tokens,
    )


@router.post(
    "/from-analysis",
    response_model=GenerateResponse,
    summary="Generate code from an existing analysis (skip re-parsing)",
)
async def generate_from_analysis(request: GenerateFromAnalysisRequest) -> GenerateResponse:
    """
    Generate code directly from an analysis JSON returned by /analyze/arxiv.

    Use this when you already have the analysis and just want to regenerate
    or retry code generation without re-fetching and re-parsing the paper.
    Faster (~20s) since it skips the parse + analyze steps.
    """
    try:
        analysis = PaperAnalysis(**request.analysis)
    except Exception as exc:
        raise http_bad_request(f"Invalid analysis JSON: {exc}")

    try:
        generator = get_generator()
        generated_code, tokens_used = await generator.generate(analysis, request.arxiv_id)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in generate_from_analysis: %s", exc)
        raise http_service_unavailable("An unexpected error occurred.")

    sandbox_result = None
    if request.include_sandbox_test:
        sandbox_result = await run_in_sandbox(
            code=generated_code.code,
            install_command=generated_code.install_command,
        )

    return GenerateResponse(
        arxiv_id=request.arxiv_id,
        paper_title=analysis.title,
        key_algorithm=analysis.key_algorithm,
        implementation_difficulty=analysis.implementation_difficulty.value,
        generated_code=generated_code,
        sandbox_result=sandbox_result,
        tokens_used=tokens_used,
    )


@router.post(
    "/upload",
    response_model=GenerateResponse,
    summary="Upload PDF, analyze, and generate code",
)
async def generate_upload(
    file: UploadFile = File(...),
    include_sandbox_test: bool = False,
) -> GenerateResponse:
    """Full pipeline for uploaded PDFs."""
    content_type = file.content_type or ""
    if "pdf" not in content_type and not (file.filename or "").lower().endswith(".pdf"):
        raise http_bad_request(f"Only PDF files accepted. Got: {content_type!r}")

    try:
        pdf_bytes = await file.read()
    except Exception as exc:
        raise http_bad_request(f"Could not read file: {exc}")

    try:
        paper = await parse_uploaded_pdf(pdf_bytes=pdf_bytes, filename=file.filename or "upload.pdf")
    except PaperTooLargeError as exc:
        raise http_payload_too_large(str(exc))
    except PaperParseError as exc:
        raise http_unprocessable(str(exc))

    try:
        analyzer = get_analyzer()
        analysis, analyze_tokens = await analyzer.analyze(paper)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))

    try:
        generator = get_generator()
        generated_code, generate_tokens = await generator.generate(analysis, paper.arxiv_id)
    except ClaudeAPIError as exc:
        raise http_service_unavailable(str(exc))
    except AnalysisError as exc:
        raise http_unprocessable(str(exc))

    sandbox_result = None
    if include_sandbox_test:
        sandbox_result = await run_in_sandbox(
            code=generated_code.code,
            install_command=generated_code.install_command,
        )

    return GenerateResponse(
        arxiv_id=paper.arxiv_id,
        paper_title=analysis.title,
        key_algorithm=analysis.key_algorithm,
        implementation_difficulty=analysis.implementation_difficulty.value,
        generated_code=generated_code,
        sandbox_result=sandbox_result,
        tokens_used=analyze_tokens + generate_tokens,
    )
