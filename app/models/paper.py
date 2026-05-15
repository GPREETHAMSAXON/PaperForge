from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
import re


class ImplementationDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PaperSource(str, Enum):
    ARXIV_URL = "arxiv_url"
    PDF_UPLOAD = "pdf_upload"


class ParseArxivRequest(BaseModel):
    url: str = Field(..., description="ArXiv paper URL or ID")

    @field_validator('url')
    @classmethod
    def validate_arxiv_url(cls, v: str) -> str:
        v = v.strip()
        patterns = [
            r"arxiv\.org/(abs|pdf)/(\d{4}\.\d{4,5}(v\d+)?)",
            r"^(\d{4}\.\d{4,5}(v\d+)?)$",
            r"arxiv\.org/(abs|pdf)/([a-z\-]+/\d{7}(v\d+)?)",
        ]
        for p in patterns:
            if re.search(p, v, re.IGNORECASE):
                return v
        raise ValueError(
            "Must be a valid arXiv URL (e.g. https://arxiv.org/abs/2301.07041) "
            "or bare arXiv ID (e.g. 2301.07041)"
        )


class ParsedPaper(BaseModel):
    arxiv_id: Optional[str] = None
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str
    full_text: str
    page_count: int
    word_count: int
    source: PaperSource
    pdf_url: Optional[str] = None


class PaperAnalysis(BaseModel):
    title: str
    problem_statement: str
    proposed_method: str
    key_algorithm: str
    novelty: str
    datasets_used: list[str] = Field(default_factory=list)
    evaluation_metrics: list[str] = Field(default_factory=list)
    reported_results: dict[str, str] = Field(default_factory=dict)
    implementation_difficulty: ImplementationDifficulty
    dependencies: list[str] = Field(default_factory=list)
    reproducibility_notes: str
    paper_type: str
    is_implementable: bool


class ParseResponse(BaseModel):
    success: bool = True
    arxiv_id: Optional[str]
    title: str
    authors: list[str]
    abstract: str
    page_count: int
    word_count: int
    source: PaperSource
    message: str = "Paper parsed successfully"


class AnalyzeResponse(BaseModel):
    success: bool = True
    arxiv_id: Optional[str]
    analysis: PaperAnalysis
    tokens_used: int
    message: str = "Analysis complete"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str