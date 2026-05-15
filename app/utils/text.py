import re


def clean_pdf_text(raw: str) -> str:
    text = raw
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\f", "\n\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = text.replace("\u2013", "-").replace("\u2014", "--")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_abstract(text: str) -> str:
    patterns = [
        r"Abstract\s*\n+(.*?)(?:\n\n|\n1\s|Introduction)",
        r"ABSTRACT\s*\n+(.*?)(?:\n\n|\n1\s|INTRODUCTION)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            abstract = match.group(1).strip()
            abstract = re.sub(r"\n+", " ", abstract)
            return abstract[:2000]
    return ''


def truncate_for_claude(text: str, max_chars: int = 80000) -> str:
    if len(text) <= max_chars:
        return text
    keep_start = int(max_chars * 0.85)
    keep_end = max_chars - keep_start
    start = text[:keep_start]
    end = text[-keep_end:]
    return start + '\n\n[... middle section truncated for length ...]\n\n' + end


def count_words(text: str) -> int:
    return len(text.split())