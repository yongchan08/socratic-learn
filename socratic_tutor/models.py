from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ParsedPage(BaseModel):
    page_number: int
    markdown: str


class ParsedDocument(BaseModel):
    document_id: str
    source_path: str
    title: str | None = None
    markdown: str
    pages: list[ParsedPage]
    created_at: datetime


class Concept(BaseModel):
    concept_id: str
    title: str
    summary: str
    importance: str
    source_pages: list[int]
    evidence_from_material: list[str] = Field(default_factory=list)


class RequiredPoint(BaseModel):
    point_id: str
    text: str
    gentle_hint: str
    direct_hint: str


class Question(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question_id: str
    concept_id: str
    question_type: Literal["explanation", "comparison", "application"]
    question: str
    required_points: list[RequiredPoint]
    source_pages: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_required_point_ids(self) -> "Question":
        linked_ids = [point.point_id for point in self.required_points]
        expected_ids = [f"rp_{index:03d}" for index in range(1, len(self.required_points) + 1)]
        if linked_ids != expected_ids:
            raise ValueError("required_points point_id values must follow rp_001, rp_002, ... order")
        return self

    @property
    def required_point_texts(self) -> list[str]:
        return [point.text for point in self.required_points]


class AnswerEvaluation(BaseModel):
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    score: float
    status: Literal[
        "sufficient",
        "partially_sufficient",
        "insufficient",
        "misconception",
    ]
    feedback_to_student: str
    hint: str | None = None
    improvement_note: str | None = None
    socratic_follow_up: str | None = None
    reveal_missing_points: bool = False
    next_action: Literal[
        "next_question",
        "ask_followup",
    ]


class StudentAnswer(BaseModel):
    answer_id: str
    question_id: str
    attempt_number: int
    answer_text: str
    evaluation: AnswerEvaluation
    created_at: datetime


class ConceptAnswer(BaseModel):
    answer_id: str
    concept_id: str
    answer_text: str
    created_at: datetime


class SessionSummary(BaseModel):
    strong_concepts: list[str] = Field(default_factory=list)
    weak_concepts: list[str] = Field(default_factory=list)
    frequently_missing_points: list[str] = Field(default_factory=list)
    recommended_review_questions: list[str] = Field(default_factory=list)
    overall_feedback: str


class StudySession(BaseModel):
    session_id: str
    document_id: str
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    output_language: Literal["ko", "en"] = "ko"
    concepts: list[Concept]
    questions: list[Question]
    concept_answers: list[ConceptAnswer] = Field(default_factory=list)
    answers: list[StudentAnswer] = Field(default_factory=list)
    summary: SessionSummary | None = None
    started_at: datetime
    ended_at: datetime | None = None


class ConceptReviewReport(BaseModel):
    review_id: str
    document_id: str
    concepts_file: str
    questions_file: str
    concept_answers: list[ConceptAnswer] = Field(default_factory=list)
    evaluations: list[StudentAnswer] = Field(default_factory=list)
    summary: SessionSummary | None = None
    started_at: datetime
    ended_at: datetime | None = None
