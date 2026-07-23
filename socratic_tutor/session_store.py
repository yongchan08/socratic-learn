from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone

from dotenv import load_dotenv

from .models import (
    Concept,
    ParsedDocument,
    ParsedPage,
    Question,
    RequiredPoint,
    StudySession,
    StudentAnswer,
    ConceptAnswer,
    AnswerEvaluation,
    SessionSummary,
)
from .db_models import (
    Base,
    DocumentDB,
    DocumentPageDB,
    ConceptDB,
    QuestionDB,
    RequiredPointDB,
    StudySessionDB,
    StudentAnswerDB,
    ConceptAnswerDB,
    AnswerEvaluationDB,
    CourseDB,
)


@dataclass
class StoredWebSession:
    session: StudySession
    current_index: int
    session_mode: str
    document_title: str | None
    config: dict[str, Any]


class PostgresSessionStore:
    def __init__(self, database_url: str) -> None:
        # DB URL 변환: postgresql:// -> postgresql+psycopg://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://")
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://")
            
        self.database_url = database_url
        
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        self.engine = create_engine(self.database_url, pool_size=5, max_overflow=10)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False)
        self._ensure_schema()

    @classmethod
    def from_environment(cls) -> "PostgresSessionStore | None":
        load_dotenv()
        database_url = os.getenv("DATABASE_URL", "").strip()
        return cls(database_url) if database_url else None

    def _ensure_schema(self) -> None:
        Base.metadata.create_all(bind=self.engine)

    def save(self, stored: StoredWebSession) -> None:
        with self.SessionLocal() as session:
            db_session = session.query(StudySessionDB).filter_by(session_id=stored.session.session_id).first()
            if not db_session:
                db_session = StudySessionDB(
                    session_id=stored.session.session_id,
                    document_id=stored.session.document_id,
                )
                session.add(db_session)
            
            db_session.session_mode = stored.session_mode
            db_session.difficulty = stored.session.difficulty
            db_session.output_language = stored.session.output_language
            db_session.started_at = stored.session.started_at
            db_session.ended_at = stored.session.ended_at
            db_session.completion_status = stored.session.completion_status
            db_session.end_reason = stored.session.end_reason
            db_session.document_title = stored.document_title
            db_session.config_data = stored.config
            
            # config_data에 current_index 임시 저장
            if db_session.config_data is None:
                db_session.config_data = {}
            db_session.config_data["current_index"] = stored.current_index
            
            db_session.summary_data = stored.session.summary.model_dump(mode="json") if stored.session.summary else None

            # 기존 답변 및 평가 지우고 다시 저장 (간단한 동기화)
            session.query(ConceptAnswerDB).filter_by(session_id=db_session.session_id).delete()
            session.query(StudentAnswerDB).filter_by(session_id=db_session.session_id).delete()
            
            for ca in stored.session.concept_answers:
                db_ca = ConceptAnswerDB(
                    answer_id=ca.answer_id,
                    session_id=db_session.session_id,
                    concept_id=ca.concept_id,
                    answer_text=ca.answer_text,
                    created_at=ca.created_at,
                )
                session.add(db_ca)
            
            for sa in stored.session.answers:
                db_sa = StudentAnswerDB(
                    answer_id=sa.answer_id,
                    session_id=db_session.session_id,
                    question_id=sa.question_id,
                    attempt_number=sa.attempt_number,
                    answer_text=sa.answer_text,
                    score=sa.evaluation.score,
                    status=sa.evaluation.status,
                    feedback_to_student=sa.evaluation.feedback_to_student,
                    hint=sa.evaluation.hint,
                    improvement_note=sa.evaluation.improvement_note,
                    socratic_follow_up=sa.evaluation.socratic_follow_up,
                    reveal_missing_points=sa.evaluation.reveal_missing_points,
                    next_action=sa.evaluation.next_action,
                    created_at=sa.created_at,
                )
                session.add(db_sa)
                
                db_eval = AnswerEvaluationDB(
                    answer_id=sa.answer_id,
                    matched_point_ids=sa.evaluation.matched_point_ids,
                    matched_points=sa.evaluation.matched_points,
                    missing_points=sa.evaluation.missing_points,
                    misconceptions=sa.evaluation.misconceptions,
                )
                session.add(db_eval)

            session.commit()

    def load(self, session_id: str) -> StoredWebSession | None:
        from sqlalchemy.orm import joinedload
        with self.SessionLocal() as session:
            db_session = (
                session.query(StudySessionDB)
                .options(
                    joinedload(StudySessionDB.concept_answers),
                    joinedload(StudySessionDB.student_answers).joinedload(StudentAnswerDB.evaluation_details),
                )
                .filter_by(session_id=session_id)
                .first()
            )
            if not db_session:
                return None
            
            # Fetch concept and question data dynamically based on the original document
            db_concepts = session.query(ConceptDB).filter_by(
                document_id=db_session.document_id,
                difficulty=db_session.difficulty,
                output_language=db_session.output_language
            ).all()
            
            concepts = [
                Concept(
                    concept_id=c.concept_id,
                    title=c.title,
                    summary=c.summary,
                    importance=c.importance,
                    source_pages=c.source_pages,
                    evidence_from_material=c.evidence_from_material,
                ) for c in db_concepts
            ]
            
            db_questions = session.query(QuestionDB).filter(
                QuestionDB.concept_id.in_([c.concept_id for c in concepts])
            ).options(joinedload(QuestionDB.required_points)).all()
            
            questions = [
                Question(
                    question_id=q.question_id,
                    concept_id=q.concept_id,
                    question_type=q.question_type, # type: ignore
                    question=q.question_text,
                    source_pages=q.source_pages,
                    required_points=[
                        RequiredPoint(
                            point_id=rp.point_id,
                            text=rp.text,
                            gentle_hint=rp.gentle_hint,
                            direct_hint=rp.direct_hint,
                        ) for rp in q.required_points
                    ]
                ) for q in db_questions
            ]

            concept_answers = [
                ConceptAnswer(
                    answer_id=ca.answer_id,
                    concept_id=ca.concept_id,
                    answer_text=ca.answer_text,
                    created_at=ca.created_at,
                ) for ca in db_session.concept_answers
            ]
            
            answers = [
                StudentAnswer(
                    answer_id=sa.answer_id,
                    question_id=sa.question_id,
                    attempt_number=sa.attempt_number,
                    answer_text=sa.answer_text,
                    created_at=sa.created_at,
                    evaluation=AnswerEvaluation(
                        matched_point_ids=sa.evaluation_details.matched_point_ids if sa.evaluation_details else [],
                        matched_points=sa.evaluation_details.matched_points if sa.evaluation_details else [],
                        missing_points=sa.evaluation_details.missing_points if sa.evaluation_details else [],
                        misconceptions=sa.evaluation_details.misconceptions if sa.evaluation_details else [],
                        score=sa.score,
                        status=sa.status, # type: ignore
                        feedback_to_student=sa.feedback_to_student,
                        hint=sa.hint,
                        improvement_note=sa.improvement_note,
                        socratic_follow_up=sa.socratic_follow_up,
                        reveal_missing_points=sa.reveal_missing_points,
                        next_action=sa.next_action, # type: ignore
                    )
                ) for sa in db_session.student_answers
            ]
            
            summary = SessionSummary.model_validate(db_session.summary_data) if db_session.summary_data else None
            
            study_session = StudySession(
                session_id=db_session.session_id,
                document_id=db_session.document_id,
                difficulty=db_session.difficulty, # type: ignore
                output_language=db_session.output_language, # type: ignore
                concepts=concepts,
                questions=questions,
                concept_answers=concept_answers,
                answers=answers,
                summary=summary,
                started_at=db_session.started_at,
                ended_at=db_session.ended_at,
                completion_status=db_session.completion_status, # type: ignore
                end_reason=db_session.end_reason, # type: ignore
            )
            
            return StoredWebSession(
                session=study_session,
                current_index=db_session.config_data.get("current_index", 0) if db_session.config_data else 0,
                session_mode=db_session.session_mode,
                document_title=db_session.document_title,
                config=db_session.config_data or {},
            )

    def save_course(self, course: dict[str, Any]) -> None:
        with self.SessionLocal() as session:
            db_course = session.query(CourseDB).filter_by(course_id=course["course_id"]).first()
            if not db_course:
                db_course = CourseDB(course_id=course["course_id"])
                session.add(db_course)
            db_course.course_data = course
            session.commit()

    def load_course(self, course_id: str) -> dict[str, Any] | None:
        with self.SessionLocal() as session:
            db_course = session.query(CourseDB).filter_by(course_id=course_id).first()
            return db_course.course_data if db_course else None

    def list_courses(self) -> list[dict[str, Any]]:
        with self.SessionLocal() as session:
            db_courses = session.query(CourseDB).order_by(CourseDB.updated_at.desc()).all()
            courses = []
            for db_c in db_courses:
                course = dict(db_c.course_data)
                course["updated_at"] = db_c.updated_at.isoformat()
                courses.append(course)
            return courses

    def delete_course(self, course_id: str) -> list[str] | None:
        with self.SessionLocal() as session:
            db_course = session.query(CourseDB).filter_by(course_id=course_id).first()
            if not db_course:
                return None
            
            course = db_course.course_data
            session_ids = [stage["session_id"] for stage in course.get("stages", []) if stage.get("session_id")]
            if course.get("final_review_session_id"):
                session_ids.append(course["final_review_session_id"])
                
            if session_ids:
                session.query(StudySessionDB).filter(StudySessionDB.session_id.in_(session_ids)).delete(synchronize_session=False)
            
            session.delete(db_course)
            session.commit()
            return session_ids

    def save_document(self, file_hash: str, document: ParsedDocument) -> None:
        with self.SessionLocal() as session:
            db_doc = session.query(DocumentDB).filter_by(file_hash=file_hash).first()
            if not db_doc:
                db_doc = DocumentDB(file_hash=file_hash, document_id=document.document_id)
                session.add(db_doc)
            
            db_doc.title = document.title
            db_doc.source_path = document.source_path
            db_doc.markdown_content = document.markdown
            db_doc.created_at = document.created_at
            
            # Update pages
            session.query(DocumentPageDB).filter_by(document_id=db_doc.document_id).delete()
            for p in document.pages:
                session.add(DocumentPageDB(
                    document_id=db_doc.document_id,
                    page_number=p.page_number,
                    markdown=p.markdown,
                ))
            session.commit()

    def load_document(self, file_hash: str) -> ParsedDocument | None:
        from sqlalchemy.orm import joinedload
        with self.SessionLocal() as session:
            db_doc = session.query(DocumentDB).options(joinedload(DocumentDB.pages)).filter_by(file_hash=file_hash).first()
            if not db_doc:
                return None
            
            return ParsedDocument(
                document_id=db_doc.document_id,
                source_path=db_doc.source_path,
                title=db_doc.title,
                markdown=db_doc.markdown_content,
                pages=[ParsedPage(page_number=p.page_number, markdown=p.markdown) for p in db_doc.pages],
                created_at=db_doc.created_at,
            )

    def save_concepts(
        self, file_hash: str, difficulty: str, output_language: str, concepts: list[Concept]
    ) -> None:
        with self.SessionLocal() as session:
            db_doc = session.query(DocumentDB).filter_by(file_hash=file_hash).first()
            if not db_doc:
                raise ValueError("문서가 존재하지 않습니다.")
            
            session.query(ConceptDB).filter_by(
                document_id=db_doc.document_id, 
                difficulty=difficulty, 
                output_language=output_language
            ).delete()
            
            for c in concepts:
                db_concept = ConceptDB(
                    concept_id=c.concept_id,
                    document_id=db_doc.document_id,
                    difficulty=difficulty,
                    output_language=output_language,
                    title=c.title,
                    summary=c.summary,
                    importance=c.importance,
                    source_pages=c.source_pages,
                    evidence_from_material=c.evidence_from_material,
                )
                session.add(db_concept)
            session.commit()

    def load_concepts(self, file_hash: str, difficulty: str, output_language: str) -> list[Concept] | None:
        with self.SessionLocal() as session:
            db_doc = session.query(DocumentDB).filter_by(file_hash=file_hash).first()
            if not db_doc:
                return None
                
            db_concepts = session.query(ConceptDB).filter_by(
                document_id=db_doc.document_id,
                difficulty=difficulty,
                output_language=output_language
            ).all()
            
            if not db_concepts:
                return None
                
            return [
                Concept(
                    concept_id=c.concept_id,
                    title=c.title,
                    summary=c.summary,
                    importance=c.importance,
                    source_pages=c.source_pages,
                    evidence_from_material=c.evidence_from_material,
                ) for c in db_concepts
            ]

    def save_questions(
        self, file_hash: str, difficulty: str, output_language: str, questions: list[Question]
    ) -> None:
        with self.SessionLocal() as session:
            db_doc = session.query(DocumentDB).filter_by(file_hash=file_hash).first()
            if not db_doc:
                raise ValueError("문서가 존재하지 않습니다.")
                
            concept_ids = [q.concept_id for q in questions]
            
            # 기존 질문 삭제 (Cascade를 통해 RequiredPoints도 삭제됨)
            session.query(QuestionDB).filter(QuestionDB.concept_id.in_(concept_ids)).delete(synchronize_session=False)
            
            for q in questions:
                db_question = QuestionDB(
                    question_id=q.question_id,
                    concept_id=q.concept_id,
                    question_type=q.question_type,
                    question_text=q.question,
                    source_pages=q.source_pages,
                )
                session.add(db_question)
                
                for rp in q.required_points:
                    db_rp = RequiredPointDB(
                        point_id=rp.point_id,
                        question_id=q.question_id,
                        text=rp.text,
                        gentle_hint=rp.gentle_hint,
                        direct_hint=rp.direct_hint,
                    )
                    session.add(db_rp)
                    
            session.commit()

    def load_questions(self, file_hash: str, difficulty: str, output_language: str) -> list[Question] | None:
        from sqlalchemy.orm import joinedload
        with self.SessionLocal() as session:
            db_doc = session.query(DocumentDB).filter_by(file_hash=file_hash).first()
            if not db_doc:
                return None
                
            db_concepts = session.query(ConceptDB).filter_by(
                document_id=db_doc.document_id,
                difficulty=difficulty,
                output_language=output_language
            ).all()
            concept_ids = [c.concept_id for c in db_concepts]
            
            if not concept_ids:
                return None
                
            db_questions = session.query(QuestionDB).filter(QuestionDB.concept_id.in_(concept_ids)).options(joinedload(QuestionDB.required_points)).all()
            
            if not db_questions:
                return None
                
            return [
                Question(
                    question_id=q.question_id,
                    concept_id=q.concept_id,
                    question_type=q.question_type, # type: ignore
                    question=q.question_text,
                    source_pages=q.source_pages,
                    required_points=[
                        RequiredPoint(
                            point_id=rp.point_id,
                            text=rp.text,
                            gentle_hint=rp.gentle_hint,
                            direct_hint=rp.direct_hint,
                        ) for rp in q.required_points
                    ]
                ) for q in db_questions
            ]
