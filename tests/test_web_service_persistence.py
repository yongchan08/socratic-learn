from datetime import datetime, timezone

from socratic_tutor.config import AppConfig
from socratic_tutor.models import Concept, Question, RequiredPoint, StudySession
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
        self.stored = stored
        self.saved = []

    def save(self, stored):
        self.saved.append(stored)
        self.stored = stored

    def load(self, session_id):
        if self.stored and self.stored.session.session_id == session_id:
            return self.stored
        return None


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
