from io import BytesIO
import queue

import pytest
from fastapi import HTTPException, UploadFile

from socratic_tutor.web_app import MAX_UPLOAD_BYTES, save_validated_pdf_upload, stream_queue_events


def test_save_validated_pdf_upload_streams_valid_file(tmp_path):
    upload = UploadFile(filename="lecture.pdf", file=BytesIO(b"%PDF-1.7\ncontent"))
    target = tmp_path / "lecture.pdf"

    save_validated_pdf_upload(upload, target)

    assert target.read_bytes() == b"%PDF-1.7\ncontent"


def test_save_validated_pdf_upload_rejects_oversized_file_and_removes_partial_file(tmp_path):
    upload = UploadFile(filename="large.pdf", file=BytesIO(b"%PDF-" + b"x" * MAX_UPLOAD_BYTES))
    target = tmp_path / "large.pdf"

    with pytest.raises(HTTPException) as exc_info:
        save_validated_pdf_upload(upload, target)

    assert exc_info.value.status_code == 413
    assert not target.exists()


def test_save_validated_pdf_upload_rejects_invalid_signature_and_removes_file(tmp_path):
    upload = UploadFile(filename="fake.pdf", file=BytesIO(b"plain text"))
    target = tmp_path / "fake.pdf"

    with pytest.raises(HTTPException) as exc_info:
        save_validated_pdf_upload(upload, target)

    assert exc_info.value.status_code == 400
    assert not target.exists()


def test_stream_queue_events_yields_heartbeat_while_queue_is_idle():
    event_queue = queue.Queue()
    events = stream_queue_events(event_queue, heartbeat_seconds=0.001)

    assert next(events) == ": heartbeat\n\n"

    event_queue.put(None)
    assert list(events) == []


def test_stream_queue_events_forwards_events_until_stop_signal():
    event_queue = queue.Queue()
    event_queue.put('data: {"step": "parsing"}\n\n')
    event_queue.put(None)

    assert list(stream_queue_events(event_queue, heartbeat_seconds=0.001)) == [
        'data: {"step": "parsing"}\n\n'
    ]
