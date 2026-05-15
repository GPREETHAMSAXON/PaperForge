from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.models.paper import PaperAnalysis
from app.models.benchmark import BenchmarkResponse
from app.services.benchmarker import get_benchmarker
from app.core.exceptions import http_bad_request, http_unprocessable, http_service_unavailable
from app.core.logging import get_logger
import json

router = APIRouter(prefix="/benchmark", tags=["benchmark"])
logger = get_logger(__name__)


@router.post("/run", response_model=BenchmarkResponse, summary="Benchmark generated code against your CSV")
async def run_benchmark(
    csv_file: UploadFile = File(..., description="Your dataset as CSV"),
    analysis_json: str = Form(..., description="PaperAnalysis JSON from /analyze endpoint"),
    generated_code: str = Form(..., description="Generated code from /generate endpoint"),
    arxiv_id: Optional[str] = Form(default=None),
    paper_title: str = Form(default="Unknown Paper"),
    key_algorithm: str = Form(default="Unknown Algorithm"),
) -> BenchmarkResponse:
    """
    Run the generated code against your uploaded CSV dataset.

    Executes in an E2B cloud sandbox — safe, isolated, no GPU required.
    Returns metrics compared to paper-reported results + Claude interpretation.

    Requires E2B_API_KEY in .env. Typical execution: 20-45 seconds.
    """
    # Validate CSV
    content_type = csv_file.content_type or ""
    filename = csv_file.filename or "dataset.csv"
    if "csv" not in content_type and not filename.lower().endswith(".csv"):
        raise http_bad_request("Only CSV files are accepted for benchmarking.")

    try:
        csv_bytes = await csv_file.read()
    except Exception as exc:
        raise http_bad_request(f"Could not read CSV file: {exc}")

    if len(csv_bytes) == 0:
        raise http_bad_request("CSV file is empty.")

    # Parse analysis
    try:
        analysis_data = json.loads(analysis_json)
        analysis = PaperAnalysis(**analysis_data)
    except Exception as exc:
        raise http_bad_request(f"Invalid analysis JSON: {exc}")

    if not generated_code.strip():
        raise http_bad_request("Generated code cannot be empty.")

    # Run benchmark
    try:
        benchmarker = get_benchmarker()
        result, tokens = await benchmarker.run(
            generated_code=generated_code,
            csv_bytes=csv_bytes,
            filename=filename,
            analysis=analysis,
            arxiv_id=arxiv_id,
        )
    except Exception as exc:
        logger.exception("Benchmark failed unexpectedly: %s", exc)
        raise http_service_unavailable(f"Benchmark failed: {exc}")

    return BenchmarkResponse(
        arxiv_id=arxiv_id,
        paper_title=paper_title,
        key_algorithm=key_algorithm,
        benchmark=result,
        tokens_used=tokens,
    )
