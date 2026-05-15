from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class BenchmarkStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"


class MetricResult(BaseModel):
    name: str
    your_value: Optional[float] = None
    paper_value: Optional[str] = None
    unit: str = ""
    higher_is_better: bool = True
    gap_pct: Optional[float] = None


class BenchmarkResult(BaseModel):
    status: BenchmarkStatus
    dataset_name: str
    dataset_rows: int
    dataset_cols: int
    metrics: list[MetricResult] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    interpretation: str = ""
    error_message: Optional[str] = None


class BenchmarkResponse(BaseModel):
    success: bool = True
    arxiv_id: Optional[str]
    paper_title: str
    key_algorithm: str
    benchmark: BenchmarkResult
    tokens_used: int = 0
    message: str = "Benchmark complete"
