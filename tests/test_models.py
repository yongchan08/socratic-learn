import pytest
from pydantic import ValidationError

from socratic_tutor.models import AnswerEvaluation, Concept, Question


def test_concept_model_validates_required_fields():
    concept = Concept(
        concept_id="concept_001",
        title="Overfitting",
        summary="Model fits training data too closely.",
        importance="Central to generalization.",
        source_pages=[1],
    )

    assert concept.title == "Overfitting"


def test_question_model_validates_allowed_question_types():
    with pytest.raises(ValidationError):
        Question(
            question_id="q_001_001",
            concept_id="concept_001",
            question_type="multiple_choice",
            question="What is overfitting?",
            required_points=["generalization"],
        )


def test_question_model_ignores_legacy_optional_fields():
    question = Question.model_validate(
        {
            "question_id": "q_001_001",
            "concept_id": "concept_001",
            "question_type": "explanation",
            "question": "Explain overfitting.",
            "required_points": ["generalization"],
            "optional_points": ["legacy optional"],
            "common_missing_points": ["legacy common missing"],
            "hints": ["Think about test data."],
            "source_pages": [1],
        }
    )

    assert question.required_points == ["generalization"]
    assert not hasattr(question, "optional_points")
    assert not hasattr(question, "common_missing_points")
    assert question.point_hints[0].required_point == "generalization"
    assert question.point_hints[0].gentle == "Think about test data."


def test_question_model_rejects_point_hint_linked_to_different_required_point():
    with pytest.raises(ValidationError):
        Question.model_validate(
            {
                "question_id": "q_001_001",
                "concept_id": "concept_001",
                "question_type": "explanation",
                "question": "Explain overfitting.",
                "required_points": ["generalization"],
                "point_hints": [
                    {
                        "point_id": "rp_001",
                        "required_point": "training speed",
                        "gentle": "Think about unseen data.",
                        "direct": "Compare training and test performance.",
                    }
                ],
            }
        )


def test_answer_evaluation_model_validates_allowed_statuses():
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            matched_points=[],
            missing_points=[],
            misconceptions=[],
            score=0.5,
            status="almost",
            feedback_to_student="Try again.",
            next_action="ask_followup",
        )


def test_answer_evaluation_model_defaults():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["missing point"],
        misconceptions=[],
        score=0.4,
        status="insufficient",
        feedback_to_student="Try again.",
        next_action="ask_followup",
    )

    assert evaluation.socratic_follow_up is None
    assert evaluation.improvement_note is None
    assert evaluation.reveal_missing_points is False
