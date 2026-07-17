import pytest
import pymupdf

from socratic_tutor import pdf_parser
from socratic_tutor.models import ParsedDocument


def test_raises_file_not_found_for_missing_pdf():
    with pytest.raises(FileNotFoundError):
        pdf_parser.parse_pdf_to_markdown("missing.pdf")


def test_raises_value_error_for_non_pdf_file(tmp_path):
    text_file = tmp_path / "lecture.txt"
    text_file.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ValueError):
        pdf_parser.parse_pdf_to_markdown(str(text_file))


def test_returns_parsed_document_for_valid_pdf_fixture(tmp_path, monkeypatch):
    pdf_file = tmp_path / "lecture.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(pdf_parser, "_to_markdown", lambda path: "# Page 1\n\nOverfitting")

    doc = pdf_parser.parse_pdf_to_markdown(str(pdf_file))

    assert isinstance(doc, ParsedDocument)
    assert doc.title == "lecture"
    assert "Overfitting" in doc.markdown
    assert doc.pages


def test_document_id_is_stable_for_same_pdf_content(tmp_path, monkeypatch):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    first.write_bytes(b"%PDF-1.4\nsame content")
    second.write_bytes(first.read_bytes())
    monkeypatch.setattr(pdf_parser, "_to_markdown", lambda path: "Lecture text")

    first_doc = pdf_parser.parse_pdf_to_markdown(str(first))
    second_doc = pdf_parser.parse_pdf_to_markdown(str(second))

    assert first_doc.document_id == second_doc.document_id


def test_rejects_file_with_pdf_extension_but_invalid_signature(tmp_path):
    pdf_file = tmp_path / "fake.pdf"
    pdf_file.write_bytes(b"not a pdf")

    with pytest.raises(ValueError, match="유효한 PDF"):
        pdf_parser.parse_pdf_to_markdown(str(pdf_file))


def test_rejects_damaged_pdf_with_valid_signature(tmp_path):
    pdf_file = tmp_path / "damaged.pdf"
    pdf_file.write_bytes(b"%PDF-1.7\nthis is not a complete pdf")

    with pytest.raises(ValueError, match="손상"):
        pdf_parser.parse_pdf_to_markdown(str(pdf_file))


def test_rejects_pdf_over_page_limit(tmp_path):
    pdf_file = tmp_path / "too-many-pages.pdf"
    document = pymupdf.open()
    for _ in range(pdf_parser.MAX_PDF_PAGES + 1):
        document.new_page()
    document.save(pdf_file)
    document.close()

    with pytest.raises(ValueError, match="최대 200페이지"):
        pdf_parser.parse_pdf_to_markdown(str(pdf_file))


def test_rejects_encrypted_pdf(tmp_path):
    pdf_file = tmp_path / "encrypted.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Private lecture")
    document.save(
        pdf_file,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner-secret",
        user_pw="user-secret",
    )
    document.close()

    with pytest.raises(ValueError, match="암호화된 PDF"):
        pdf_parser.parse_pdf_to_markdown(str(pdf_file))


def test_rejects_pdf_without_extractable_text(tmp_path):
    pdf_file = tmp_path / "scan.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(pdf_file)
    document.close()

    with pytest.raises(ValueError, match="텍스트를 찾을 수 없습니다"):
        pdf_parser.parse_pdf_to_markdown(str(pdf_file))
