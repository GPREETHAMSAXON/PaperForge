import time
import asyncio
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.generation import SandboxResult, SandboxStatus

logger = get_logger(__name__)
settings = get_settings()

SANDBOX_TIMEOUT_SECONDS = 30


async def run_in_sandbox(code: str, install_command: str) -> SandboxResult:
    """
    Execute generated code in an E2B sandboxed Python environment.

    Falls back gracefully if:
    - E2B_API_KEY is not configured
    - e2b package is not installed
    - Sandbox times out

    E2B provides isolated cloud containers — safe to run untrusted generated code.
    Install: pip install e2b-code-interpreter
    Docs: https://e2b.dev/docs
    """
    # Check if E2B is available
    try:
        from e2b_code_interpreter import Sandbox  # type: ignore
    except ImportError:
        logger.info("E2B not installed — skipping sandbox execution")
        return SandboxResult(
            status=SandboxStatus.SKIPPED,
            error_message=(
                "E2B sandbox not available. "
                "Install with: pip install e2b-code-interpreter "
                "and set E2B_API_KEY in your .env"
            ),
        )

    e2b_api_key = getattr(settings, "e2b_api_key", None)
    if not e2b_api_key:
        logger.info("E2B_API_KEY not set — skipping sandbox execution")
        return SandboxResult(
            status=SandboxStatus.SKIPPED,
            error_message="E2B_API_KEY not configured. Add it to your .env to enable sandbox execution.",
        )

    start_ms = int(time.time() * 1000)

    try:
        result = await asyncio.wait_for(
            _execute_in_sandbox(Sandbox, e2b_api_key, code, install_command),
            timeout=SANDBOX_TIMEOUT_SECONDS,
        )
        result.execution_time_ms = int(time.time() * 1000) - start_ms
        return result

    except asyncio.TimeoutError:
        logger.warning("Sandbox execution timed out after %ds", SANDBOX_TIMEOUT_SECONDS)
        return SandboxResult(
            status=SandboxStatus.TIMEOUT,
            error_message=f"Execution timed out after {SANDBOX_TIMEOUT_SECONDS}s. "
            "The code may require more compute than the sandbox allows. "
            "Download the .py file and run locally instead.",
        )
    except Exception as exc:
        logger.error("Sandbox error: %s", exc)
        return SandboxResult(
            status=SandboxStatus.ERROR,
            error_message=f"Sandbox error: {exc}",
        )


async def _execute_in_sandbox(
    Sandbox, api_key: str, code: str, install_command: str
) -> SandboxResult:
    """Inner execution — runs in E2B container."""
    # E2B's SDK is sync; run in thread pool to not block the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _sync_execute, Sandbox, api_key, code, install_command
    )


def _sync_execute(Sandbox, api_key: str, code: str, install_command: str) -> SandboxResult:
    """Synchronous E2B execution — called from thread pool."""
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    with Sandbox(api_key=api_key) as sandbox:
        # Step 1: Install dependencies if needed
        if install_command and install_command.strip() != "pip install":
            packages = install_command.replace("pip install", "").strip()
            if packages:
                logger.info("Installing packages in sandbox: %s", packages)
                install_result = sandbox.run_code(
                    f"import subprocess; subprocess.run(['pip', 'install', {', '.join(repr(p) for p in packages.split())}], capture_output=True)"
                )
                if install_result.error:
                    logger.warning(
                        "Package install warning (non-fatal): %s", install_result.error
                    )

        # Step 2: Run the generated code
        execution = sandbox.run_code(code)

        for log in execution.logs.stdout:
            stdout_lines.append(str(log))
        for log in execution.logs.stderr:
            stderr_lines.append(str(log))

        if execution.error:
            return SandboxResult(
                status=SandboxStatus.ERROR,
                stdout="\n".join(stdout_lines),
                stderr="\n".join(stderr_lines) or str(execution.error),
                error_message=str(execution.error),
            )

        return SandboxResult(
            status=SandboxStatus.SUCCESS,
            stdout="\n".join(stdout_lines) or "Code executed successfully (no output)",
            stderr="\n".join(stderr_lines),
        )
