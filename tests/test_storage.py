from socratic_tutor.storage import cache_path, compute_file_hash, load_json, save_json


def test_compute_file_hash_returns_stable_hash(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("same content", encoding="utf-8")

    assert compute_file_hash(path) == compute_file_hash(path)


def test_save_json_creates_file(tmp_path):
    path = tmp_path / "data.json"

    save_json({"ok": True}, path)

    assert path.exists()


def test_load_json_reads_file(tmp_path):
    path = tmp_path / "data.json"
    save_json({"ok": True}, path)

    assert load_json(path) == {"ok": True}


def test_cache_path_includes_pdf_title_and_hash_prefix(tmp_path):
    path = cache_path(
        tmp_path,
        "abcdef1234567890",
        "parsed.json",
        source_path="Lecture 09-1.pdf",
    )

    assert path == tmp_path / "Lecture-09-1_abcdef123456" / "parsed.json"
