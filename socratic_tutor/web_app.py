from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .pipeline import format_pipeline_error
from .storage import ensure_dir
from .web_service import WebStudyError, WebStudyManager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
UPLOAD_DIR = PROJECT_ROOT / "uploads"

manager = WebStudyManager()
app = FastAPI(title="Socratic Lecture Tutor Web")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


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
    with target.open("wb") as file:
        shutil.copyfileobj(pdf.file, file)

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
    return manager.snapshot(session.session_id)


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
