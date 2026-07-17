from datetime import datetime, timezone

import typer

from socratic_tutor.config import AppConfig
from socratic_tutor.models import Concept, Question, RequiredPoint
from socratic_tutor.session import run_concept_review_session, run_interactive_session


def _config() -> AppConfig:
    return AppConfig(
        pdf_path=None,
        api_key="test-key",
        output_dir="outputs",
        cache_dir="cache",
    )


def _concept() -> Concept:
    return Concept(
        concept_id="concept_001",
        title="Usability",
        summary="사용하기 쉬운 정도",
        importance="UI 평가의 핵심 기준",
        source_pages=[1],
    )


def _question() -> Question:
    return Question(
        question_id="q_001_001",
        concept_id="concept_001",
        question_type="explanation",
        question="사용성이 무엇인지 설명해보세요.",
        required_points=[RequiredPoint(
            point_id="rp_001", text="사용하기 쉬운 정도", gentle_hint="생각해보게.", direct_hint="설명해보게."
        )],
    )


def _application_question() -> Question:
    return Question(
        question_id="q_001_002",
        concept_id="concept_001",
        question_type="application",
        question="사용성을 실제 UI에 적용해보세요.",
        required_points=[RequiredPoint(
            point_id="rp_001", text="실제 사용 맥락", gentle_hint="생각해보게.", direct_hint="설명해보게."
        )],
    )


class RecordingLLM:
    def __init__(self, events):
        self.events = events
        self.call_count = 0

    def complete_json(self, system_prompt, user_prompt):
        self.events.append("llm")
        required_point = ["사용하기 쉬운 정도", "실제 사용 맥락"][self.call_count]
        self.call_count += 1
        return {
            "matched_points": [required_point],
            "missing_points": [],
            "misconceptions": [],
            "score": 1,
            "status": "sufficient",
            "feedback_to_student": "핵심을 포함했네.",
            "next_action": "next_question",
        }


def test_quit_command_ends_session_without_answering_all_questions(monkeypatch):
    monkeypatch.setattr(typer, "prompt", lambda _: "/quit")

    session = run_interactive_session(
        document_id="doc_12345678",
        concepts=[_concept()],
        questions=[_question()],
        config=_config(),
        llm_client=object(),
    )

    assert session.ended_at is not None
    assert session.answers == []
    assert "subject" not in session.model_dump(mode="json")


def test_prompt_abort_ends_session_without_losing_partial_progress(monkeypatch):
    def raise_abort(_: str) -> str:
        raise typer.Abort()

    monkeypatch.setattr(typer, "prompt", raise_abort)

    session = run_interactive_session(
        document_id="doc_12345678",
        concepts=[_concept()],
        questions=[_question()],
        config=_config(),
        llm_client=object(),
    )

    assert isinstance(session.ended_at, datetime)
    assert session.ended_at.tzinfo == timezone.utc


def test_collects_one_answer_per_concept_before_evaluating_both_questions(monkeypatch, capsys):
    events = []

    def answer_prompt(_):
        events.append("answer")
        return "사용하기 쉬워야 하고 실제 사용 맥락도 고려해야 합니다."

    monkeypatch.setattr(typer, "prompt", answer_prompt)
    session = run_concept_review_session(
        document_id="doc_12345678",
        concepts=[_concept()],
        questions=[_question(), _application_question()],
        config=_config(),
        llm_client=RecordingLLM(events),
    )

    assert events == ["answer", "llm", "llm"]
    assert len(session.concept_answers) == 1
    assert len(session.answers) == 2
    assert {answer.question_id for answer in session.answers} == {"q_001_001", "q_001_002"}
    assert all(not answer.evaluation.missing_points for answer in session.answers)
    review_prompt = capsys.readouterr().out
    assert "Usability" in review_prompt
    assert "사용하기 쉬운 정도" not in review_prompt
