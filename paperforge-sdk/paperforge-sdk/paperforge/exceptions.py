"""
PaperForge SDK exceptions.
"""


class PaperForgeError(Exception):
    """Base exception for all PaperForge SDK errors."""
    pass


class APIError(PaperForgeError):
    """Raised when the PaperForge API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"APIError({self.args[0]!r}, status_code={self.status_code})"


class PaperNotFoundError(APIError):
    """Raised when a paper cannot be found on arXiv (404)."""
    pass


class InvalidArxivURLError(PaperForgeError):
    """Raised when an invalid arXiv URL or ID is provided."""
    pass


class ParseError(APIError):
    """Raised when a PDF cannot be parsed (scanned/image-only PDF)."""
    pass


class GenerationError(APIError):
    """Raised when code generation fails."""
    pass


class BenchmarkError(APIError):
    """Raised when a benchmark run fails."""
    pass


class TimeoutError(PaperForgeError):
    """Raised when a request exceeds the configured timeout."""
    pass


class ConnectionError(PaperForgeError):
    """Raised when the SDK cannot connect to the PaperForge API."""
    pass
