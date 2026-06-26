import pytest

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
