from __future__ import annotations

import math
import uuid
from pathlib import Path
from threading import Lock

from .config import AppConfig, load_app_config
from .evaluator import MAX_ATTEMPTS_PER_QUESTION, evaluate_answer
from .llm_client import LLMClient
from .models import AnswerEvaluation, ConceptAnswer, Question, StudentAnswer, StudySession
from .pipeline import (
    document_output_dir,
    extract_or_load_concepts,
    extract_syllabus_weeks,
    generate_or_load_questions,
    load_generated_learning_materials,
    parse_or_load_pdf,
    save_concept_review_report,
)
from .session import evaluate_concept_answers, generate_session_summary
from .storage import save_json
from .session_store import PostgresSessionStore, StoredWebSession
from .utils import truncate_markdown, utc_now

END_COMMANDS = {"/quit", "/exit", "/done"}


class WebStudyError(ValueError):
    pass


class WebStudyManager:
    def __init__(self, session_store=None) -> None:
        self._sessions: dict[str, StudySession] = {}
        self._configs: dict[str, AppConfig] = {}
        self._llm_clients: dict[str, LLMClient] = {}
        self._current_indexes: dict[str, int] = {}
        self._session_modes: dict[str, str] = {}
        self._document_titles: dict[str, str | None] = {}
        self._course_links: dict[str, tuple[str, int]] = {}
        self._lock = Lock()
        self._session_store = session_store if session_store is not None else PostgresSessionStore.from_environment()

    def create_session(
        self,
        pdf_path: str | Path,
        difficulty: str = "normal",
        output_language: str = "ko",
        model: str | None = None,
        output_dir: str = "./outputs",
        cache_dir: str = "./cache",
        skip_cache: bool = False,
        on_progress: dict | None = None,
        session_mode: str = "study",
        course_id: str | None = None,
        stage_index: int | None = None,
    ) -> StudySession:
        """학습 세션을 생성합니다.

        Args:
            on_progress: 진행 단계별 콜백 딕셔너리. 다음 키를 지원합니다:
                - "after_parse": PDF 파싱 완료 후 호출 () -> None
                - "after_concepts": 개념 추출 완료 후 호출 () -> None
                - "on_questions_progress": 질문 생성 진행 중 호출 (done: int, total: int) -> None
        """
        config = load_app_config(
            pdf=str(pdf_path),
            difficulty=difficulty,
            output_language=output_language,
            model=model or None,
            output_dir=output_dir,
            cache_dir=cache_dir,
            skip_cache=skip_cache,
        )
        if not config.api_key:
            raise WebStudyError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

        _cb = on_progress or {}

        llm_client = LLMClient(model=config.model, api_key=config.api_key)
        material_store = self._session_store
        parsed_doc, file_hash = parse_or_load_pdf(config, material_store=material_store)

        if cb := _cb.get("after_parse"):
            cb()

        if session_mode == "concept_review":
            try:
                concepts, questions = load_generated_learning_materials(
                    parsed_doc, config, file_hash=file_hash, material_store=material_store
                )
            except FileNotFoundError as exc:
                raise WebStudyError(str(exc)) from exc
        else:
            markdown_for_llm, _ = truncate_markdown(parsed_doc.markdown)
            concepts = extract_or_load_concepts(
                parsed_doc, markdown_for_llm, file_hash, config, llm_client, material_store=material_store
            )
            if not concepts:
                raise WebStudyError("핵심 개념을 추출하지 못했습니다.")
            if cb := _cb.get("after_concepts"):
                cb()
            questions = generate_or_load_questions(
                parsed_doc, concepts, markdown_for_llm, file_hash, config, llm_client,
                on_progress=_cb.get("on_questions_progress"),
                material_store=material_store,
            )
        if not questions:
            raise WebStudyError("질문을 생성하지 못했습니다.")

        session = StudySession(
            session_id=f"session_{utc_now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            document_id=parsed_doc.document_id,
            difficulty=config.difficulty,
            output_language=config.output_language,
            concepts=concepts,
            questions=questions,
            started_at=utc_now(),
        )

        with self._lock:
            self._sessions[session.session_id] = session
            self._configs[session.session_id] = config
            self._llm_clients[session.session_id] = llm_client
            self._current_indexes[session.session_id] = 0
            self._session_modes[session.session_id] = session_mode
            self._document_titles[session.session_id] = parsed_doc.title
            if course_id is not None and stage_index is not None:
                self._course_links[session.session_id] = (course_id, stage_index)
                self._attach_course_session(course_id, stage_index, session.session_id, parsed_doc.title)
        self._persist(session.session_id)
        return session

    def create_course(self, title: str | None = None, week_count: int = 13) -> dict:
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용하려면 DATABASE_URL 설정이 필요합니다.")
        if not (1 <= week_count <= 52):
            raise WebStudyError("주차 수는 1에서 52 사이여야 합니다.")
        course = {
            "course_id": f"course_{uuid.uuid4().hex[:12]}",
            "title": title.strip() if title and title.strip() else "새 학습 로드맵",
            "week_count": week_count,
            "stages": self._build_stage_list(week_count),
            "final_review_session_id": None,
            "created_at": utc_now().isoformat(),
        }
        self._session_store.save_course(course)
        return course

    def create_course_from_syllabus(self, pdf_path: str | Path, title: str | None = None) -> dict:
        """강의계획서 PDF를 분석해 주차별 학습 주제가 반영된 로드맵을 생성합니다."""
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용하려면 DATABASE_URL 설정이 필요합니다.")
        config = load_app_config(pdf=str(pdf_path))
        if not config.api_key:
            raise WebStudyError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        llm_client = LLMClient(model=config.model, api_key=config.api_key)
        parsed_doc, _ = parse_or_load_pdf(config, material_store=self._session_store)
        markdown_for_llm, _ = truncate_markdown(parsed_doc.markdown)
        topics = extract_syllabus_weeks(markdown_for_llm, config, llm_client)
        if not topics:
            raise WebStudyError("강의계획서에서 주차별 항목을 찾지 못했습니다. 다른 파일을 시도해주세요.")

        week_count = max(1, min(len(topics), 52))
        course = self.create_course(title or parsed_doc.title, week_count=week_count)
        week_stages = [stage for stage in course["stages"] if stage["kind"] == "week"]
        for stage, topic in zip(week_stages, topics):
            stage["title"] = topic
        self._session_store.save_course(course)
        return course

    @staticmethod
    def _build_stage_list(week_count: int) -> list[dict]:
        """N주차 로드맵을 생성합니다.

        절반 지점에 중간고사, 마지막에 기말고사를 삽입합니다. 각 체크포인트는
        직전 체크포인트(또는 처음) 이후의 주차들만 종합 리뷰 대상으로 삼습니다.
        """
        midterm_at = math.ceil(week_count / 2)
        stages: list[dict] = []
        stage_index = 1

        def add_week(week_number: int) -> int:
            nonlocal stage_index
            stages.append({
                "stage_index": stage_index, "kind": "week", "title": f"{week_number}주차 강의",
                "session_id": None, "document_title": None, "completed": False,
            })
            index = stage_index
            stage_index += 1
            return index

        def add_checkpoint(checkpoint_type: str, title: str, source_stage_indexes: list[int]) -> None:
            nonlocal stage_index
            stages.append({
                "stage_index": stage_index, "kind": "checkpoint", "checkpoint_type": checkpoint_type,
                "title": title, "session_id": None, "document_title": None, "completed": False,
                "source_stage_indexes": source_stage_indexes,
            })
            stage_index += 1

        midterm_sources = [add_week(week_number) for week_number in range(1, midterm_at + 1)]
        add_checkpoint("midterm", "중간고사", midterm_sources)
        final_sources = [add_week(week_number) for week_number in range(midterm_at + 1, week_count + 1)]
        add_checkpoint("final", "기말고사", final_sources or midterm_sources)
        return stages

    def normalize_course(self, course: dict, *, persist: bool = True) -> dict:
        """이전 3단계 고정 로드맵을 새 week/checkpoint 구조로 읽기 시점에 보정합니다."""
        changed = False
        stages = course.get("stages", [])
        for stage in stages:
            if "kind" not in stage:
                stage["kind"] = "week"
                changed = True
        if not any(stage.get("kind") == "checkpoint" for stage in stages):
            source_indexes = [stage["stage_index"] for stage in stages]
            next_index = max(source_indexes, default=0) + 1
            stages.append({
                "stage_index": next_index, "kind": "checkpoint", "checkpoint_type": "final",
                "title": "최종 개념 리포트", "session_id": course.get("final_review_session_id"),
                "document_title": None, "completed": bool(course.get("final_review_session_id")),
                "source_stage_indexes": source_indexes,
            })
            course["stages"] = stages
            changed = True
        if "week_count" not in course:
            course["week_count"] = sum(1 for stage in stages if stage.get("kind") == "week")
            changed = True
        if changed and persist and self._session_store is not None:
            self._session_store.save_course(course)
        return course

    @staticmethod
    def _find_stage(course: dict, stage_index: int) -> dict:
        for stage in course.get("stages", []):
            if stage["stage_index"] == stage_index:
                return stage
        raise WebStudyError("올바르지 않은 학습 단계입니다.")

    def list_courses(self) -> list[dict]:
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용하려면 DATABASE_URL 설정이 필요합니다.")
        return [self.normalize_course(course, persist=False) for course in self._session_store.list_courses()]

    def delete_course(self, course_id: str) -> None:
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용할 수 없습니다.")
        session_ids = self._session_store.delete_course(course_id)
        if session_ids is None:
            raise WebStudyError("학습 로드맵을 찾을 수 없습니다.")
        with self._lock:
            for session_id in session_ids:
                self._sessions.pop(session_id, None)
                self._configs.pop(session_id, None)
                self._llm_clients.pop(session_id, None)
                self._current_indexes.pop(session_id, None)
                self._session_modes.pop(session_id, None)
                self._document_titles.pop(session_id, None)
                self._course_links.pop(session_id, None)

    def get_course(self, course_id: str) -> dict:
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용할 수 없습니다.")
        course = self._session_store.load_course(course_id)
        if course is None:
            raise WebStudyError("학습 로드맵을 찾을 수 없습니다.")
        return self.normalize_course(course)

    def create_checkpoint_review(self, course_id: str, stage_index: int) -> StudySession:
        course = self.get_course(course_id)
        stage = self._find_stage(course, stage_index)
        if stage.get("kind") != "checkpoint":
            raise WebStudyError("올바르지 않은 중간·기말고사 단계입니다.")
        if stage.get("session_id"):
            return self.get_session(stage["session_id"])

        source_indexes = set(stage.get("source_stage_indexes", []))
        source_stages = [s for s in course["stages"] if s["stage_index"] in source_indexes]
        if not source_stages or not all(s["completed"] for s in source_stages):
            raise WebStudyError("이전 학습 단계를 모두 완료해야 중간·기말고사를 시작할 수 있습니다.")
        stored_stages = [self._session_store.load(s["session_id"]) for s in source_stages]
        if any(stored is None for stored in stored_stages):
            raise WebStudyError("단계별 학습 세션을 불러오지 못했습니다.")

        concepts: list = []
        questions: list[Question] = []
        for source_stage, stored in zip(source_stages, stored_stages):
            prefix = f"stage_{source_stage['stage_index']}_"
            concept_ids = {}
            for concept in stored.session.concepts:
                new_id = f"{prefix}{concept.concept_id}"
                concept_ids[concept.concept_id] = new_id
                concepts.append(concept.model_copy(update={"concept_id": new_id}))
            for question in stored.session.questions:
                questions.append(question.model_copy(update={
                    "question_id": f"{prefix}{question.question_id}",
                    "concept_id": concept_ids[question.concept_id],
                }))

        first = stored_stages[0]
        session = StudySession(
            session_id=f"checkpoint_{utc_now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            document_id=course_id,
            difficulty=first.session.difficulty,
            output_language=first.session.output_language,
            concepts=concepts,
            questions=questions,
            started_at=utc_now(),
        )
        config = load_app_config(
            difficulty=session.difficulty,
            output_language=session.output_language,
            model=first.config.get("model"),
        )
        with self._lock:
            self._sessions[session.session_id] = session
            self._configs[session.session_id] = config
            self._llm_clients[session.session_id] = LLMClient(model=config.model, api_key=config.api_key)
            self._current_indexes[session.session_id] = 0
            self._session_modes[session.session_id] = "concept_review"
            self._document_titles[session.session_id] = f"{course['title']} · {stage['title']}"
            self._course_links[session.session_id] = (course_id, stage_index)
        stage["session_id"] = session.session_id
        if stage.get("checkpoint_type") == "final":
            course["final_review_session_id"] = session.session_id
        self._session_store.save_course(course)
        self._persist(session.session_id)
        return session

    def get_session(self, session_id: str) -> StudySession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            if self._restore(session_id):
                return self._sessions[session_id]
            raise WebStudyError("학습 세션을 찾을 수 없습니다.") from exc

    def current_question(self, session_id: str) -> Question | None:
        session = self.get_session(session_id)
        index = self._current_indexes.get(session_id, 0)
        if index >= len(session.questions):
            return None
        return session.questions[index]

    def answer(self, session_id: str, answer_text: str) -> StudySession:
        answer_text = answer_text.strip()
        if not answer_text:
            raise WebStudyError("답변이 비어 있습니다.")
        command = answer_text.lower()
        if command in END_COMMANDS:
            return self.finish(session_id, end_reason="user_quit")
        if command == "/skip":
            return self.skip(session_id)
        if self.get_session(session_id).ended_at is not None:
            raise WebStudyError("이미 종료된 학습 세션입니다.")
        if self._session_modes.get(session_id) == "concept_review":
            return self._answer_concept_review(session_id, answer_text)
        question = self.current_question(session_id)
        if question is None:
            return self.finish(session_id, end_reason="all_answered")

        session = self.get_session(session_id)
        attempt_number = self._attempt_number(session, question)
        if attempt_number > MAX_ATTEMPTS_PER_QUESTION:
            self._advance(session_id)
            self._persist(session_id)
            return session
        config = self._configs[session_id]
        evaluation = evaluate_answer(
            self._llm_clients[session_id], question, answer_text, attempt_number, output_language=config.output_language,
        )
        session.answers.append(
            StudentAnswer(
                answer_id=f"ans_{uuid.uuid4().hex[:8]}",
                question_id=question.question_id,
                attempt_number=attempt_number,
                answer_text=answer_text,
                evaluation=evaluation,
                created_at=utc_now(),
            )
        )
        if evaluation.next_action == "next_question" or attempt_number >= MAX_ATTEMPTS_PER_QUESTION:
            self._advance(session_id)
        if self.current_question(session_id) is None:
            self.finish(session_id, end_reason="all_answered")
        else:
            self._persist(session_id)
        return session

    def skip(self, session_id: str) -> StudySession:
        if self.get_session(session_id).ended_at is not None:
            raise WebStudyError("이미 종료된 학습 세션입니다.")
        if self._session_modes.get(session_id) == "concept_review":
            return self._answer_concept_review(session_id, "/skip")
        question = self.current_question(session_id)
        if question is None:
            return self.finish(session_id, end_reason="all_answered")
        session = self.get_session(session_id)
        session.answers.append(
            StudentAnswer(
                answer_id=f"ans_{uuid.uuid4().hex[:8]}",
                question_id=question.question_id,
                attempt_number=self._attempt_number(session, question),
                answer_text="/skip",
                evaluation=AnswerEvaluation(
                    matched_points=[], missing_points=question.required_point_texts, misconceptions=[], score=0,
                    status="insufficient", feedback_to_student="사용자가 이 질문을 건너뛰었습니다.",
                    next_action="next_question",
                ),
                created_at=utc_now(),
            )
        )
        self._advance(session_id)
        if self.current_question(session_id) is None:
            self.finish(session_id, end_reason="all_answered")
        else:
            self._persist(session_id)
        return session

    def finish(self, session_id: str, end_reason: str = "user_quit") -> StudySession:
        session = self.get_session(session_id)
        if session.ended_at is None:
            fully_completed = self._all_items_answered(session_id)
            config = self._configs[session_id]
            llm_client = self._llm_clients.get(session_id)
            if self._session_modes.get(session_id) == "concept_review" and llm_client is not None:
                evaluate_concept_answers(session, llm_client)
            generate_session_summary(session, llm_client)
            session.ended_at = utc_now()
            session.completion_status = "completed" if fully_completed else "ended_early"
            session.end_reason = "all_answered" if fully_completed else end_reason
            if self._session_store is None:
                if self._session_modes.get(session_id) == "concept_review":
                    save_concept_review_report(
                        session,
                        _DocumentRef(session.document_id, self._document_titles.get(session_id)),
                        config,
                    )
                else:
                    save_json(
                        session,
                        document_output_dir(
                            config, _DocumentRef(session.document_id, self._document_titles.get(session_id))
                        ) / f"{session.session_id}.json",
                    )
            self._persist(session_id)
            if fully_completed:
                self._complete_course_stage(session_id)
        return session

    def _all_items_answered(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        index = self._current_indexes.get(session_id, 0)
        if self._session_modes.get(session_id) == "concept_review":
            answered = {answer.concept_id for answer in session.concept_answers}
            return index >= len(session.concepts) and all(
                concept.concept_id in answered for concept in session.concepts
            )
        answered = {answer.question_id for answer in session.answers}
        return index >= len(session.questions) and all(
            question.question_id in answered for question in session.questions
        )

    def snapshot(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if self._session_modes.get(session_id) == "concept_review":
            return self._concept_review_snapshot(session_id, session)
        question = self.current_question(session_id)
        index = self._current_indexes.get(session_id, 0)
        return {
            "session": session.model_dump(mode="json"),
            "current_question": question.model_dump(mode="json") if question else None,
            "current_index": min(index, len(session.questions)),
            "total_questions": len(session.questions),
            "last_answer": session.answers[-1].model_dump(mode="json") if session.answers else None,
            "completed": session.ended_at is not None,
        }

    def _advance(self, session_id: str) -> None:
        self._current_indexes[session_id] = self._current_indexes.get(session_id, 0) + 1

    def _attempt_number(self, session: StudySession, question: Question) -> int:
        return sum(1 for answer in session.answers if answer.question_id == question.question_id) + 1

    def _answer_concept_review(self, session_id: str, answer_text: str) -> StudySession:
        session = self.get_session(session_id)
        if session.ended_at is not None:
            raise WebStudyError("이미 종료된 학습 세션입니다.")
        index = self._current_indexes.get(session_id, 0)
        if index >= len(session.concepts):
            return self.finish(session_id, end_reason="all_answered")
        concept = session.concepts[index]
        session.concept_answers.append(
            ConceptAnswer(
                answer_id=f"concept_ans_{uuid.uuid4().hex[:8]}",
                concept_id=concept.concept_id,
                answer_text=answer_text,
                created_at=utc_now(),
            )
        )
        self._advance(session_id)
        if self._current_indexes[session_id] >= len(session.concepts):
            self.finish(session_id, end_reason="all_answered")
        else:
            self._persist(session_id)
        return session

    def _persist(self, session_id: str) -> None:
        if self._session_store is None:
            return
        session = self._sessions[session_id]
        config = self._configs[session_id]
        self._session_store.save(
            StoredWebSession(
                session=session,
                current_index=self._current_indexes.get(session_id, 0),
                session_mode=self._session_modes.get(session_id, "study"),
                document_title=self._document_titles.get(session_id),
                config={
                    "model": config.model,
                    "output_dir": str(config.output_dir),
                    "cache_dir": str(config.cache_dir),
                    "skip_cache": config.skip_cache,
                    "course_id": self._course_links.get(session_id, (None, None))[0],
                    "stage_index": self._course_links.get(session_id, (None, None))[1],
                },
            )
        )

    def _restore(self, session_id: str) -> bool:
        if self._session_store is None:
            return False
        stored = self._session_store.load(session_id)
        if stored is None:
            return False
        config = load_app_config(
            difficulty=stored.session.difficulty,
            output_language=stored.session.output_language,
            model=stored.config.get("model"),
            output_dir=stored.config.get("output_dir", "./outputs"),
            cache_dir=stored.config.get("cache_dir", "./cache"),
            skip_cache=stored.config.get("skip_cache", False),
        )
        with self._lock:
            self._sessions[session_id] = stored.session
            self._configs[session_id] = config
            self._llm_clients[session_id] = LLMClient(model=config.model, api_key=config.api_key)
            self._current_indexes[session_id] = stored.current_index
            self._session_modes[session_id] = stored.session_mode
            self._document_titles[session_id] = stored.document_title
            course_id = stored.config.get("course_id")
            stage_index = stored.config.get("stage_index")
            if course_id is not None and stage_index is not None:
                self._course_links[session_id] = (course_id, int(stage_index))
        return True

    def _attach_course_session(
        self, course_id: str, stage_index: int, session_id: str, document_title: str | None
    ) -> None:
        course = self.get_course(course_id)
        stage = self._find_stage(course, stage_index)
        if stage.get("kind") != "week":
            raise WebStudyError("이 단계는 PDF 업로드를 지원하지 않습니다.")
        position = course["stages"].index(stage)
        if position > 0 and not course["stages"][position - 1]["completed"]:
            raise WebStudyError("이전 학습 단계를 먼저 완료해야 합니다.")
        stage["session_id"] = session_id
        stage["document_title"] = document_title
        stage["completed"] = False
        self._session_store.save_course(course)

    def _complete_course_stage(self, session_id: str) -> None:
        link = self._course_links.get(session_id)
        if link is None or self._session_store is None:
            return
        course_id, stage_index = link
        course = self.get_course(course_id)
        stage = self._find_stage(course, stage_index)
        if stage["session_id"] == session_id:
            stage["completed"] = True
            self._session_store.save_course(course)

    def get_course_summary(self, course_id: str) -> dict:
        course = self.get_course(course_id)
        stages = course.get("stages", [])
        completed = sum(1 for stage in stages if stage.get("completed"))
        total = len(stages)
        is_complete = bool(stages) and stages[-1].get("kind") == "checkpoint" and stages[-1].get("completed", False)

        total_seconds = 0.0
        strong_titles: set[str] = set()
        for stage in stages:
            session_id = stage.get("session_id")
            if not session_id:
                continue
            stored = self._session_store.load(session_id)
            if stored is None:
                continue
            session = stored.session
            if session.started_at and session.ended_at:
                total_seconds += (session.ended_at - session.started_at).total_seconds()
            if session.summary:
                strong_titles.update(session.summary.strong_concepts)

        return {
            "course_id": course_id,
            "is_complete": is_complete,
            "progress": {"completed": completed, "total": total},
            "total_study_seconds": round(total_seconds),
            "concepts_understood_count": len(strong_titles),
        }

    def _concept_review_snapshot(self, session_id: str, session: StudySession) -> dict:
        index = self._current_indexes.get(session_id, 0)
        concept = session.concepts[index] if index < len(session.concepts) else None
        current_prompt = None
        if concept is not None:
            current_prompt = {
                "question_id": f"concept_prompt_{concept.concept_id}",
                "concept_id": concept.concept_id,
                "question_type": "explanation",
                "question": concept.title,
                "required_points": [], "source_pages": concept.source_pages,
            }
        return {
            "session": session.model_dump(mode="json"),
            "session_mode": "concept_review",
            "current_question": current_prompt,
            "current_index": min(index, len(session.concepts)),
            "total_questions": len(session.concepts),
            "last_answer": session.concept_answers[-1].model_dump(mode="json") if session.concept_answers else None,
            "completed": session.ended_at is not None,
        }

class _DocumentRef:
    def __init__(self, document_id: str, title: str | None = None) -> None:
        self.document_id = document_id
        self.title = title or "web-session"
