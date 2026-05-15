"""
PaperForge Python SDK — main client.
"""
from __future__ import annotations

import httpx
from pathlib import Path
from typing import Optional

from .models import (
    PaperAnalysis, GeneratedCode, BenchmarkResult,
    MetricResult, PaperResult,
)
from .exceptions import (
    APIError, PaperNotFoundError, InvalidArxivURLError,
    ParseError, GenerationError, BenchmarkError,
    TimeoutError, ConnectionError,
)

DEFAULT_BASE_URL = "https://paperforge.onrender.com"
DEFAULT_TIMEOUT = 120.0  # seconds — Claude calls can take 40-90s


class PaperForge:
    """
    PaperForge Python SDK client.

    Converts arXiv research papers into structured methodology extractions
    and runnable Python implementations using Claude AI.

    Args:
        base_url: Base URL of the PaperForge API.
                  Defaults to the hosted API at paperforge.onrender.com.
                  Set to "http://localhost:8000" for local development.
        timeout: Request timeout in seconds. Default 120s.

    Example::

        from paperforge import PaperForge

        pf = PaperForge()

        # Analyze a paper
        analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
        print(analysis.key_algorithm)   # Transformer
        print(analysis.is_hard)         # True

        # Generate code
        code = pf.generate("https://arxiv.org/abs/1706.03762")
        code.save("transformer.py")

        # Full pipeline in one call
        result = pf.paper("https://arxiv.org/abs/1706.03762")
        print(result.analysis.reported_results)
        result.save_code("output/")
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "User-Agent": "paperforge-sdk/0.2.0",
                "Accept": "application/json",
            },
        )

    # ─── Public API ────────────────────────────────────────────────────────

    def health(self) -> dict:
        """
        Check if the PaperForge API is reachable.

        Returns:
            Dict with keys: status, version, environment.

        Example::

            pf.health()
            # {'status': 'ok', 'version': '0.1.0', 'environment': 'production'}
        """
        resp = self._get("/health")
        return resp

    def analyze(self, url: str) -> PaperAnalysis:
        """
        Fetch a paper from arXiv and extract its methodology using Claude.

        Args:
            url: arXiv URL (e.g. ``https://arxiv.org/abs/1706.03762``)
                 or bare ID (e.g. ``1706.03762``).

        Returns:
            :class:`PaperAnalysis` with title, algorithm, difficulty,
            datasets, results, and more.

        Raises:
            InvalidArxivURLError: If the URL is not a valid arXiv URL.
            PaperNotFoundError: If the paper doesn't exist on arXiv.
            ParseError: If the PDF cannot be parsed.
            APIError: For other API errors.

        Example::

            analysis = pf.analyze("1706.03762")
            print(analysis.key_algorithm)        # Transformer
            print(analysis.implementation_difficulty)  # hard
            print(analysis.reported_results)
            # {'WMT 2014 EN-DE BLEU': '28.4', ...}
        """
        data = self._post("/api/v1/analyze/arxiv", {"url": url})
        return self._parse_analysis(data)

    def analyze_pdf(self, path: str | Path) -> PaperAnalysis:
        """
        Analyze a locally stored PDF file.

        Args:
            path: Path to a PDF file on disk.

        Returns:
            :class:`PaperAnalysis`

        Example::

            analysis = pf.analyze_pdf("papers/attention.pdf")
            print(analysis.title)
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        if not p.suffix.lower() == ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {p.suffix}")

        with open(p, "rb") as f:
            resp = self._post_multipart(
                "/api/v1/analyze/upload",
                files={"file": (p.name, f, "application/pdf")},
            )
        return self._parse_analysis(resp)

    def generate(self, url: str) -> GeneratedCode:
        """
        Fetch a paper from arXiv and generate a Python implementation.

        Strategy is chosen automatically based on difficulty:
        - easy/medium → full implementation
        - hard → core mechanism only
        - non-implementable → documented skeleton

        Args:
            url: arXiv URL or bare ID.

        Returns:
            :class:`GeneratedCode` with code, usage example, and limitations.

        Example::

            code = pf.generate("https://arxiv.org/abs/1706.03762")
            print(code.strategy)          # "core"
            print(code.estimated_lines)   # 67
            code.save("attention.py")
            code.print_usage()
        """
        data = self._post(
            "/api/v1/generate/arxiv",
            {"url": url, "include_sandbox_test": False},
        )
        return self._parse_generated_code(data)

    def generate_from_analysis(self, analysis: PaperAnalysis) -> GeneratedCode:
        """
        Generate code from an existing :class:`PaperAnalysis` (skips re-parsing).

        Faster than :meth:`generate` since it skips the fetch + analyze steps.
        Use when you already have an analysis and want to regenerate code.

        Args:
            analysis: A :class:`PaperAnalysis` returned by :meth:`analyze`.

        Returns:
            :class:`GeneratedCode`

        Example::

            analysis = pf.analyze("1706.03762")
            code = pf.generate_from_analysis(analysis)
            code.save("output/")
        """
        analysis_dict = {
            "title": analysis.title,
            "problem_statement": analysis.problem_statement,
            "proposed_method": analysis.proposed_method,
            "key_algorithm": analysis.key_algorithm,
            "novelty": analysis.novelty,
            "datasets_used": analysis.datasets_used,
            "evaluation_metrics": analysis.evaluation_metrics,
            "reported_results": analysis.reported_results,
            "implementation_difficulty": analysis.implementation_difficulty,
            "dependencies": analysis.dependencies,
            "reproducibility_notes": analysis.reproducibility_notes,
            "paper_type": analysis.paper_type,
            "is_implementable": analysis.is_implementable,
        }
        data = self._post(
            "/api/v1/generate/from-analysis",
            {
                "arxiv_id": analysis.arxiv_id,
                "analysis": analysis_dict,
                "include_sandbox_test": False,
            },
        )
        return self._parse_generated_code(data)

    def paper(self, url: str) -> PaperResult:
        """
        Full pipeline: analyze + generate in one call.

        Args:
            url: arXiv URL or bare ID.

        Returns:
            :class:`PaperResult` combining analysis and generated code.

        Example::

            result = pf.paper("https://arxiv.org/abs/1706.03762")
            print(result.analysis.key_algorithm)   # Transformer
            print(result.code.strategy)            # core
            result.save_code("output/")
            print(f"Total tokens used: {result.total_tokens}")
        """
        analysis = self.analyze(url)
        code = self.generate_from_analysis(analysis)
        return PaperResult(
            arxiv_id=analysis.arxiv_id,
            analysis=analysis,
            code=code,
            total_tokens=analysis.tokens_used + code.tokens_used,
        )

    def benchmark(
        self,
        csv_path: str | Path,
        analysis: PaperAnalysis,
        generated_code: GeneratedCode,
    ) -> BenchmarkResult:
        """
        Benchmark generated code against your CSV dataset using E2B sandbox.

        Args:
            csv_path: Path to a CSV file on disk.
            analysis: :class:`PaperAnalysis` from :meth:`analyze`.
            generated_code: :class:`GeneratedCode` from :meth:`generate`.

        Returns:
            :class:`BenchmarkResult` with metrics, interpretation, and stdout.

        Example::

            analysis = pf.analyze("1603.02754")
            code = pf.generate_from_analysis(analysis)
            result = pf.benchmark("data/iris.csv", analysis, code)
            print(result.status)           # "success"
            print(result.interpretation)   # Claude's analysis
            for m in result.metrics:
                print(m.name, m.your_value, m.gap_pct)
        """
        p = Path(csv_path)
        if not p.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        analysis_dict = {
            "title": analysis.title,
            "problem_statement": analysis.problem_statement,
            "proposed_method": analysis.proposed_method,
            "key_algorithm": analysis.key_algorithm,
            "novelty": analysis.novelty,
            "datasets_used": analysis.datasets_used,
            "evaluation_metrics": analysis.evaluation_metrics,
            "reported_results": analysis.reported_results,
            "implementation_difficulty": analysis.implementation_difficulty,
            "dependencies": analysis.dependencies,
            "reproducibility_notes": analysis.reproducibility_notes,
            "paper_type": analysis.paper_type,
            "is_implementable": analysis.is_implementable,
        }

        import json
        with open(p, "rb") as f:
            resp = self._post_multipart(
                "/api/v1/benchmark/run",
                data={
                    "analysis_json": json.dumps(analysis_dict),
                    "generated_code": generated_code.code,
                    "arxiv_id": analysis.arxiv_id or "",
                    "paper_title": analysis.title,
                    "key_algorithm": analysis.key_algorithm,
                },
                files={"csv_file": (p.name, f, "text/csv")},
            )

        b = resp["benchmark"]
        metrics = [
            MetricResult(
                name=m["name"],
                your_value=m.get("your_value"),
                paper_value=m.get("paper_value"),
                unit=m.get("unit", ""),
                higher_is_better=m.get("higher_is_better", True),
                gap_pct=m.get("gap_pct"),
            )
            for m in b.get("metrics", [])
        ]
        return BenchmarkResult(
            status=b["status"],
            dataset_name=b["dataset_name"],
            dataset_rows=b["dataset_rows"],
            dataset_cols=b["dataset_cols"],
            metrics=metrics,
            interpretation=b.get("interpretation", ""),
            stdout=b.get("stdout", ""),
            execution_time_ms=b.get("execution_time_ms", 0),
            error_message=b.get("error_message"),
            tokens_used=resp.get("tokens_used", 0),
        )

    # ─── HTTP helpers ──────────────────────────────────────────────────────

    def _get(self, path: str) -> dict:
        try:
            resp = self._client.get(path)
            return self._handle(resp)
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Request timed out: {exc}") from exc
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Could not connect to PaperForge API at {self.base_url}. "
                "Is the server running?"
            ) from exc

    def _post(self, path: str, body: dict) -> dict:
        try:
            resp = self._client.post(path, json=body)
            return self._handle(resp)
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Request timed out after {self._client.timeout}s. "
                "Paper analysis can take 40-90s — try increasing timeout."
            ) from exc
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Could not connect to PaperForge API at {self.base_url}."
            ) from exc

    def _post_multipart(self, path: str, data: dict = None, files: dict = None) -> dict:
        try:
            resp = self._client.post(path, data=data or {}, files=files or {})
            return self._handle(resp)
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Request timed out: {exc}") from exc
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Could not connect to PaperForge API at {self.base_url}."
            ) from exc

    def _handle(self, resp: httpx.Response) -> dict:
        if resp.status_code == 200:
            return resp.json()
        detail = ""
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text

        if resp.status_code == 404:
            raise PaperNotFoundError(str(detail), status_code=404)
        if resp.status_code == 400:
            raise InvalidArxivURLError(str(detail))
        if resp.status_code == 422:
            raise ParseError(str(detail), status_code=422)
        if resp.status_code == 503:
            raise APIError(str(detail), status_code=503)
        raise APIError(str(detail), status_code=resp.status_code)

    # ─── Parsers ───────────────────────────────────────────────────────────

    def _parse_analysis(self, data: dict) -> PaperAnalysis:
        a = data.get("analysis", data)
        return PaperAnalysis(
            title=a["title"],
            problem_statement=a["problem_statement"],
            proposed_method=a["proposed_method"],
            key_algorithm=a["key_algorithm"],
            novelty=a["novelty"],
            datasets_used=a.get("datasets_used", []),
            evaluation_metrics=a.get("evaluation_metrics", []),
            reported_results=a.get("reported_results", {}),
            implementation_difficulty=a["implementation_difficulty"],
            dependencies=a.get("dependencies", []),
            reproducibility_notes=a.get("reproducibility_notes", ""),
            paper_type=a.get("paper_type", "empirical"),
            is_implementable=a.get("is_implementable", True),
            arxiv_id=data.get("arxiv_id"),
            tokens_used=data.get("tokens_used", 0),
        )

    def _parse_generated_code(self, data: dict) -> GeneratedCode:
        c = data.get("generated_code", data)
        return GeneratedCode(
            strategy=c["strategy"],
            code=c["code"],
            explanation=c["explanation"],
            usage_example=c["usage_example"],
            install_command=c["install_command"],
            limitations=c["limitations"],
            estimated_lines=c.get("estimated_lines", 0),
            arxiv_id=data.get("arxiv_id"),
            tokens_used=data.get("tokens_used", 0),
        )

    # ─── Context manager support ───────────────────────────────────────────

    def __enter__(self) -> "PaperForge":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __repr__(self) -> str:
        return f"PaperForge(base_url={self.base_url!r})"
