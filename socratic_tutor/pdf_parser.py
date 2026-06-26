from __future__ import annotations

import contextlib
import os
import re
import sys
from pathlib import Path

from .models import ParsedDocument, ParsedPage
from .utils import short_uuid, utc_now


PAGE_MARKER_PATTERNS = [
    r"\n-{3,}\s*\n\s*Page\s+\d+\s*\n-{3,}\s*\n",
    r"\n\s*<!--\s*page\s+\d+\s*-->\s*\n",
    r"\n\s*-----\s*Page\s+\d+\s*-----\s*\n",
    r"\f",
]


def parse_pdf_to_markdown(pdf_path: str) -> ParsedDocument:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported in MVP.")

    markdown = _to_markdown(str(path))
    pages = split_markdown_into_pages(markdown)

    return ParsedDocument(
        document_id=short_uuid("doc"),
        source_path=str(path),
        title=path.stem,
        markdown=markdown,
        pages=pages,
        created_at=utc_now(),
    )


def split_markdown_into_pages(markdown: str) -> list[ParsedPage]:
    text = markdown.strip()
    if not text:
        return [ParsedPage(page_number=1, markdown="")]

    for pattern in PAGE_MARKER_PATTERNS:
        parts = [part.strip() for part in re.split(pattern, text, flags=re.IGNORECASE) if part.strip()]
        if len(parts) > 1:
            return [
                ParsedPage(page_number=index, markdown=part)
                for index, part in enumerate(parts, start=1)
            ]

    heading_parts = re.split(r"\n(?=#{1,2}\s+\S)", text)
    heading_parts = [part.strip() for part in heading_parts if part.strip()]
    if len(heading_parts) > 1:
        return [
            ParsedPage(page_number=index, markdown=part)
            for index, part in enumerate(heading_parts, start=1)
        ]

    return [ParsedPage(page_number=1, markdown=text)]


def _to_markdown(path: str) -> str:
    import pymupdf4llm

    with suppress_native_output():
        return pymupdf4llm.to_markdown(path)


@contextlib.contextmanager
def suppress_native_output():
    """Suppress noisy parser/OCR output written through Python or native fds."""
    sys.stdout.flush()
    sys.stderr.flush()

    stdout_fd = sys.stdout.fileno()
    stderr_fd = sys.stderr.fileno()
    saved_stdout = os.dup(stdout_fd)
    saved_stderr = os.dup(stderr_fd)
    devnull = os.open(os.devnull, os.O_WRONLY)

    try:
        os.dup2(devnull, stdout_fd)
        os.dup2(devnull, stderr_fd)
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved_stdout, stdout_fd)
        os.dup2(saved_stderr, stderr_fd)
        os.close(saved_stdout)
        os.close(saved_stderr)
        os.close(devnull)
