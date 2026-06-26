from __future__ import annotations

from typing import Annotated

import typer

from .config import load_app_config
from .llm_client import LLMJSONParseError
from .pipeline import document_output_dir, format_pipeline_error, inspect_session, run_parse_pipeline, run_study_pipeline
from .renderer import print_error, print_success


app = typer.Typer(help="Socratic lecture tutor CLI.")


@app.command()
def parse(
    pdf: Annotated[str, typer.Option("--pdf", help="PDF 파일 경로.")],
    output_dir: Annotated[str, typer.Option("--output-dir")] = "./outputs",
) -> None:
    """PDF만 Markdown으로 파싱해서 저장합니다."""
    try:
        config = load_app_config(pdf=pdf, output_dir=output_dir)
        doc = run_parse_pipeline(config)
    except Exception as exc:
        print_error(_humanize_error(exc))
        raise typer.Exit(code=1) from exc

    print_success(f"PDF 분석 완료: {document_output_dir(config, doc) / f'{doc.title}_parsed.md'}")


@app.command()
def start(
    pdf: Annotated[str, typer.Option("--pdf", help="PDF 파일 경로.")],
    subject: Annotated[str | None, typer.Option("--subject")] = None,
    difficulty: Annotated[str, typer.Option("--difficulty")] = "normal",
    output_language: Annotated[str, typer.Option("--output-language")] = "ko",
    max_concepts: Annotated[int, typer.Option("--max-concepts")] = 7,
    questions_per_concept: Annotated[int, typer.Option("--questions-per-concept")] = 3,
    model: Annotated[str | None, typer.Option("--model")] = None,
    output_dir: Annotated[str, typer.Option("--output-dir")] = "./outputs",
    cache_dir: Annotated[str, typer.Option("--cache-dir")] = "./cache",
    skip_cache: Annotated[bool, typer.Option("--skip-cache")] = False,
) -> None:
    """강의 PDF 기반 대화형 학습 세션을 시작합니다."""
    try:
        config = load_app_config(
            pdf=pdf,
            subject=subject,
            difficulty=difficulty,
            output_language=output_language,
            max_concepts=max_concepts,
            questions_per_concept=questions_per_concept,
            model=model,
            output_dir=output_dir,
            cache_dir=cache_dir,
            skip_cache=skip_cache,
        )
        run_study_pipeline(config)
    except typer.Exit:
        raise
    except Exception as exc:
        print_error(_humanize_error(exc))
        raise typer.Exit(code=1) from exc


@app.command()
def inspect(
    session: Annotated[str, typer.Option("--session", help="세션 JSON 경로.")],
) -> None:
    """이전 세션 JSON을 읽어서 요약을 출력합니다."""
    try:
        inspect_session(session)
    except Exception as exc:
        print_error(_humanize_error(exc))
        raise typer.Exit(code=1) from exc


def _humanize_error(exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return str(exc)
    if isinstance(exc, LLMJSONParseError):
        return "LLM 응답을 JSON으로 파싱하지 못했습니다.\n다시 실행하거나 모델을 변경해보세요."
    message = format_pipeline_error(exc)
    if "OPENAI_API_KEY" in message:
        return message
    if "Only PDF files" in message:
        return "MVP에서는 PDF 파일만 지원합니다."
    if "pymupdf" in message.lower() or "fitz" in message.lower():
        return "PDF 파싱에 실패했습니다.\n파일이 손상되었거나 텍스트 추출이 어려운 PDF일 수 있습니다."
    return message
