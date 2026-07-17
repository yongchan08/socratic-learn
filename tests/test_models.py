import pytest
from pydantic import ValidationError

from socratic_tutor.models import AnswerEvaluation, Concept, Question, RequiredPoint


def _point(text: str, index: int = 1) -> RequiredPoint:
    return RequiredPoint(
        point_id=f"rp_{index:03d}", text=text, gentle_hint="Think about it.", direct_hint="Explain it directly."
    )


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
            required_points=[_point("generalization")],
        )


def test_question_model_ignores_unrelated_extra_fields():
    question = Question.model_validate(
        {
            "question_id": "q_001_001",
            "concept_id": "concept_001",
            "question_type": "explanation",
            "question": "Explain overfitting.",
            "required_points": [{
                "point_id": "rp_001", "text": "generalization",
                "gentle_hint": "Think about test data.", "direct_hint": "Compare the results.",
            }],
            "optional_points": ["legacy optional"],
            "common_missing_points": ["legacy common missing"],
            "source_pages": [1],
        }
    )

    assert question.required_point_texts == ["generalization"]
    assert not hasattr(question, "optional_points")
    assert not hasattr(question, "common_missing_points")
    assert question.required_points[0].gentle_hint == "Think about test data."


def test_question_model_rejects_out_of_order_required_point_id():
    with pytest.raises(ValidationError):
        Question.model_validate(
            {
                "question_id": "q_001_001",
                "concept_id": "concept_001",
                "question_type": "explanation",
                "question": "Explain overfitting.",
                "required_points": [{
                    "point_id": "rp_002", "text": "generalization",
                    "gentle_hint": "Think about unseen data.",
                    "direct_hint": "Compare training and test performance.",
                }],
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
