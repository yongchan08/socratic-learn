from __future__ import annotations

import uuid
from collections import defaultdict

import typer
from pydantic import ValidationError

from .config import AppConfig
from .evaluator import MAX_ATTEMPTS_PER_QUESTION, evaluate_answer
from .models import (
    AnswerEvaluation,
    Concept,
    Question,
    SessionSummary,
    StudentAnswer,
    StudySession,
)
from .prompts import build_session_summary_prompt
from .renderer import console, print_evaluation, print_question, print_session_summary
from .utils import utc_now


ANSWER_PROMPT = "답변 (/quit 종료, /skip 건너뛰기, /help 도움말)"
HELP_TEXT = "/skip 현재 질문 건너뛰기\n/quit 현재까지 답변으로 세션 종료 및 요약\n/help 사용 가능한 명령어 표시"
END_COMMANDS = {"/quit", "/exit", "/done"}


def run_interactive_session(
    document_id: str,
    concepts: list[Concept],
    questions: list[Question],
    config: AppConfig,
    llm_client: object,
) -> StudySession:
    session = StudySession(
        session_id=f"session_{utc_now().strftime('%Y%m%d_%H%M%S')}",
        document_id=document_id,
        subject=config.subject,
        difficulty=config.difficulty,
        output_language=config.output_language,
        concepts=concepts,
        questions=questions,
        started_at=utc_now(),
    )

    concept_by_id = {concept.concept_id: concept for concept in concepts}
    total = len(questions)

    for index, question in enumerate(questions, start=1):
        concept = concept_by_id[question.concept_id]
        attempts = 0
        while attempts < MAX_ATTEMPTS_PER_QUESTION:
            print_question(concept, question, index, total)
            try:
                answer_text = typer.prompt(ANSWER_PROMPT).strip()
            except (KeyboardInterrupt, EOFError, typer.Abort):
                console.print("\n[yellow]세션을 종료합니다. 현재까지의 답변으로 요약을 생성합니다.[/yellow]")
                session.ended_at = utc_now()
                return session

            if not answer_text:
                console.print("[yellow]답변이 비어 있어요. 한 문장이라도 입력해보세요.[/yellow]")
                continue
            if answer_text == "/help":
                console.print(HELP_TEXT)
                continue
            if answer_text in END_COMMANDS:
                console.print("[yellow]세션을 종료합니다. 현재까지의 답변으로 요약을 생성합니다.[/yellow]")
                session.ended_at = utc_now()
                return session
            if answer_text == "/skip":
                session.answers.append(_skipped_answer(question, attempts + 1))
                break

            attempts += 1
            evaluation = evaluate_answer(
                llm_client,
                question,
                answer_text,
                attempts,
                output_language=config.output_language,
            )
            session.answers.append(
                StudentAnswer(
                    answer_id=f"ans_{uuid.uuid4().hex[:8]}",
                    question_id=question.question_id,
                    attempt_number=attempts,
                    answer_text=answer_text,
                    evaluation=evaluation,
                    created_at=utc_now(),
                )
            )
            print_evaluation(evaluation, attempts)

            if evaluation.next_action == "next_question":
                if evaluation.reveal_missing_points and attempts >= MAX_ATTEMPTS_PER_QUESTION:
                    console.print("[yellow]최대 시도 횟수에 도달해 다음 질문으로 넘어갑니다.[/yellow]")
                else:
                    console.print("[green]다음 질문으로 넘어갑니다.[/green]")
                break
            if attempts >= MAX_ATTEMPTS_PER_QUESTION:
                console.print("[yellow]최대 시도 횟수에 도달해 다음 질문으로 넘어갑니다.[/yellow]")
                break

    session.ended_at = utc_now()
    return session


def _skipped_answer(question: Question, attempt_number: int) -> StudentAnswer:
    return StudentAnswer(
        answer_id=f"ans_{uuid.uuid4().hex[:8]}",
        question_id=question.question_id,
        attempt_number=attempt_number,
        answer_text="/skip",
        evaluation=AnswerEvaluation(
            matched_points=[],
            missing_points=question.required_points,
            misconceptions=[],
            score=0,
            status="insufficient",
            feedback_to_student="사용자가 이 질문을 건너뛰었습니다.",
            hint=None,
            next_action="next_question",
        ),
        created_at=utc_now(),
    )


def generate_session_summary(session: StudySession, llm_client: object | None = None) -> SessionSummary:
    if llm_client is not None and session.answers:
        system_prompt, user_prompt = build_session_summary_prompt(
            session,
            output_language=session.output_language,
        )
        try:
            payload = llm_client.complete_json(system_prompt, user_prompt)
            summary = SessionSummary.model_validate(payload)
            session.summary = summary
            return summary
        except (ValidationError, RuntimeError, ValueError):
            pass

    summary = _fallback_summary(session)
    session.summary = summary
    return summary


def _fallback_summary(session: StudySession) -> SessionSummary:
    questions_by_id = {question.question_id: question for question in session.questions}
    concepts_by_id = {concept.concept_id: concept for concept in session.concepts}
    scores: dict[str, list[float]] = defaultdict(list)
    missing: list[str] = []

    for answer in session.answers:
        question = questions_by_id.get(answer.question_id)
        if not question:
            continue
        scores[question.concept_id].append(answer.evaluation.score)
        missing.extend(answer.evaluation.missing_points)

    strong: list[str] = []
    weak: list[str] = []
    for concept in session.concepts:
        concept_scores = scores.get(concept.concept_id, [])
        if concept_scores and sum(concept_scores) / len(concept_scores) >= 0.75:
            strong.append(concept.title)
        elif concept_scores:
            weak.append(concept.title)

    frequent_missing = []
    for item in missing:
        if item not in frequent_missing:
            frequent_missing.append(item)
        if len(frequent_missing) >= 5:
            break

    review_questions = [
        f"{concepts_by_id[concept_id].title}을(를) 핵심 근거와 함께 다시 설명해보세요."
        for concept_id, concept_scores in scores.items()
        if concept_scores and sum(concept_scores) / len(concept_scores) < 0.75
    ][:5]

    return SessionSummary(
        strong_concepts=strong,
        weak_concepts=weak,
        frequently_missing_points=frequent_missing,
        recommended_review_questions=review_questions,
        overall_feedback="현재 답변 기록을 기준으로 생성한 로컬 요약입니다.",
    )


def show_summary(session: StudySession, llm_client: object | None = None) -> SessionSummary:
    summary = generate_session_summary(session, llm_client)
    print_session_summary(summary)
    return summary
