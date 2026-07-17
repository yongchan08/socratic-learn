from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import AnswerEvaluation, Concept, Question, SessionSummary, StudySession


console = Console()


def print_header(text: str) -> None:
    console.rule(f"[bold]{text}[/bold]")


def print_warning(text: str) -> None:
    console.print(f"[yellow]{text}[/yellow]")


def print_success(text: str) -> None:
    console.print(f"[green]{text}[/green]")


def print_error(text: str) -> None:
    console.print(f"[red]{text}[/red]")


def print_concepts(concepts: list[Concept]) -> None:
    table = Table(title="추출된 핵심 개념", show_lines=False)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Concept")
    table.add_column("Summary")
    for index, concept in enumerate(concepts, start=1):
        table.add_row(str(index), concept.title, concept.summary)
    console.print(table)


def print_question(concept: Concept, question: Question, index: int, total: int) -> None:
    print_header(f"개념: {concept.title}")
    console.print(f"[bold][질문 {index}/{total}][/bold] {question.question}")


def print_evaluation(evaluation: AnswerEvaluation, attempt_number: int | None = None) -> None:
    if evaluation.next_action == "next_question":
        console.print(Panel(evaluation.feedback_to_student, title="평가", expand=False))
        if evaluation.reveal_missing_points and evaluation.missing_points:
            console.print("\n[bold]이번에는 빠진 핵심을 조금 더 직접적으로 알려드릴게요.[/bold]")
            console.print("\n[bold]보완할 내용:[/bold]")
            for point in evaluation.missing_points:
                console.print(f"- {point}")
            direct_hint = evaluation.hint or evaluation.improvement_note
            if direct_hint:
                console.print(f"\n[yellow]힌트 또는 짧은 설명: {direct_hint}[/yellow]")
            return
        if evaluation.matched_points:
            console.print("[bold]포함된 내용:[/bold]")
            for point in evaluation.matched_points:
                console.print(f"- {point}")
        if _should_print_improvement_note(evaluation):
            console.print("\n[bold]조금 더 보완하면 좋은 점:[/bold]")
            console.print(evaluation.improvement_note)
        return

    console.print(Panel(evaluation.feedback_to_student, title="평가", expand=False))
    follow_up = evaluation.socratic_follow_up or evaluation.hint
    if follow_up:
        console.print("\n[bold]한 단계 더 생각해볼게요.[/bold]")
        console.print(follow_up)
    console.print("\n[bold]다시 답변해보세요.[/bold]")


def _should_print_improvement_note(evaluation: AnswerEvaluation) -> bool:
    if not evaluation.improvement_note:
        return False
    return not _is_similar_text(evaluation.feedback_to_student, evaluation.improvement_note)


def _is_similar_text(left: str, right: str) -> bool:
    left_norm = _normalize_text(left)
    right_norm = _normalize_text(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    shorter, longer = sorted([left_norm, right_norm], key=len)
    if len(shorter) >= 20 and shorter in longer:
        return True
    left_tokens = set(left_norm.split())
    right_tokens = set(right_norm.split())
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    return overlap >= 0.85


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def print_session_summary(summary: SessionSummary) -> None:
    print_header("학습 세션 완료")
    console.print("[bold]잘 이해한 개념:[/bold]")
    for item in summary.strong_concepts or ["없음"]:
        console.print(f"- {item}")
    console.print("\n[bold]보완이 필요한 개념:[/bold]")
    for item in summary.weak_concepts or ["없음"]:
        console.print(f"- {item}")
    console.print("\n[bold]자주 빠뜨린 요소:[/bold]")
    for item in summary.frequently_missing_points or ["없음"]:
        console.print(f"- {item}")
    console.print("\n[bold]추천 복습 질문:[/bold]")
    for index, question in enumerate(summary.recommended_review_questions, start=1):
        console.print(f"{index}. {question}")
    console.print(f"\n[bold]종합 피드백:[/bold] {summary.overall_feedback}")


def print_required_points_report(session: StudySession) -> None:
    answers_by_question = {answer.question_id: answer for answer in session.answers}
    print_header("개념별 필수 요소 리포트")
    for concept in session.concepts:
        console.print(f"\n[bold]{concept.title}[/bold]")
        for question in (item for item in session.questions if item.concept_id == concept.concept_id):
            answer = answers_by_question.get(question.question_id)
            console.print(f"[cyan]{question.question_type}[/cyan] {question.question}")
            if answer is None:
                console.print("- 평가 기록 없음")
                continue
            matched = answer.evaluation.matched_points or ["없음"]
            missing = answer.evaluation.missing_points or ["없음"]
            console.print(f"- 충족: {', '.join(matched)}")
            console.print(f"- 미충족: {', '.join(missing)}")
