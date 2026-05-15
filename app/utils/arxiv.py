import re
from app.core.exceptions import InvalidArxivIdError

_ARXIV_ID_PATTERNS = [
    re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)"),
    re.compile(r"arxiv\.org/(?:abs|pdf)/([a-z\-]+/\d{7}(?:v\d+)?)"),
    re.compile(r"^(\d{4}\.\d{4,5}(?:v\d+)?)$"),
    re.compile(r"^([a-z\-]+/\d{7}(?:v\d+)?)$"),
]


def extract_arxiv_id(url_or_id: str) -> str:
    text = url_or_id.strip()
    for pattern in _ARXIV_ID_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    raise InvalidArxivIdError(
        f'Could not extract arXiv ID from: {url_or_id!r}. '
        'Expected format: https://arxiv.org/abs/2301.07041 or bare ID 2301.07041'
    )


def build_pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}"


def build_abs_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/abs/{arxiv_id}"


def strip_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id)