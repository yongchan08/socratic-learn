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
    prerequisites: list[str] = Field(default_factory=list)
    common_misconceptions: list[str] = Field(default_factory=list)
    evidence_from_material: list[str] = Field(default_factory=list)


class PointHint(BaseModel):
    point_id: str
    required_point: str
    gentle: str
    direct: str


class Question(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question_id: str
    concept_id: str
    question_type: Literal["explanation", "comparison", "application"]
    question: str
    required_points: list[str]
    point_hints: list[PointHint] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_point_hints(self) -> "Question":
        if not self.point_hints and len(self.hints) == len(self.required_points):
            self.point_hints = [
                PointHint(
                    point_id=f"rp_{index:03d}",
                    required_point=point,
                    gentle=hint,
                    direct=hint,
                )
                for index, (point, hint) in enumerate(zip(self.required_points, self.hints), start=1)
            ]
        if not self.point_hints:
            return self

        linked_points = [hint.required_point for hint in self.point_hints]
        linked_ids = [hint.point_id for hint in self.point_hints]
        if linked_points != self.required_points:
            raise ValueError("point_hints must cover required_points once and in the same order")
        expected_ids = [f"rp_{index:03d}" for index in range(1, len(self.required_points) + 1)]
        if linked_ids != expected_ids:
            raise ValueError("point_hints point_id values must follow rp_001, rp_002, ... order")
        return self


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
        "show_summary",
    ]


class StudentAnswer(BaseModel):
    answer_id: str
    question_id: str
    attempt_number: int
    answer_text: str
    evaluation: AnswerEvaluation
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
    subject: str | None = None
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    output_language: Literal["ko", "en"] = "ko"
    concepts: list[Concept]
    questions: list[Question]
    answers: list[StudentAnswer] = Field(default_factory=list)
    summary: SessionSummary | None = None
    started_at: datetime
    ended_at: datetime | None = None
