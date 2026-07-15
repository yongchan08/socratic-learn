from __future__ import annotations

import uuid
from datetime import datetime, timezone


MAX_MARKDOWN_CHARS = 80_000


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def short_uuid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def truncate_markdown(markdown: str, max_chars: int = MAX_MARKDOWN_CHARS) -> tuple[str, bool]:
    if len(markdown) <= max_chars:
        return markdown, False

    part = max_chars // 3
    middle_start = max((len(markdown) // 2) - (part // 2), 0)
    middle_end = middle_start + part
    truncated = "\n\n[... truncated middle-aware excerpt ...]\n\n".join(
        [
            markdown[:part],
            markdown[middle_start:middle_end],
            markdown[-part:],
        ]
    )
    return truncated, True
