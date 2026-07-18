from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from pathlib import Path

import typer
from pydantic import ValidationError

from .config import MAX_CONCEPTS, QUESTIONS_PER_CONCEPT, AppConfig
from .llm_client import LLMClient
from .models import Concept, ConceptReviewReport, ParsedDocument, Question, StudySession
from .pdf_parser import parse_pdf_to_markdown
from .prompts import build_concept_extraction_prompt, build_question_generation_prompt
from .renderer import console, print_concepts, print_header, print_required_points_report, print_session_summary, print_warning
from .session import generate_session_summary, run_concept_review_session, run_interactive_session
from .storage import cache_path, compute_file_hash, ensure_dir, legacy_cache_path, load_json, save_json, save_text
from .utils import truncate_markdown, utc_now


QUESTION_GENERATION_TIMEOUT_SECONDS = 120.0


class QuestionGenerationTimeoutError(RuntimeError):
    pass


class QuestionGenerationError(RuntimeError):
    pass


def run_parse_pipeline(config: AppConfig) -> ParsedDocument:
    if config.pdf_path is None:
        raise ValueError("--pdf is required.")
    console.print("PDF 파싱 중...")
    doc = parse_pdf_to_markdown(str(config.pdf_path))
    output_dir = document_output_dir(config, doc)
    save_text(doc.markdown, output_dir / f"{doc.title}_parsed.md")
    save_text(doc.markdown, output_dir / f"parsed_{doc.document_id}.md")
    save_json(doc, output_dir / f"parsed_{doc.document_id}.json")
    return doc


def run_study_pipeline(config: AppConfig) -> StudySession:
    if not config.api_key:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.\n.env 파일을 만들고 OPENAI_API_KEY를 추가하세요.")

    llm_client = LLMClient(model=config.model, api_key=config.api_key)
    parsed_doc, file_hash = parse_or_load_pdf(config)
    markdown_for_llm, was_truncated = truncate_markdown(parsed_doc.markdown)
    if was_truncated:
        print_warning("PDF 텍스트가 길어 일부만 사용합니다. 시작, 중간, 끝 부분을 보존했습니다.")

    concepts = extract_or_load_concepts(parsed_doc, markdown_for_llm, file_hash, config, llm_client)
    if not concepts:
        raise ValueError("핵심 개념을 추출하지 못했습니다.\nPDF에 텍스트가 충분히 포함되어 있는지 확인하세요.")

    print_header("PDF 분석 완료")
    print_concepts(concepts)
    if not typer.confirm("이 개념들로 학습을 시작할까요?", default=True):
        raise typer.Exit(code=0)

    questions = generate_or_load_questions(parsed_doc, concepts, markdown_for_llm, file_hash, config, llm_client)
    session = run_interactive_session(parsed_doc.document_id, concepts, questions, config, llm_client)
    summary = generate_session_summary(session, llm_client)
    session.ended_at = session.ended_at or utc_now()
    save_path = save_json(session, document_output_dir(config, parsed_doc) / f"{session.session_id}.json")
    print_session_summary(summary)
    console.print(f"\n세션 결과가 저장되었습니다:\n{save_path}")
    return session


def run_concept_review_pipeline(config: AppConfig) -> StudySession:
    """기존 학습 세션과 별개로 개념별 자유 답변 및 일괄 평가를 실행합니다."""
    if not config.api_key:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.\n.env 파일을 만들고 OPENAI_API_KEY를 추가하세요.")
    llm_client = LLMClient(model=config.model, api_key=config.api_key)
    parsed_doc, _ = parse_or_load_pdf(config)
    concepts, questions = load_generated_learning_materials(parsed_doc, config)
    session = run_concept_review_session(parsed_doc.document_id, concepts, questions, config, llm_client)
    summary = generate_session_summary(session, llm_client)
    save_path = save_concept_review_report(session, parsed_doc, config)
    print_required_points_report(session)
    print_session_summary(summary)
    console.print(f"\n개념 리포트가 저장되었습니다:\n{save_path}")
    return session


def load_generated_learning_materials(
    parsed_doc: ParsedDocument,
    config: AppConfig,
    file_hash: str | None = None,
    material_store: object | None = None,
) -> tuple[list[Concept], list[Question]]:
    if material_store is not None and file_hash is not None:
        concepts = material_store.load_concepts(file_hash, config.difficulty, config.output_language)
        questions = material_store.load_questions(file_hash, config.difficulty, config.output_language)
        if concepts is None or questions is None:
            raise FileNotFoundError(
                "개념 리포트에 필요한 기존 학습 자료가 데이터베이스에 없습니다. "
                "먼저 같은 PDF와 설정으로 질문 학습을 실행해 개념과 질문을 생성하세요."
            )
        return concepts, questions
    output_dir = document_output_dir(config, parsed_doc)
    concepts_path = output_dir / f"concepts_{parsed_doc.document_id}.json"
    questions_path = output_dir / f"questions_{parsed_doc.document_id}.json"
    missing = [path.name for path in (concepts_path, questions_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "개념 리포트에 필요한 기존 학습 파일이 없습니다: "
            f"{', '.join(missing)}\n먼저 같은 PDF로 start 기능을 실행해 개념과 질문을 생성하세요."
        )
    concepts = [Concept.model_validate(item) for item in load_json(concepts_path)]
    questions = [Question.model_validate(item) for item in load_json(questions_path)]
    return concepts, questions


def save_concept_review_report(
    session: StudySession,
    parsed_doc: ParsedDocument,
    config: AppConfig,
) -> Path:
    output_dir = document_output_dir(config, parsed_doc)
    report = ConceptReviewReport(
        review_id=session.session_id,
        document_id=session.document_id,
        concepts_file=f"concepts_{parsed_doc.document_id}.json",
        questions_file=f"questions_{parsed_doc.document_id}.json",
        concept_answers=session.concept_answers,
        evaluations=session.answers,
        summary=session.summary,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )
    return save_json(report, output_dir / f"{session.session_id}.json")


def parse_or_load_pdf(config: AppConfig, material_store: object | None = None) -> tuple[ParsedDocument, str]:
    if config.pdf_path is None:
        raise ValueError("--pdf is required.")
    file_hash = compute_file_hash(config.pdf_path)
    if material_store is not None:
        doc = None if config.skip_cache else material_store.load_document(file_hash)
        if doc is None:
            console.print("PDF 파싱 중...")
            doc = parse_pdf_to_markdown(str(config.pdf_path))
            material_store.save_document(file_hash, doc)
        return doc, file_hash
    cached = cache_path(config.cache_dir, file_hash, "parsed.json", source_path=config.pdf_path)
    legacy_cached = legacy_cache_path(config.cache_dir, file_hash, "parsed.json")
    if cached.exists() and not config.skip_cache:
        doc = ParsedDocument.model_validate(load_json(cached))
    elif legacy_cached.exists() and not config.skip_cache:
        doc = ParsedDocument.model_validate(load_json(legacy_cached))
        save_json(doc, cached)
    else:
        console.print("PDF 파싱 중...")
        doc = parse_pdf_to_markdown(str(config.pdf_path))
        save_json(doc, cached)

    output_dir = document_output_dir(config, doc)
    save_text(doc.markdown, output_dir / f"parsed_{doc.document_id}.md")
    save_json(doc, output_dir / f"parsed_{doc.document_id}.json")
    return doc, file_hash


def extract_or_load_concepts(
    parsed_doc: ParsedDocument,
    markdown: str,
    file_hash: str,
    config: AppConfig,
    llm_client: object,
    material_store: object | None = None,
) -> list[Concept]:
    if material_store is not None and not config.skip_cache:
        stored = material_store.load_concepts(file_hash, config.difficulty, config.output_language)
        if stored is not None:
            return stored[:MAX_CONCEPTS]
    cached = cache_path(
        config.cache_dir,
        file_hash,
        f"concepts_auto_{MAX_CONCEPTS}_{config.output_language}.json",
        title=parsed_doc.title,
    )
    if material_store is None and cached.exists() and not config.skip_cache:
        concepts = [Concept.model_validate(item) for item in load_json(cached)[:MAX_CONCEPTS]]
        save_json(concepts, document_output_dir(config, parsed_doc) / f"concepts_{parsed_doc.document_id}.json")
        return concepts

    system_prompt, user_prompt = build_concept_extraction_prompt(
        markdown=markdown,
        difficulty=config.difficulty,
        output_language=config.output_language,
    )
    payload = llm_client.complete_json(system_prompt, user_prompt)
    raw_concepts = payload.get("concepts", [])
    concepts = []
    for index, item in enumerate(raw_concepts[:MAX_CONCEPTS], start=1):
        item = dict(item)
        item["concept_id"] = f"concept_{index:03d}"
        concepts.append(Concept.model_validate(item))

    if material_store is not None:
        material_store.save_concepts(file_hash, config.difficulty, config.output_language, concepts)
    else:
        save_json(concepts, cached)
        save_json(concepts, document_output_dir(config, parsed_doc) / f"concepts_{parsed_doc.document_id}.json")
    return concepts


def generate_or_load_questions(
    parsed_doc: ParsedDocument,
    concepts: list[Concept],
    markdown: str,
    file_hash: str,
    config: AppConfig,
    llm_client: object,
    on_progress: object | None = None,
    material_store: object | None = None,
) -> list[Question]:
    """개념별 질문을 생성합니다. 캐시가 없으면 ThreadPoolExecutor로 병렬 생성합니다.

    Args:
        on_progress: 각 개념 완료 시 호출되는 콜백 (concept_index: int, total: int) -> None
    """
    cached = cache_path(
        config.cache_dir,
        file_hash,
        f"questions_{config.output_language}_v6_unified_points_q{QUESTIONS_PER_CONCEPT}.json",
        title=parsed_doc.title,
    )
    if material_store is not None and not config.skip_cache:
        stored = material_store.load_questions(file_hash, config.difficulty, config.output_language)
        if stored is not None:
            return stored
    if material_store is None and cached.exists() and not config.skip_cache:
        questions = [Question.model_validate(item) for item in load_json(cached)]
        save_json(questions, document_output_dir(config, parsed_doc) / f"questions_{parsed_doc.document_id}.json")
        return questions

    total = len(concepts)

    def _generate_for_concept(args: tuple) -> tuple[int, list[Question]]:
        concept_index, concept = args
        excerpt = _excerpt_for_concept(parsed_doc, concept, markdown)
        system_prompt, user_prompt = build_question_generation_prompt(
            concept=concept,
            document_excerpt=excerpt,
            output_language=config.output_language,
        )
        try:
            payload = llm_client.complete_json(system_prompt, user_prompt)
        except Exception as exc:
            raise QuestionGenerationError(
                f"'{concept.title}' ({concept.concept_id}) 개념의 질문 생성에 실패했습니다: {exc}"
            ) from exc
        raw_questions = payload.get("questions", [])
        qs: list[Question] = []
        for question_index, item in enumerate(raw_questions[:QUESTIONS_PER_CONCEPT], start=1):
            item = dict(item)
            _assign_required_point_ids(item)
            item["concept_id"] = concept.concept_id
            item["question_id"] = f"q_{concept_index:03d}_{question_index:03d}"
            question = Question.model_validate(item)
            qs.append(question)
        _validate_question_mix(qs)
        return concept_index, qs

    # 최대 7개 스레드로 병렬 처리 (OpenAI API는 스레드 안전)
    pool = ThreadPoolExecutor(max_workers=min(total, 7))
    timed_out = False
    try:
        futures = {pool.submit(_generate_for_concept, (i, c)): i for i, c in enumerate(concepts, start=1)}
        results = _collect_question_results(futures, total, on_progress)
    except QuestionGenerationTimeoutError:
        timed_out = True
        raise
    finally:
        pool.shutdown(wait=not timed_out, cancel_futures=timed_out)

    # 원래 순서대로 정렬
    questions: list[Question] = []
    for i in sorted(results):
        questions.extend(results[i])

    if material_store is not None:
        material_store.save_questions(file_hash, config.difficulty, config.output_language, questions)
    else:
        save_json(questions, cached)
        save_json(questions, document_output_dir(config, parsed_doc) / f"questions_{parsed_doc.document_id}.json")
    return questions


def _validate_question_mix(questions: list[Question]) -> None:
    question_types = [question.question_type for question in questions]
    if len(questions) != QUESTIONS_PER_CONCEPT or question_types[0] != "explanation" or question_types[1] not in {
        "comparison",
        "application",
    }:
        raise ValueError(
            "Generated questions must contain one explanation question followed by one comparison or application question."
        )


def _assign_required_point_ids(question_data: dict) -> None:
    """LLM 의미 출력과 무관한 point_id를 배열 순서에 따라 결정적으로 부여합니다."""
    required_points = question_data.get("required_points")
    if not isinstance(required_points, list):
        return
    for index, point in enumerate(required_points, start=1):
        if isinstance(point, dict):
            point["point_id"] = f"rp_{index:03d}"


def _collect_question_results(
    futures: dict[Future, int],
    total: int,
    on_progress: object | None,
    timeout_seconds: float = QUESTION_GENERATION_TIMEOUT_SECONDS,
) -> dict[int, list[Question]]:
    results: dict[int, list[Question]] = {}
    completed = 0
    try:
        for future in as_completed(futures, timeout=timeout_seconds):
            concept_index, questions = future.result()
            results[concept_index] = questions
            completed += 1
            if on_progress:
                on_progress(completed, total)
    except FuturesTimeoutError as exc:
        for future in futures:
            future.cancel()
        raise QuestionGenerationTimeoutError(
            f"질문 생성이 제한 시간 {int(timeout_seconds)}초를 초과했습니다."
        ) from exc
    return results


def document_output_dir(config: AppConfig, parsed_doc: ParsedDocument) -> Path:
    folder_name = f"{parsed_doc.title or 'document'}_{parsed_doc.document_id}"
    return ensure_dir(config.output_dir / folder_name)


def _excerpt_for_concept(parsed_doc: ParsedDocument, concept: Concept, markdown: str) -> str:
    page_numbers = set(concept.source_pages)
    pages = [page.markdown for page in parsed_doc.pages if page.page_number in page_numbers]
    excerpt = "\n\n".join(pages).strip() or markdown
    return excerpt[:12_000]


def load_session(path: str | Path) -> StudySession:
    return StudySession.model_validate(load_json(path))


def inspect_session(path: str | Path) -> StudySession:
    session = load_session(path)
    if session.summary:
        print_session_summary(session.summary)
    else:
        summary = generate_session_summary(session, llm_client=None)
        print_session_summary(summary)
    return session


def format_pipeline_error(error: Exception) -> str:
    if isinstance(error, ValidationError):
        return f"LLM 응답이 예상 스키마와 다릅니다.\n{error}"
    return str(error)
