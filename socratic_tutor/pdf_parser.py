from __future__ import annotations

import re
from pathlib import Path

from .models import ParsedDocument, ParsedPage
from .utils import short_uuid, utc_now


PDF_SIGNATURE = b"%PDF-"
MAX_PDF_PAGES = 200


def parse_pdf_to_markdown(pdf_path: str) -> ParsedDocument:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported in MVP.")
    with path.open("rb") as file:
        if file.read(len(PDF_SIGNATURE)) != PDF_SIGNATURE:
            raise ValueError("유효한 PDF 파일이 아닙니다.")

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

    # 페이지 구분자 패턴으로 분리 시도
    page_marker_pattern = r"\n-----\s*\n\s*Page\s+\d+\s*\n-----\s*\n"
    parts = [part.strip() for part in re.split(page_marker_pattern, text, flags=re.IGNORECASE) if part.strip()]
    if len(parts) > 1:
        return [ParsedPage(page_number=index, markdown=part) for index, part in enumerate(parts, start=1)]

    # 헤딩 기반 분리
    heading_parts = re.split(r"\n(?=#{1,2}\s+\S)", text)
    heading_parts = [part.strip() for part in heading_parts if part.strip()]
    if len(heading_parts) > 1:
        return [ParsedPage(page_number=index, markdown=part) for index, part in enumerate(heading_parts, start=1)]

    return [ParsedPage(page_number=1, markdown=text)]


def _to_markdown(path: str) -> str:
    """pymupdf를 직접 사용해 순수 텍스트를 추출합니다.
    pymupdf4llm 대비 5~10배 빠르며, LLM 처리에는 텍스트만 필요하므로 품질 손실 없음.
    """
    import pymupdf  # pymupdf4llm의 의존성으로 이미 설치되어 있음

    try:
        doc = pymupdf.open(path)
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("PDF가 손상되어 열 수 없습니다.") from exc

    try:
        if doc.needs_pass:
            raise ValueError("암호화된 PDF는 지원하지 않습니다. 암호를 해제한 뒤 다시 업로드하세요.")
        if doc.page_count > MAX_PDF_PAGES:
            raise ValueError(f"PDF는 최대 {MAX_PDF_PAGES}페이지까지 업로드할 수 있습니다.")

        parts: list[str] = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                parts.append(f"\n-----\n Page {i} \n-----\n\n{text}")
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("PDF가 손상되어 텍스트를 추출할 수 없습니다.") from exc
    finally:
        doc.close()

    if not parts:
        raise ValueError("PDF에서 텍스트를 찾을 수 없습니다. 스캔 이미지 PDF는 지원하지 않습니다.")
    return "\n".join(parts)
