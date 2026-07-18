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
    ConceptAnswer,
    Question,
    SessionSummary,
    StudentAnswer,
    StudySession,
)
from .prompts import build_session_summary_prompt
from .renderer import console, print_evaluation, print_question
from .utils import utc_now


ANSWER_PROMPT = "이 개념에 대한 생각을 적어보세요 (/quit 종료, /skip 건너뛰기, /help 도움말)"
HELP_TEXT = "/skip 현재 개념 건너뛰기\n/quit 현재까지 답변으로 종료 및 리포트 생성\n/help 사용 가능한 명령어 표시"
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
                answer_text = typer.prompt("답변 (/quit 종료, /skip 건너뛰기, /help 도움말)").strip()
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
                llm_client, question, answer_text, attempts, output_language=config.output_language,
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
            if evaluation.next_action == "next_question" or attempts >= MAX_ATTEMPTS_PER_QUESTION:
                break

    session.ended_at = utc_now()
    return session


def run_concept_review_session(
    document_id: str,
    concepts: list[Concept],
    questions: list[Question],
    config: AppConfig,
    llm_client: object,
) -> StudySession:
    """개념별 자유 답변을 먼저 수집한 뒤 질문별 required_points를 일괄 평가합니다."""
    session = StudySession(
        session_id=f"concept_review_{utc_now().strftime('%Y%m%d_%H%M%S')}",
        document_id=document_id,
        difficulty=config.difficulty,
        output_language=config.output_language,
        concepts=concepts,
        questions=questions,
        started_at=utc_now(),
    )
    for index, concept in enumerate(concepts, start=1):
        while True:
            console.print(f"\n[bold][개념 {index}/{len(concepts)}] {concept.title}[/bold]")
            try:
                answer_text = typer.prompt(ANSWER_PROMPT).strip()
            except (KeyboardInterrupt, EOFError, typer.Abort):
                session.ended_at = utc_now()
                evaluate_concept_answers(session, llm_client)
                return session
            if not answer_text:
                console.print("[yellow]답변이 비어 있어요. 한 문장이라도 입력해보세요.[/yellow]")
                continue
            if answer_text == "/help":
                console.print(HELP_TEXT)
                continue
            if answer_text in END_COMMANDS:
                session.ended_at = utc_now()
                evaluate_concept_answers(session, llm_client)
                return session
            session.concept_answers.append(_concept_answer(concept, answer_text))
            break
    session.ended_at = utc_now()
    evaluate_concept_answers(session, llm_client)
    return session


def _concept_answer(concept: Concept, answer_text: str) -> ConceptAnswer:
    return ConceptAnswer(
        answer_id=f"concept_ans_{uuid.uuid4().hex[:8]}",
        concept_id=concept.concept_id,
        answer_text=answer_text,
        created_at=utc_now(),
    )


def evaluate_concept_answers(session: StudySession, llm_client: object) -> list[StudentAnswer]:
    """모든 개념 답변 수집 후 질문별 required_points 충족 여부를 일괄 평가합니다."""
    if session.answers:
        return session.answers
    questions_by_concept: dict[str, list[Question]] = defaultdict(list)
    for question in session.questions:
        questions_by_concept[question.concept_id].append(question)

    for concept_answer in session.concept_answers:
        for question in questions_by_concept.get(concept_answer.concept_id, []):
            if concept_answer.answer_text == "/skip":
                evaluated = _skipped_answer(question, 1)
            else:
                evaluation = evaluate_answer(
                    llm_client,
                    question,
                    concept_answer.answer_text,
                    3,
                    output_language=session.output_language,
                )
                evaluated = StudentAnswer(
                    answer_id=f"ans_{uuid.uuid4().hex[:8]}",
                    question_id=question.question_id,
                    attempt_number=1,
                    answer_text=concept_answer.answer_text,
                    evaluation=evaluation,
                    created_at=utc_now(),
                )
            session.answers.append(evaluated)
    return session.answers


def _skipped_answer(question: Question, attempt_number: int) -> StudentAnswer:
    return StudentAnswer(
        answer_id=f"ans_{uuid.uuid4().hex[:8]}",
        question_id=question.question_id,
        attempt_number=attempt_number,
        answer_text="/skip",
        evaluation=AnswerEvaluation(
            matched_points=[],
            missing_points=question.required_point_texts,
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
    progress = _session_progress(session)
    if llm_client is not None and session.answers:
        system_prompt, user_prompt = build_session_summary_prompt(
            session,
            output_language=session.output_language,
        )
        try:
            payload = llm_client.complete_json(system_prompt, user_prompt)
            summary = SessionSummary.model_validate(payload)
            summary.unanswered_concepts = progress["unanswered_concepts"]
            summary.completion_rate = progress["completion_rate"]
            session.summary = summary
            return summary
        except (ValidationError, RuntimeError, ValueError):
            pass

    summary = _fallback_summary(session)
    session.summary = summary
    return summary


def _session_progress(session: StudySession) -> dict:
    answered_question_ids = {answer.question_id for answer in session.answers}
    answered_concept_ids = {
        question.concept_id for question in session.questions if question.question_id in answered_question_ids
    }
    answered_concept_ids.update(answer.concept_id for answer in session.concept_answers)
    total = len(session.concepts)
    unanswered = [concept.title for concept in session.concepts if concept.concept_id not in answered_concept_ids]
    return {
        "completion_rate": (total - len(unanswered)) / total if total else 1.0,
        "unanswered_concepts": unanswered,
    }


def _fallback_summary(session: StudySession) -> SessionSummary:
    progress = _session_progress(session)
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
        unanswered_concepts=progress["unanswered_concepts"],
        completion_rate=progress["completion_rate"],
        overall_feedback="현재 답변 기록을 기준으로 생성한 로컬 요약입니다.",
    )
