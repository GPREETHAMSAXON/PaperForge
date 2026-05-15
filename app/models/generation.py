from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class GenerationStrategy(str, Enum):
    FULL = "full"          # Complete runnable implementation
    CORE = "core"          # Core algorithm only (for hard papers)
    SKELETON = "skeleton"  # Documented skeleton when paper lacks detail


class SandboxStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"   # E2B not configured / difficulty too high


# ─── Requests ──────────────────────────────────────────────────────────────


class GenerateRequest(BaseModel):
    url: str = Field(..., description="ArXiv URL or ID")
    include_sandbox_test: bool = Field(
        default=False,
        description="Run generated code in E2B sandbox to verify it executes"
    )


class GenerateFromAnalysisRequest(BaseModel):
    """Generate code directly from an existing analysis JSON (skip re-parsing)."""
    arxiv_id: Optional[str] = None
    analysis: dict = Field(..., description="PaperAnalysis JSON from /analyze endpoint")
    include_sandbox_test: bool = Field(default=False)


# ─── Generated code ────────────────────────────────────────────────────────


class GeneratedCode(BaseModel):
    strategy: GenerationStrategy
    language: str = "python"
    code: str = Field(description="The generated Python implementation")
    explanation: str = Field(description="What the code implements and how to use it")
    usage_example: str = Field(description="Minimal runnable usage example")
    install_command: str = Field(description="pip install command for dependencies")
    limitations: str = Field(
        description="What this implementation does NOT cover vs the full paper"
    )
    estimated_lines: int


# ─── Sandbox execution ─────────────────────────────────────────────────────


class SandboxResult(BaseModel):
    status: SandboxStatus
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None


# ─── API responses ─────────────────────────────────────────────────────────


class GenerateResponse(BaseModel):
    success: bool = True
    arxiv_id: Optional[str]
    paper_title: str
    key_algorithm: str
    implementation_difficulty: str
    generated_code: GeneratedCode
    sandbox_result: Optional[SandboxResult] = None
    tokens_used: int
    message: str = "Code generation complete"
