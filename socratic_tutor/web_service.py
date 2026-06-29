from __future__ import annotations

import uuid
from pathlib import Path
from threading import Lock

from .config import AppConfig, load_app_config
from .evaluator import MAX_ATTEMPTS_PER_QUESTION, evaluate_answer
from .llm_client import LLMClient
from .models import AnswerEvaluation, Question, StudentAnswer, StudySession
from .pipeline import (
    document_output_dir,
    extract_or_load_concepts,
    generate_or_load_questions,
    parse_or_load_pdf,
)
from .session import generate_session_summary
from .storage import save_json
from .utils import truncate_markdown, utc_now


class WebStudyError(ValueError):
    pass


class WebStudyManager:
    def __init__(self) -> None:
        self._sessions: dict[str, StudySession] = {}
        self._configs: dict[str, AppConfig] = {}
        self._llm_clients: dict[str, LLMClient] = {}
        self._current_indexes: dict[str, int] = {}
        self._lock = Lock()

    def create_session(
        self,
        pdf_path: str | Path,
        subject: str | None = None,
        difficulty: str = "normal",
        output_language: str = "ko",
        max_concepts: int = 7,
        questions_per_concept: int = 3,
        model: str | None = None,
        output_dir: str = "./outputs",
        cache_dir: str = "./cache",
        skip_cache: bool = False,
    ) -> StudySession:
        config = load_app_config(
            pdf=str(pdf_path),
            subject=subject or None,
            difficulty=difficulty,
            output_language=output_language,
            max_concepts=max_concepts,
            questions_per_concept=questions_per_concept,
            model=model or None,
            output_dir=output_dir,
            cache_dir=cache_dir,
            skip_cache=skip_cache,
        )
        if not config.api_key:
            raise WebStudyError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

        llm_client = LLMClient(model=config.model, api_key=config.api_key)
        parsed_doc, file_hash = parse_or_load_pdf(config)
        markdown_for_llm, _ = truncate_markdown(parsed_doc.markdown)
        concepts = extract_or_load_concepts(parsed_doc, markdown_for_llm, file_hash, config, llm_client)
        if not concepts:
            raise WebStudyError("핵심 개념을 추출하지 못했습니다.")
        questions = generate_or_load_questions(parsed_doc, concepts, markdown_for_llm, file_hash, config, llm_client)
        if not questions:
            raise WebStudyError("질문을 생성하지 못했습니다.")

        session = StudySession(
            session_id=f"session_{utc_now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            document_id=parsed_doc.document_id,
            subject=config.subject,
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
        return session

    def get_session(self, session_id: str) -> StudySession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
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
        question = self.current_question(session_id)
        if question is None:
            return self.finish(session_id)

        session = self.get_session(session_id)
        attempt_number = self._attempt_number(session, question)
        if attempt_number > MAX_ATTEMPTS_PER_QUESTION:
            self._advance(session_id)
            return session

        config = self._configs[session_id]
        llm_client = self._llm_clients[session_id]
        evaluation = evaluate_answer(
            llm_client,
            question,
            answer_text,
            attempt_number,
            output_language=config.output_language,
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
        return session

    def skip(self, session_id: str) -> StudySession:
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
                    matched_points=[],
                    missing_points=question.required_points,
                    misconceptions=[],
                    score=0,
                    status="insufficient",
                    feedback_to_student="사용자가 이 질문을 건너뛰었습니다.",
                    next_action="next_question",
                ),
                created_at=utc_now(),
            )
        )
        self._advance(session_id)
        if self.current_question(session_id) is None:
            self.finish(session_id)
        return session

    def finish(self, session_id: str) -> StudySession:
        session = self.get_session(session_id)
        if session.ended_at is None:
            config = self._configs[session_id]
            llm_client = self._llm_clients.get(session_id)
            session.ended_at = utc_now()
            generate_session_summary(session, llm_client)
            save_json(session, document_output_dir(config, _DocumentRef(session.document_id)) / f"{session.session_id}.json")
        return session

    def snapshot(self, session_id: str) -> dict:
        session = self.get_session(session_id)
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


class _DocumentRef:
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        self.title = "web-session"
