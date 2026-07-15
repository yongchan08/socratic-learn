from io import BytesIO
import asyncio
import json
import queue

import pytest
from fastapi import HTTPException, UploadFile

from socratic_tutor.web_app import MAX_UPLOAD_BYTES, save_validated_pdf_upload, stream_queue_events
from socratic_tutor import web_app
from socratic_tutor.web_service import WebStudyError


def test_health_returns_uncached_ok_response():
    response = web_app.health()

    assert response.headers["cache-control"] == "no-store"
    assert json.loads(response.body) == {"status": "ok"}


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


class FakeManager:
    def __init__(self, error=None):
        self.error = error

    def create_session(self, **kwargs):
        if self.error:
            raise self.error
        return type("Session", (), {"session_id": "session_test"})()

    def snapshot(self, session_id):
        return {"session_id": session_id}


def _create_session(upload):
    return web_app.create_session(
        pdf=upload,
        subject=None,
        difficulty="normal",
        output_language="ko",
        max_concepts=7,
        questions_per_concept=3,
        model=None,
        skip_cache=False,
    )


def _create_streaming_session(upload):
    return web_app.create_session_stream(
        pdf=upload,
        subject=None,
        difficulty="normal",
        output_language="ko",
        max_concepts=7,
        questions_per_concept=3,
        model=None,
        skip_cache=False,
    )


def test_create_session_removes_uploaded_pdf_after_success(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web_app, "manager", FakeManager())
    upload = UploadFile(filename="lecture.pdf", file=BytesIO(b"%PDF-1.7\ncontent"))

    assert _create_session(upload) == {"session_id": "session_test"}
    assert list(tmp_path.iterdir()) == []


def test_create_session_removes_uploaded_pdf_after_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web_app, "manager", FakeManager(WebStudyError("analysis failed")))
    upload = UploadFile(filename="lecture.pdf", file=BytesIO(b"%PDF-1.7\ncontent"))

    with pytest.raises(HTTPException):
        _create_session(upload)

    assert list(tmp_path.iterdir()) == []


def test_streaming_session_removes_uploaded_pdf_when_worker_finishes(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web_app, "manager", FakeManager())
    upload = UploadFile(filename="lecture.pdf", file=BytesIO(b"%PDF-1.7\ncontent"))

    response = _create_streaming_session(upload)

    async def consume_response():
        return [chunk async for chunk in response.body_iterator]

    chunks = asyncio.run(consume_response())
    assert any('"step": "done"' in chunk for chunk in chunks)
    assert list(tmp_path.iterdir()) == []
