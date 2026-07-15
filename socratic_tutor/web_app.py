from __future__ import annotations

import json
import os
import queue
import threading
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .pipeline import format_pipeline_error
from .pdf_parser import PDF_SIGNATURE
from .storage import ensure_dir
from .web_service import WebStudyError, WebStudyManager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
SSE_HEARTBEAT_SECONDS = 15

manager = WebStudyManager()
app = FastAPI(title="Socratic Lecture Tutor Web")

_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_frontend_url = os.getenv("FRONTEND_URL", "").strip()
if _frontend_url:
    _origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse(
        content={"status": "ok"},
        headers={"Cache-Control": "no-store"},
    )


def save_validated_pdf_upload(pdf: UploadFile, target: Path) -> None:
    total_bytes = 0
    signature = b""
    try:
        with target.open("wb") as file:
            while chunk := pdf.file.read(UPLOAD_CHUNK_BYTES):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="PDF 파일은 최대 25MB까지 업로드할 수 있습니다.")
                if len(signature) < len(PDF_SIGNATURE):
                    signature += chunk[: len(PDF_SIGNATURE) - len(signature)]
                file.write(chunk)
        if signature != PDF_SIGNATURE:
            raise HTTPException(status_code=400, detail="유효한 PDF 파일이 아닙니다.")
    except Exception:
        target.unlink(missing_ok=True)
        raise


def stream_queue_events(event_queue: queue.Queue, heartbeat_seconds: float = SSE_HEARTBEAT_SECONDS):
    while True:
        try:
            item = event_queue.get(timeout=heartbeat_seconds)
        except queue.Empty:
            yield ": heartbeat\n\n"
            continue
        if item is None:
            break
        yield item


@app.post("/api/sessions")
def create_session(
    pdf: UploadFile = File(),
    subject: str | None = Form(None),
    difficulty: str = Form("normal"),
    output_language: str = Form("ko"),
    max_concepts: int = Form(7),
    questions_per_concept: int = Form(3),
    model: str | None = Form(None),
    skip_cache: bool = Form(False),
) -> dict:
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")
    ensure_dir(UPLOAD_DIR)
    target = UPLOAD_DIR / f"{Path(pdf.filename).stem}_{uuid.uuid4().hex[:8]}{Path(pdf.filename).suffix}"
    save_validated_pdf_upload(pdf, target)

    try:
        session = manager.create_session(
            pdf_path=target,
            subject=subject,
            difficulty=difficulty,
            output_language=output_language,
            max_concepts=max_concepts,
            questions_per_concept=questions_per_concept,
            model=model,
            skip_cache=skip_cache,
        )
    except WebStudyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=format_pipeline_error(exc)) from exc
    finally:
        target.unlink(missing_ok=True)
    return manager.snapshot(session.session_id)


@app.post("/api/sessions/stream")
def create_session_stream(
    pdf: UploadFile = File(),
    subject: str | None = Form(None),
    difficulty: str = Form("normal"),
    output_language: str = Form("ko"),
    max_concepts: int = Form(7),
    questions_per_concept: int = Form(3),
    model: str | None = Form(None),
    skip_cache: bool = Form(False),
) -> StreamingResponse:
    """세션 생성 진행 상황을 SSE(Server-Sent Events)로 실시간 스트리밍합니다.

    클라이언트는 다음 형태의 이벤트를 수신합니다:
      data: {"step": "parsing", "message": "..."}\n\n
      data: {"step": "concepts", "message": "..."}\n\n
      data: {"step": "questions", "message": "...", "done": 2, "total": 7}\n\n
      data: {"step": "done", "payload": {...세션 전체 데이터...}}\n\n
      data: {"step": "error", "message": "..."}\n\n
    """
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    ensure_dir(UPLOAD_DIR)
    target = UPLOAD_DIR / f"{Path(pdf.filename).stem}_{uuid.uuid4().hex[:8]}{Path(pdf.filename).suffix}"
    save_validated_pdf_upload(pdf, target)

    # 이벤트 큐: 백그라운드 스레드 → SSE 제너레이터
    event_queue: queue.Queue = queue.Queue()

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _worker() -> None:
        try:
            event_queue.put(_sse({"step": "parsing", "message": "📜 두루마리를 해독하는 중..."}))

            def on_questions_progress(done: int, total: int) -> None:
                event_queue.put(_sse({
                    "step": "questions",
                    "message": f"✍️ 학문의 관문 조성 중... ({done}/{total})",
                    "done": done,
                    "total": total,
                }))

            session = manager.create_session(
                pdf_path=target,
                subject=subject,
                difficulty=difficulty,
                output_language=output_language,
                max_concepts=max_concepts,
                questions_per_concept=questions_per_concept,
                model=model,
                skip_cache=skip_cache,
                on_progress={
                    "after_parse": lambda: event_queue.put(
                        _sse({"step": "concepts", "message": "🔍 핵심 개념 발굴 중..."})
                    ),
                    "after_concepts": lambda: event_queue.put(
                        _sse({"step": "questions_start", "message": "✍️ 학문의 관문 조성 시작..."})
                    ),
                    "on_questions_progress": on_questions_progress,
                },
            )
            snapshot = manager.snapshot(session.session_id)
            event_queue.put(_sse({"step": "done", "payload": snapshot}))
        except WebStudyError as exc:
            event_queue.put(_sse({"step": "error", "message": str(exc)}))
        except Exception as exc:
            event_queue.put(_sse({"step": "error", "message": format_pipeline_error(exc)}))
        finally:
            target.unlink(missing_ok=True)
            event_queue.put(None)  # 종료 신호

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    return StreamingResponse(
        stream_queue_events(event_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        },
    )


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    try:
        return manager.snapshot(session_id)
    except WebStudyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/answers")
def answer(session_id: str, request: AnswerRequest) -> dict:
    try:
        manager.answer(session_id, request.answer)
        return manager.snapshot(session_id)
    except WebStudyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=format_pipeline_error(exc)) from exc


@app.post("/api/sessions/{session_id}/skip")
def skip(session_id: str) -> dict:
    try:
        manager.skip(session_id)
        return manager.snapshot(session_id)
    except WebStudyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/finish")
def finish(session_id: str) -> dict:
    try:
        manager.finish(session_id)
        return manager.snapshot(session_id)
    except WebStudyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=format_pipeline_error(exc)) from exc


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{path:path}")
def serve_frontend(path: str) -> FileResponse:
    requested = FRONTEND_DIST / path
    if path and requested.exists() and requested.is_file():
        return FileResponse(requested)
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found. Run npm install and npm run build in frontend/.")
    return FileResponse(index)


def run() -> None:
    uvicorn.run("socratic_tutor.web_app:app", host="127.0.0.1", port=8000)
