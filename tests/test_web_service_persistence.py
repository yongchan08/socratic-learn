from datetime import datetime, timezone

from socratic_tutor.config import AppConfig
from socratic_tutor.models import AnswerEvaluation, Concept, Question, RequiredPoint, StudentAnswer, StudySession
from socratic_tutor.session_store import StoredWebSession
from socratic_tutor.web_service import WebStudyManager


def _session() -> StudySession:
    return StudySession(
        session_id="session_restore_test",
        document_id="doc_test",
        concepts=[Concept(
            concept_id="concept_001",
            title="캐시",
            summary="데이터를 임시 저장한다.",
            importance="성능에 중요하다.",
            source_pages=[1],
        )],
        questions=[Question(
            question_id="q_001_001",
            concept_id="concept_001",
            question_type="explanation",
            question="캐시를 설명하세요.",
            required_points=[RequiredPoint(
                point_id="rp_001",
                text="데이터 임시 저장",
                gentle_hint="저장 위치를 생각해보세요.",
                direct_hint="임시 저장을 설명하세요.",
            )],
        )],
        started_at=datetime.now(timezone.utc),
    )


class FakeStore:
    def __init__(self, stored=None):
        self.stored = {stored.session.session_id: stored} if stored else {}
        self.saved = []
        self.courses = {}

    def save(self, stored):
        self.saved.append(stored)
        self.stored[stored.session.session_id] = stored

    def load(self, session_id):
        return self.stored.get(session_id)

    def save_course(self, course):
        self.courses[course["course_id"]] = course

    def load_course(self, course_id):
        return self.courses.get(course_id)

    def list_courses(self):
        return list(reversed(list(self.courses.values())))

    def delete_course(self, course_id):
        course = self.courses.pop(course_id, None)
        if course is None:
            return None
        session_ids = [stage["session_id"] for stage in course["stages"] if stage["session_id"]]
        if course["final_review_session_id"]:
            session_ids.append(course["final_review_session_id"])
        for session_id in session_ids:
            self.stored.pop(session_id, None)
        return session_ids


def test_persist_saves_session_progress_and_non_secret_config():
    store = FakeStore()
    manager = WebStudyManager(session_store=store)
    session = _session()
    manager._sessions[session.session_id] = session
    manager._configs[session.session_id] = AppConfig(api_key="secret", model="test-model")
    manager._current_indexes[session.session_id] = 1
    manager._session_modes[session.session_id] = "study"
    manager._document_titles[session.session_id] = "Lecture"

    manager._persist(session.session_id)

    saved = store.saved[0]
    assert saved.current_index == 1
    assert saved.config["model"] == "test-model"
    assert "api_key" not in saved.config


def test_get_session_restores_missing_in_memory_session(monkeypatch):
    session = _session()
    stored = StoredWebSession(
        session=session,
        current_index=0,
        session_mode="study",
        document_title="Lecture",
        config={"model": "test-model", "output_dir": "outputs", "cache_dir": "cache"},
    )
    monkeypatch.setenv("OPENAI_API_KEY", "restored-key")
    manager = WebStudyManager(session_store=FakeStore(stored))

    restored = manager.get_session(session.session_id)

    assert restored == session
    assert manager.current_question(session.session_id).question_id == "q_001_001"
    assert manager._configs[session.session_id].api_key == "restored-key"


def test_course_does_not_complete_stage_when_session_ends_early(monkeypatch):
    store = FakeStore()
    manager = WebStudyManager(session_store=store)
    course = manager.create_course()
    session = _session()
    manager._sessions[session.session_id] = session
    manager._configs[session.session_id] = AppConfig(api_key="test-key")
    manager._llm_clients[session.session_id] = None
    manager._current_indexes[session.session_id] = 0
    manager._session_modes[session.session_id] = "study"
    manager._document_titles[session.session_id] = "첫 강의"
    manager._course_links[session.session_id] = (course["course_id"], 1)
    manager._attach_course_session(course["course_id"], 1, session.session_id, "첫 강의")
    monkeypatch.setattr("socratic_tutor.web_service.generate_session_summary", lambda session, client: None)

    manager.finish(session.session_id)

    saved_course = manager.get_course(course["course_id"])
    assert saved_course["stages"][0]["completed"] is False
    assert saved_course["stages"][0]["document_title"] == "첫 강의"
    assert session.completion_status == "ended_early"
    assert session.end_reason == "user_quit"


def test_course_completes_stage_after_all_questions_are_resolved(monkeypatch):
    store = FakeStore()
    manager = WebStudyManager(session_store=store)
    course = manager.create_course()
    session = _session()
    session.answers.append(StudentAnswer(
        answer_id="ans_001",
        question_id="q_001_001",
        attempt_number=1,
        answer_text="/skip",
        evaluation=AnswerEvaluation(
            score=0, status="insufficient", feedback_to_student="건너뜀", next_action="next_question"
        ),
        created_at=datetime.now(timezone.utc),
    ))
    manager._sessions[session.session_id] = session
    manager._configs[session.session_id] = AppConfig(api_key="test-key")
    manager._llm_clients[session.session_id] = None
    manager._current_indexes[session.session_id] = 1
    manager._session_modes[session.session_id] = "study"
    manager._document_titles[session.session_id] = "첫 강의"
    manager._course_links[session.session_id] = (course["course_id"], 1)
    manager._attach_course_session(course["course_id"], 1, session.session_id, "첫 강의")
    monkeypatch.setattr("socratic_tutor.web_service.generate_session_summary", lambda session, client: None)

    manager.finish(session.session_id, end_reason="all_answered")

    assert manager.get_course(course["course_id"])["stages"][0]["completed"] is True
    assert session.completion_status == "completed"
    assert session.end_reason == "all_answered"


def test_typed_quit_finishes_without_evaluating_or_storing_answer(monkeypatch):
    manager = WebStudyManager(session_store=FakeStore())
    session = _session()
    manager._sessions[session.session_id] = session
    manager._configs[session.session_id] = AppConfig(api_key="test-key")
    manager._llm_clients[session.session_id] = object()
    manager._current_indexes[session.session_id] = 0
    manager._session_modes[session.session_id] = "study"
    manager._document_titles[session.session_id] = "강의"
    monkeypatch.setattr("socratic_tutor.web_service.generate_session_summary", lambda session, client: None)
    monkeypatch.setattr(
        "socratic_tutor.web_service.evaluate_answer",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM evaluation must not run")),
    )

    manager.answer(session.session_id, "  /QUIT  ")

    assert session.answers == []
    assert session.completion_status == "ended_early"
    assert session.end_reason == "user_quit"


def test_typed_skip_uses_fixed_skip_evaluation_without_llm(monkeypatch):
    manager = WebStudyManager(session_store=FakeStore())
    session = _session()
    manager._sessions[session.session_id] = session
    manager._configs[session.session_id] = AppConfig(api_key="test-key")
    manager._llm_clients[session.session_id] = object()
    manager._current_indexes[session.session_id] = 0
    manager._session_modes[session.session_id] = "study"
    manager._document_titles[session.session_id] = "강의"
    monkeypatch.setattr("socratic_tutor.web_service.generate_session_summary", lambda session, client: None)
    monkeypatch.setattr(
        "socratic_tutor.web_service.evaluate_answer",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM evaluation must not run")),
    )

    manager.answer(session.session_id, " /SKIP ")

    assert len(session.answers) == 1
    assert session.answers[0].answer_text == "/skip"
    assert session.answers[0].evaluation.missing_points == ["데이터 임시 저장"]
    assert session.completion_status == "completed"


def test_course_review_namespaces_concepts_and_questions(monkeypatch):
    store = FakeStore()
    manager = WebStudyManager(session_store=store)
    course = manager.create_course()
    for index, stage in enumerate(course["stages"], start=1):
        session = _session().model_copy(update={
            "session_id": f"session_stage_{index}",
            "document_id": f"doc_{index}",
            "ended_at": datetime.now(timezone.utc),
        })
        stored = StoredWebSession(
            session=session,
            current_index=1,
            session_mode="study",
            document_title=f"강의 {index}",
            config={"model": "test-model"},
        )
        store.stored[session.session_id] = stored
        stage["session_id"] = session.session_id
        stage["completed"] = True
    store.save_course(course)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    review = manager.create_course_review(course["course_id"])

    assert [concept.concept_id for concept in review.concepts] == [
        "stage_1_concept_001", "stage_2_concept_001", "stage_3_concept_001"
    ]
    assert [question.question_id for question in review.questions] == [
        "stage_1_q_001_001", "stage_2_q_001_001", "stage_3_q_001_001"
    ]
    assert review.questions[1].concept_id == "stage_2_concept_001"


def test_lists_multiple_courses_and_preserves_titles():
    manager = WebStudyManager(session_store=FakeStore())

    first = manager.create_course("운영체제")
    second = manager.create_course("데이터베이스")

    assert [course["title"] for course in manager.list_courses()] == ["데이터베이스", "운영체제"]
    assert first["course_id"] != second["course_id"]


def test_delete_course_removes_linked_sessions_from_store_and_memory():
    store = FakeStore()
    manager = WebStudyManager(session_store=store)
    course = manager.create_course("삭제할 과정")
    session = _session()
    stored = StoredWebSession(
        session=session,
        current_index=0,
        session_mode="study",
        document_title="강의",
        config={"model": "test-model"},
    )
    store.stored[session.session_id] = stored
    manager._sessions[session.session_id] = session
    course["stages"][0]["session_id"] = session.session_id
    store.save_course(course)

    manager.delete_course(course["course_id"])

    assert manager.list_courses() == []
    assert store.load(session.session_id) is None
    assert session.session_id not in manager._sessions
