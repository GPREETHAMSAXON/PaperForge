import asyncio
import time
import json
import re
from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.paper import PaperAnalysis
from app.models.benchmark import BenchmarkResult, BenchmarkStatus, MetricResult

logger = get_logger(__name__)
settings = get_settings()

BENCHMARK_TIMEOUT = 45

HARNESS_TEMPLATE = '''
import pandas as pd
import numpy as np
import json, sys, warnings, io
warnings.filterwarnings("ignore")

CSV_DATA = """{csv_data}"""
df = pd.read_csv(io.StringIO(CSV_DATA))
print(f"DATASET_INFO: rows={{len(df)}}, cols={{len(df.columns)}}, columns={{list(df.columns)}}")

{generated_code}

try:
    result = run_{func_name}(df)
    if isinstance(result, dict):
        metrics = {{}}
        for k, v in result.items():
            try:
                metrics[k] = float(v)
            except (TypeError, ValueError):
                metrics[k] = str(v)
        print(f"METRICS: {{json.dumps(metrics)}}")
    else:
        print(f"RESULT: {{result}}")
except Exception as e:
    print(f"BENCHMARK_ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
'''

INTERPRET_PROMPT = """Paper: {title} | Algorithm: {key_algorithm}
Paper results: {reported_results}
User dataset: {dataset_rows} rows, {dataset_cols} cols
User metrics: {metrics}
Status: {status}

Write 2-3 sentences: how results compare to paper, likely reason for any gap, one improvement suggestion. Under 80 words. Be specific."""


class Benchmarker:
    def __init__(self):
        self._claude = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def run(self, generated_code, csv_bytes, filename, analysis, arxiv_id=None):
        csv_text = csv_bytes.decode("utf-8", errors="replace")
        rows, cols = self._csv_meta(csv_text)
        logger.info("Benchmark | rows=%d cols=%d arxiv_id=%s", rows, cols, arxiv_id or "upload")

        if len(csv_text) > 50000:
            csv_text = self._truncate_csv(csv_text, 500)

        func_name = self._extract_func_name(generated_code, analysis.key_algorithm)
        harness = HARNESS_TEMPLATE.format(
            csv_data=csv_text.replace('"""', "'''"),
            generated_code=generated_code,
            func_name=func_name,
        )

        start_ms = int(time.time() * 1000)
        out = await self._run_e2b(harness, analysis.dependencies)
        elapsed = int(time.time() * 1000) - start_ms

        if out["status"] == "timeout":
            return BenchmarkResult(
                status=BenchmarkStatus.TIMEOUT,
                dataset_name=filename, dataset_rows=rows, dataset_cols=cols,
                execution_time_ms=elapsed,
                error_message=f"Timed out after {BENCHMARK_TIMEOUT}s. Try a smaller dataset.",
            ), 0

        if out["status"] == "error":
            return BenchmarkResult(
                status=BenchmarkStatus.ERROR,
                dataset_name=filename, dataset_rows=rows, dataset_cols=cols,
                stdout=out.get("stdout", ""), stderr=out.get("stderr", ""),
                execution_time_ms=elapsed,
                error_message=out.get("error", "Execution failed"),
            ), 0

        stdout = out.get("stdout", "")
        stderr = out.get("stderr", "")
        metrics = self._parse_metrics(stdout, analysis.reported_results)
        interpretation, tokens = await self._interpret(analysis, rows, cols, metrics, "success" if metrics else "partial")
        status = BenchmarkStatus.SUCCESS if metrics else BenchmarkStatus.PARTIAL

        return BenchmarkResult(
            status=status, dataset_name=filename, dataset_rows=rows, dataset_cols=cols,
            metrics=metrics, stdout=stdout[:3000], stderr=stderr[:1000],
            execution_time_ms=elapsed, interpretation=interpretation,
        ), tokens

    async def _run_e2b(self, code, dependencies):
        try:
            from e2b_code_interpreter import Sandbox
        except ImportError:
            return {"status": "error", "error": "e2b-code-interpreter not installed"}
        if not settings.e2b_api_key:
            return {"status": "error", "error": "E2B_API_KEY not set in .env"}

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_e2b, code, dependencies),
                timeout=BENCHMARK_TIMEOUT,
            )
        except asyncio.TimeoutError:
            return {"status": "timeout"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _sync_e2b(self, code, dependencies):
        from e2b_code_interpreter import Sandbox
        stdout_lines, stderr_lines = [], []
        safe_deps = list(set(["pandas", "numpy", "scikit-learn"] + [
            d for d in dependencies if d not in ("torch", "tensorflow", "jax")
        ]))
        with Sandbox(api_key=settings.e2b_api_key) as sbx:
            sbx.run_code(
                "import subprocess; subprocess.run(['pip', 'install'] + "
                + repr(safe_deps) + ", capture_output=True)"
            )
            execution = sbx.run_code(code)
            for log in execution.logs.stdout:
                stdout_lines.append(str(log))
            for log in execution.logs.stderr:
                stderr_lines.append(str(log))
            if execution.error:
                return {"status": "error", "stdout": "\n".join(stdout_lines),
                        "stderr": "\n".join(stderr_lines), "error": str(execution.error)}
            return {"status": "success", "stdout": "\n".join(stdout_lines), "stderr": "\n".join(stderr_lines)}

    def _parse_metrics(self, stdout, reported_results):
        metrics = []
        for line in stdout.split("\n"):
            if line.startswith("METRICS:"):
                try:
                    raw = json.loads(line[8:].strip())
                    for k, v in raw.items():
                        paper_val = self._find_paper_metric(k, reported_results)
                        gap = None
                        if paper_val and isinstance(v, float):
                            try:
                                pn = float(re.search(r"[\d.]+", paper_val).group())
                                gap = round((v - pn) / pn * 100, 1)
                            except Exception:
                                pass
                        metrics.append(MetricResult(
                            name=k, your_value=v if isinstance(v, float) else None,
                            paper_value=paper_val,
                            higher_is_better=self._higher_is_better(k), gap_pct=gap,
                        ))
                except Exception:
                    pass
        return metrics

    def _find_paper_metric(self, key, reported):
        kl = key.lower().replace("_", " ")
        for k, v in reported.items():
            if kl in k.lower() or k.lower() in kl:
                return v
        return None

    def _higher_is_better(self, name):
        return not any(w in name.lower() for w in ["loss", "error", "mse", "mae", "rmse", "perplexity"])

    def _extract_func_name(self, code, algorithm):
        m = re.search(r"def run_(\w+)\(", code)
        if m:
            return m.group(1)
        return re.sub(r"[^\w]", "_", algorithm.lower()).strip("_")[:30]

    def _csv_meta(self, csv_text):
        try:
            lines = [l for l in csv_text.strip().split("\n") if l]
            return max(0, len(lines) - 1), len(lines[0].split(",")) if lines else 0
        except Exception:
            return 0, 0

    def _truncate_csv(self, csv_text, max_rows=500):
        lines = csv_text.strip().split("\n")
        return "\n".join([lines[0]] + lines[1:max_rows + 1])

    async def _interpret(self, analysis, rows, cols, metrics, status):
        metrics_str = ", ".join(
            f"{m.name}={m.your_value} (paper: {m.paper_value})" for m in metrics
        ) or "no metrics extracted"
        prompt = INTERPRET_PROMPT.format(
            title=analysis.title, key_algorithm=analysis.key_algorithm,
            reported_results=json.dumps(analysis.reported_results),
            dataset_rows=rows, dataset_cols=cols, metrics=metrics_str, status=status,
        )
        try:
            resp = await self._claude.messages.create(
                model=settings.claude_model, max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip(), resp.usage.input_tokens + resp.usage.output_tokens
        except Exception as exc:
            logger.warning("Interpretation failed: %s", exc)
            return "Benchmark completed. Compare your metrics with the paper results above.", 0


_benchmarker = None

def get_benchmarker():
    global _benchmarker
    if _benchmarker is None:
        _benchmarker = Benchmarker()
    return _benchmarker
