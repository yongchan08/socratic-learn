from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

from .models import Concept, ParsedDocument, Question, StudySession


@dataclass
class StoredWebSession:
    session: StudySession
    current_index: int
    session_mode: str
    document_title: str | None
    config: dict[str, Any]


class MemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, StoredWebSession] = {}
        self._documents: dict[str, ParsedDocument] = {}
        self._materials: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._courses: dict[str, dict[str, Any]] = {}

    def save(self, stored: StoredWebSession) -> None:
        self._sessions[stored.session.session_id] = stored

    def load(self, session_id: str) -> StoredWebSession | None:
        return self._sessions.get(session_id)

    def save_course(self, course: dict[str, Any]) -> None:
        self._courses[course["course_id"]] = course

    def load_course(self, course_id: str) -> dict[str, Any] | None:
        return self._courses.get(course_id)

    def list_courses(self) -> list[dict[str, Any]]:
        return list(sorted(self._courses.values(), key=lambda item: item.get("updated_at", item.get("created_at", "")), reverse=True))

    def delete_course(self, course_id: str) -> list[str] | None:
        course = self._courses.pop(course_id, None)
        if course is None:
            return None
        session_ids = [stage["session_id"] for stage in course.get("stages", []) if stage.get("session_id")]
        if course.get("final_review_session_id"):
            session_ids.append(course["final_review_session_id"])
        for session_id in session_ids:
            self._sessions.pop(session_id, None)
        return session_ids

    def save_document(self, file_hash: str, document: ParsedDocument) -> None:
        self._documents[file_hash] = document

    def load_document(self, file_hash: str) -> ParsedDocument | None:
        return self._documents.get(file_hash)

    def save_concepts(self, file_hash: str, difficulty: str, output_language: str, concepts: list[Concept]) -> None:
        self._save_material_field(file_hash, difficulty, output_language, "concepts_data", concepts)

    def load_concepts(self, file_hash: str, difficulty: str, output_language: str) -> list[Concept] | None:
        payload = self._load_material_field(file_hash, difficulty, output_language, "concepts_data")
        return [Concept.model_validate(item) for item in payload] if payload is not None else None

    def save_questions(self, file_hash: str, difficulty: str, output_language: str, questions: list[Question]) -> None:
        self._save_material_field(file_hash, difficulty, output_language, "questions_data", questions)

    def load_questions(self, file_hash: str, difficulty: str, output_language: str) -> list[Question] | None:
        payload = self._load_material_field(file_hash, difficulty, output_language, "questions_data")
        return [Question.model_validate(item) for item in payload] if payload is not None else None

    def _save_material_field(
        self, file_hash: str, difficulty: str, output_language: str, field: str, values: list[Any]
    ) -> None:
        if field not in {"concepts_data", "questions_data"}:
            raise ValueError("지원하지 않는 학습 자료 필드입니다.")
        key = (file_hash, difficulty, output_language)
        payload = [value.model_dump(mode="json") if hasattr(value, "model_dump") else value for value in values]
        data = self._materials.get(key, {})
        data[field] = payload
        self._materials[key] = data

    def _load_material_field(
        self, file_hash: str, difficulty: str, output_language: str, field: str
    ) -> list[dict[str, Any]] | None:
        if field not in {"concepts_data", "questions_data"}:
            raise ValueError("지원하지 않는 학습 자료 필드입니다.")
        payload = self._materials.get((file_hash, difficulty, output_language), {}).get(field)
        return payload if payload is not None else None


class PostgresSessionStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_schema()

    @classmethod
    def from_environment(cls) -> "PostgresSessionStore | None":
        load_dotenv()
        database_url = os.getenv("DATABASE_URL", "").strip()
        if database_url.lower() in {"memory://", "memory", "mock://", "mock"}:
            return MemorySessionStore()
        return cls(database_url) if database_url else None

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "DATABASE_URL을 사용하려면 psycopg를 설치해야 합니다. pip install -e '.[dev]'를 실행해주세요."
            ) from exc
        return psycopg.connect(self.database_url)

    def _ensure_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS web_study_sessions (
                    session_id TEXT PRIMARY KEY,
                    session_data JSONB NOT NULL,
                    current_index INTEGER NOT NULL,
                    session_mode TEXT NOT NULL,
                    document_title TEXT,
                    config_data JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_documents (
                    file_hash TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    parsed_data JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_materials (
                    file_hash TEXT NOT NULL REFERENCES learning_documents(file_hash) ON DELETE CASCADE,
                    difficulty TEXT NOT NULL,
                    output_language TEXT NOT NULL,
                    concepts_data JSONB,
                    questions_data JSONB,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (file_hash, difficulty, output_language)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_courses (
                    course_id TEXT PRIMARY KEY,
                    course_data JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

    def save(self, stored: StoredWebSession) -> None:
        session_data = stored.session.model_dump(mode="json")
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO web_study_sessions (
                    session_id, session_data, current_index, session_mode, document_title, config_data, updated_at
                ) VALUES (%s, %s::jsonb, %s, %s, %s, %s::jsonb, NOW())
                ON CONFLICT (session_id) DO UPDATE SET
                    session_data = EXCLUDED.session_data,
                    current_index = EXCLUDED.current_index,
                    session_mode = EXCLUDED.session_mode,
                    document_title = EXCLUDED.document_title,
                    config_data = EXCLUDED.config_data,
                    updated_at = NOW()
                """,
                (
                    stored.session.session_id,
                    json.dumps(session_data, ensure_ascii=False),
                    stored.current_index,
                    stored.session_mode,
                    stored.document_title,
                    json.dumps(stored.config, ensure_ascii=False),
                ),
            )

    def load(self, session_id: str) -> StoredWebSession | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT session_data, current_index, session_mode, document_title, config_data
                FROM web_study_sessions
                WHERE session_id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return StoredWebSession(
            session=StudySession.model_validate(row[0]),
            current_index=row[1],
            session_mode=row[2],
            document_title=row[3],
            config=row[4],
        )

    def save_course(self, course: dict[str, Any]) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO learning_courses (course_id, course_data, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (course_id) DO UPDATE SET
                    course_data = EXCLUDED.course_data,
                    updated_at = NOW()
                """,
                (course["course_id"], json.dumps(course, ensure_ascii=False)),
            )

    def load_course(self, course_id: str) -> dict[str, Any] | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT course_data FROM learning_courses WHERE course_id = %s", (course_id,))
            row = cursor.fetchone()
        return row[0] if row else None

    def list_courses(self) -> list[dict[str, Any]]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT course_data, updated_at FROM learning_courses ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
        courses = []
        for course_data, updated_at in rows:
            course = dict(course_data)
            course["updated_at"] = updated_at.isoformat()
            courses.append(course)
        return courses

    def delete_course(self, course_id: str) -> list[str] | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT course_data FROM learning_courses WHERE course_id = %s FOR UPDATE", (course_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            course = row[0]
            session_ids = [stage["session_id"] for stage in course.get("stages", []) if stage.get("session_id")]
            if course.get("final_review_session_id"):
                session_ids.append(course["final_review_session_id"])
            if session_ids:
                cursor.execute("DELETE FROM web_study_sessions WHERE session_id = ANY(%s)", (session_ids,))
            cursor.execute("DELETE FROM learning_courses WHERE course_id = %s", (course_id,))
        return session_ids

    def save_document(self, file_hash: str, document: ParsedDocument) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO learning_documents (file_hash, document_id, parsed_data, updated_at)
                VALUES (%s, %s, %s::jsonb, NOW())
                ON CONFLICT (file_hash) DO UPDATE SET
                    document_id = EXCLUDED.document_id,
                    parsed_data = EXCLUDED.parsed_data,
                    updated_at = NOW()
                """,
                (
                    file_hash,
                    document.document_id,
                    json.dumps(document.model_dump(mode="json"), ensure_ascii=False),
                ),
            )

    def load_document(self, file_hash: str) -> ParsedDocument | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT parsed_data FROM learning_documents WHERE file_hash = %s", (file_hash,))
            row = cursor.fetchone()
        return ParsedDocument.model_validate(row[0]) if row else None

    def save_concepts(
        self, file_hash: str, difficulty: str, output_language: str, concepts: list[Concept]
    ) -> None:
        self._save_material_field(file_hash, difficulty, output_language, "concepts_data", concepts)

    def load_concepts(self, file_hash: str, difficulty: str, output_language: str) -> list[Concept] | None:
        payload = self._load_material_field(file_hash, difficulty, output_language, "concepts_data")
        return [Concept.model_validate(item) for item in payload] if payload is not None else None

    def save_questions(
        self, file_hash: str, difficulty: str, output_language: str, questions: list[Question]
    ) -> None:
        self._save_material_field(file_hash, difficulty, output_language, "questions_data", questions)

    def load_questions(self, file_hash: str, difficulty: str, output_language: str) -> list[Question] | None:
        payload = self._load_material_field(file_hash, difficulty, output_language, "questions_data")
        return [Question.model_validate(item) for item in payload] if payload is not None else None

    def _save_material_field(
        self, file_hash: str, difficulty: str, output_language: str, field: str, values: list[Any]
    ) -> None:
        if field not in {"concepts_data", "questions_data"}:
            raise ValueError("지원하지 않는 학습 자료 필드입니다.")
        payload = [value.model_dump(mode="json") if hasattr(value, "model_dump") else value for value in values]
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO learning_materials (file_hash, difficulty, output_language, {field}, updated_at)
                VALUES (%s, %s, %s, %s::jsonb, NOW())
                ON CONFLICT (file_hash, difficulty, output_language) DO UPDATE SET
                    {field} = EXCLUDED.{field},
                    updated_at = NOW()
                """,
                (file_hash, difficulty, output_language, json.dumps(payload, ensure_ascii=False)),
            )

    def _load_material_field(
        self, file_hash: str, difficulty: str, output_language: str, field: str
    ) -> list[dict[str, Any]] | None:
        if field not in {"concepts_data", "questions_data"}:
            raise ValueError("지원하지 않는 학습 자료 필드입니다.")
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT {field} FROM learning_materials
                    WHERE file_hash = %s AND difficulty = %s AND output_language = %s""",
                (file_hash, difficulty, output_language),
            )
            row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
