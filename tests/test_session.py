from datetime import datetime, timezone

import typer

from socratic_tutor.config import AppConfig
from socratic_tutor.models import Concept, Question
from socratic_tutor.session import MAX_ATTEMPTS_PER_QUESTION, run_interactive_session


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
        required_points=["사용하기 쉬운 정도"],
    )


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


def test_max_attempts_is_three():
    assert MAX_ATTEMPTS_PER_QUESTION == 3
