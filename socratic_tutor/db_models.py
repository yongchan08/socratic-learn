from typing import Any
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    ARRAY,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    pass

class DocumentDB(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    file_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    pages: Mapped[list["DocumentPageDB"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    concepts: Mapped[list["ConceptDB"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySessionDB"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentPageDB(Base):
    __tablename__ = "document_pages"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id", ondelete="CASCADE"), primary_key=True
    )
    page_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped["DocumentDB"] = relationship(back_populates="pages")


class ConceptDB(Base):
    __tablename__ = "concepts"

    concept_id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False
    )
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    output_language: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[str] = mapped_column(Text, nullable=False)
    source_pages: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    evidence_from_material: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    document: Mapped["DocumentDB"] = relationship(back_populates="concepts")
    questions: Mapped[list["QuestionDB"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    concept_answers: Mapped[list["ConceptAnswerDB"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )


class QuestionDB(Base):
    __tablename__ = "questions"

    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    concept_id: Mapped[str] = mapped_column(
        ForeignKey("concepts.concept_id", ondelete="CASCADE"), nullable=False
    )
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_pages: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)

    concept: Mapped["ConceptDB"] = relationship(back_populates="questions")
    required_points: Mapped[list["RequiredPointDB"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="RequiredPointDB.point_id"
    )
    student_answers: Mapped[list["StudentAnswerDB"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class RequiredPointDB(Base):
    __tablename__ = "required_points"

    point_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.question_id", ondelete="CASCADE"), primary_key=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    gentle_hint: Mapped[str] = mapped_column(Text, nullable=False)
    direct_hint: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped["QuestionDB"] = relationship(back_populates="required_points")


class StudySessionDB(Base):
    __tablename__ = "study_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False
    )
    session_mode: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, default="normal")
    output_language: Mapped[str] = mapped_column(String, default="ko")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_status: Mapped[str | None] = mapped_column(String)
    end_reason: Mapped[str | None] = mapped_column(String)
    document_title: Mapped[str | None] = mapped_column(String)
    config_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    summary_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    document: Mapped["DocumentDB"] = relationship(back_populates="study_sessions")
    concept_answers: Mapped[list["ConceptAnswerDB"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ConceptAnswerDB.created_at"
    )
    student_answers: Mapped[list["StudentAnswerDB"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="StudentAnswerDB.created_at"
    )


class ConceptAnswerDB(Base):
    __tablename__ = "concept_answers"

    answer_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("study_sessions.session_id", ondelete="CASCADE"), nullable=False
    )
    concept_id: Mapped[str] = mapped_column(
        ForeignKey("concepts.concept_id", ondelete="CASCADE"), nullable=False
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["StudySessionDB"] = relationship(back_populates="concept_answers")
    concept: Mapped["ConceptDB"] = relationship(back_populates="concept_answers")


class StudentAnswerDB(Base):
    __tablename__ = "student_answers"

    answer_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("study_sessions.session_id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.question_id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    feedback_to_student: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text)
    improvement_note: Mapped[str | None] = mapped_column(Text)
    socratic_follow_up: Mapped[str | None] = mapped_column(Text)
    reveal_missing_points: Mapped[bool] = mapped_column(Boolean, default=False)
    next_action: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["StudySessionDB"] = relationship(back_populates="student_answers")
    question: Mapped["QuestionDB"] = relationship(back_populates="student_answers")
    evaluation_details: Mapped["AnswerEvaluationDB"] = relationship(
        back_populates="answer", cascade="all, delete-orphan", uselist=False
    )


class AnswerEvaluationDB(Base):
    __tablename__ = "answer_evaluations"

    evaluation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    answer_id: Mapped[str] = mapped_column(
        ForeignKey("student_answers.answer_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    matched_point_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    matched_points: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    missing_points: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    misconceptions: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    answer: Mapped["StudentAnswerDB"] = relationship(back_populates="evaluation_details")


class CourseDB(Base):
    __tablename__ = "learning_courses"

    course_id: Mapped[str] = mapped_column(String, primary_key=True)
    course_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
