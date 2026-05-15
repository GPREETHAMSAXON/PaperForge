"""
PaperForge Python SDK

Convert arXiv research papers into structured methodology extractions
and runnable Python implementations using Claude AI.

Quick start::

    from paperforge import PaperForge

    pf = PaperForge()

    # Analyze a paper
    analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
    print(analysis.key_algorithm)   # Transformer

    # Generate code
    code = pf.generate("https://arxiv.org/abs/1706.03762")
    code.save("transformer.py")

    # Full pipeline
    result = pf.paper("https://arxiv.org/abs/1706.03762")
    result.save_code("output/")
"""

from .client import PaperForge
from .models import (
    PaperAnalysis,
    GeneratedCode,
    BenchmarkResult,
    MetricResult,
    PaperResult,
)
from .exceptions import (
    PaperForgeError,
    APIError,
    PaperNotFoundError,
    InvalidArxivURLError,
    ParseError,
    GenerationError,
    BenchmarkError,
    TimeoutError,
    ConnectionError,
)

__version__ = "0.2.0"
__author__ = "Saxon (GPREETHAMSAXON)"
__all__ = [
    "PaperForge",
    "PaperAnalysis",
    "GeneratedCode",
    "BenchmarkResult",
    "MetricResult",
    "PaperResult",
    "PaperForgeError",
    "APIError",
    "PaperNotFoundError",
    "InvalidArxivURLError",
    "ParseError",
    "GenerationError",
    "BenchmarkError",
    "TimeoutError",
    "ConnectionError",
]
