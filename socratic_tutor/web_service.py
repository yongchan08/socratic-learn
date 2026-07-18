from __future__ import annotations

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
    generate_or_load_questions,
    load_generated_learning_materials,
    parse_or_load_pdf,
    save_concept_review_report,
)
from .session import evaluate_concept_answers, generate_session_summary
from .storage import save_json
from .session_store import PostgresSessionStore, StoredWebSession
from .utils import truncate_markdown, utc_now


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

    def create_course(self, title: str | None = None) -> dict:
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용하려면 DATABASE_URL 설정이 필요합니다.")
        course = {
            "course_id": f"course_{uuid.uuid4().hex[:12]}",
            "title": title.strip() if title and title.strip() else "새 학습 로드맵",
            "stages": [
                {"stage_index": index, "title": f"{index}단계 강의", "session_id": None,
                 "document_title": None, "completed": False}
                for index in range(1, 4)
            ],
            "final_review_session_id": None,
            "created_at": utc_now().isoformat(),
        }
        self._session_store.save_course(course)
        return course

    def list_courses(self) -> list[dict]:
        if self._session_store is None:
            raise WebStudyError("학습 로드맵을 사용하려면 DATABASE_URL 설정이 필요합니다.")
        return self._session_store.list_courses()

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
        return course

    def create_course_review(self, course_id: str) -> StudySession:
        course = self.get_course(course_id)
        if not all(stage["completed"] for stage in course["stages"]):
            raise WebStudyError("모든 소크라테스 학습 단계를 완료해야 개념 리포트를 시작할 수 있습니다.")
        stored_stages = [self._session_store.load(stage["session_id"]) for stage in course["stages"]]
        if any(stored is None for stored in stored_stages):
            raise WebStudyError("단계별 학습 세션을 불러오지 못했습니다.")

        concepts: list = []
        questions: list[Question] = []
        for stage, stored in zip(course["stages"], stored_stages):
            prefix = f"stage_{stage['stage_index']}_"
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
            session_id=f"course_review_{utc_now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
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
            self._document_titles[session.session_id] = course["title"]
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
        if self._session_modes.get(session_id) == "concept_review":
            return self._answer_concept_review(session_id, answer_text)
        question = self.current_question(session_id)
        if question is None:
            return self.finish(session_id)

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
            self.finish(session_id)
        else:
            self._persist(session_id)
        return session

    def skip(self, session_id: str) -> StudySession:
        if self._session_modes.get(session_id) == "concept_review":
            return self._answer_concept_review(session_id, "/skip")
        question = self.current_question(session_id)
        if question is None:
            return self.finish(session_id)
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
            self.finish(session_id)
        else:
            self._persist(session_id)
        return session

    def finish(self, session_id: str) -> StudySession:
        session = self.get_session(session_id)
        if session.ended_at is None:
            config = self._configs[session_id]
            llm_client = self._llm_clients.get(session_id)
            if self._session_modes.get(session_id) == "concept_review" and llm_client is not None:
                evaluate_concept_answers(session, llm_client)
            generate_session_summary(session, llm_client)
            session.ended_at = utc_now()
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
            self._complete_course_stage(session_id)
        return session

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
        index = self._current_indexes.get(session_id, 0)
        if index >= len(session.concepts):
            return self.finish(session_id)
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
            self.finish(session_id)
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
        if stage_index < 1 or stage_index > len(course["stages"]):
            raise WebStudyError("올바르지 않은 학습 단계입니다.")
        if stage_index > 1 and not course["stages"][stage_index - 2]["completed"]:
            raise WebStudyError("이전 학습 단계를 먼저 완료해야 합니다.")
        stage = course["stages"][stage_index - 1]
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
        stage = course["stages"][stage_index - 1]
        if stage["session_id"] == session_id:
            stage["completed"] = True
            self._session_store.save_course(course)

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
