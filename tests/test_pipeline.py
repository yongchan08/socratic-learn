from concurrent.futures import Future
from types import SimpleNamespace

import pytest

from socratic_tutor.config import AppConfig
from socratic_tutor.models import Concept, Question, RequiredPoint
from socratic_tutor.pipeline import (
    QuestionGenerationTimeoutError,
    _assign_required_point_ids,
    _collect_question_results,
    _validate_question_mix,
    document_output_dir,
    load_generated_learning_materials,
)
from socratic_tutor.storage import save_json


def test_collect_question_results_times_out_and_cancels_pending_future():
    pending = Future()

    with pytest.raises(QuestionGenerationTimeoutError, match="제한 시간"):
        _collect_question_results({pending: 1}, total=1, on_progress=None, timeout_seconds=0.001)

    assert pending.cancelled()


def _question(question_type: str, index: int) -> Question:
    return Question(
        question_id=f"q_001_{index:03d}",
        concept_id="concept_001",
        question_type=question_type,
        question="Question",
        required_points=[RequiredPoint(
            point_id="rp_001", text="Point", gentle_hint="Think.", direct_hint="Explain."
        )],
    )


@pytest.mark.parametrize("second_type", ["comparison", "application"])
def test_validate_question_mix_accepts_explanation_then_transfer(second_type):
    _validate_question_mix([_question("explanation", 1), _question(second_type, 2)])


def test_validate_question_mix_rejects_two_explanation_questions():
    with pytest.raises(ValueError, match="one explanation"):
        _validate_question_mix([_question("explanation", 1), _question("explanation", 2)])


def test_assign_required_point_ids_replaces_unreliable_llm_ids():
    question_data = {
        "required_points": [
            {"point_id": "point-7", "text": "A"},
            {"point_id": "rp_009", "text": "B"},
        ]
    }

    _assign_required_point_ids(question_data)

    assert [point["point_id"] for point in question_data["required_points"]] == ["rp_001", "rp_002"]


def test_concept_review_loads_materials_created_by_study_feature(tmp_path):
    config = AppConfig(output_dir=tmp_path)
    document = SimpleNamespace(document_id="doc_test", title="Lecture")
    output_dir = document_output_dir(config, document)
    concept = Concept(
        concept_id="concept_001", title="Caching", summary="Summary", importance="Important", source_pages=[1]
    )
    questions = [_question("explanation", 1), _question("application", 2)]
    save_json([concept], output_dir / "concepts_doc_test.json")
    save_json(questions, output_dir / "questions_doc_test.json")

    loaded_concepts, loaded_questions = load_generated_learning_materials(document, config)

    assert loaded_concepts == [concept]
    assert loaded_questions == questions


def test_concept_review_requires_study_feature_outputs(tmp_path):
    config = AppConfig(output_dir=tmp_path)
    document = SimpleNamespace(document_id="doc_test", title="Lecture")

    with pytest.raises(FileNotFoundError, match="먼저 같은 PDF로 start"):
        load_generated_learning_materials(document, config)


class FakeMaterialStore:
    def __init__(self, concepts=None, questions=None):
        self.concepts = concepts
        self.questions = questions

    def load_concepts(self, file_hash, difficulty, output_language):
        assert (file_hash, difficulty, output_language) == ("hash", "normal", "ko")
        return self.concepts

    def load_questions(self, file_hash, difficulty, output_language):
        assert (file_hash, difficulty, output_language) == ("hash", "normal", "ko")
        return self.questions


def test_concept_review_loads_materials_from_database_store_without_output_files(tmp_path):
    config = AppConfig(output_dir=tmp_path)
    document = SimpleNamespace(document_id="doc_test", title="Lecture")
    concept = Concept(
        concept_id="concept_001", title="Caching", summary="Summary", importance="Important", source_pages=[1]
    )
    questions = [_question("explanation", 1), _question("application", 2)]

    loaded_concepts, loaded_questions = load_generated_learning_materials(
        document,
        config,
        file_hash="hash",
        material_store=FakeMaterialStore([concept], questions),
    )

    assert loaded_concepts == [concept]
    assert loaded_questions == questions
    assert list(tmp_path.iterdir()) == []


def test_concept_review_requires_database_materials_when_store_is_configured(tmp_path):
    config = AppConfig(output_dir=tmp_path)
    document = SimpleNamespace(document_id="doc_test", title="Lecture")

    with pytest.raises(FileNotFoundError, match="데이터베이스"):
        load_generated_learning_materials(
            document,
            config,
            file_hash="hash",
            material_store=FakeMaterialStore(),
        )
