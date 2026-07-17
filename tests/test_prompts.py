from socratic_tutor.models import Concept
from socratic_tutor.models import Question, RequiredPoint
from socratic_tutor.prompts import (
    build_answer_evaluation_prompt,
    build_concept_extraction_prompt,
    build_question_generation_prompt,
)


def _point(text: str, index: int = 1) -> RequiredPoint:
    return RequiredPoint(
        point_id=f"rp_{index:03d}", text=text, gentle_hint="Think about it.", direct_hint="Explain it directly."
    )


def test_question_generation_prompt_avoids_compound_questions():
    concept = Concept(
        concept_id="concept_001",
        title="Multimodality",
        summary="Models process multiple modalities.",
        importance="Important for grounding.",
        source_pages=[1],
    )

    _, user_prompt = build_question_generation_prompt(
        concept=concept,
        document_excerpt="Visual context can add meaning.",
    )

    assert "Each question should ask one main thing only" in user_prompt
    assert "Avoid compound questions" in user_prompt


def test_question_generation_prompt_requires_explanation_then_transfer_question():
    concept = Concept(
        concept_id="concept_001",
        title="Overfitting",
        summary="The model fits training data too closely.",
        importance="It harms generalization.",
        source_pages=[1],
    )

    _, user_prompt = build_question_generation_prompt(
        concept=concept,
        document_excerpt="Training and test errors can diverge.",
    )

    assert 'The first question_type must be "explanation"' in user_prompt
    assert 'The second question_type must be either "comparison" or "application"' in user_prompt
    assert "especially its summary and core principle" in user_prompt


def test_concept_extraction_prompt_uses_current_schema():
    _, user_prompt = build_concept_extraction_prompt(
        markdown="Training error and test error can diverge.",
        difficulty="normal",
    )

    json_shape = user_prompt.split("Rules:", maxsplit=1)[0]
    assert '"importance"' in json_shape
    assert '"evidence_from_material"' in json_shape
    assert "up to a maximum of 5" in user_prompt
    assert "Do not add marginal concepts just to reach a particular count" in user_prompt


def test_question_generation_prompt_uses_korean_output_language():
    concept = Concept(
        concept_id="concept_001",
        title="Multimodality",
        summary="Models process multiple modalities.",
        importance="Important for grounding.",
        source_pages=[1],
    )

    _, user_prompt = build_question_generation_prompt(
        concept=concept,
        document_excerpt="Visual context can add meaning.",
        output_language="ko",
    )

    assert 'Korean (output_language is "ko")' in user_prompt
    assert "Generate all user-facing fields in Korean if output_language is \"ko\"" in user_prompt
    assert "Even if the lecture material is in English, questions must be written in the output language" in user_prompt


def test_answer_evaluation_prompt_accepts_korean_answers():
    question = Question(
        question_id="q_001_001",
        concept_id="concept_001",
        question_type="explanation",
        question="사람이 언어를 이해할 때 단어만으로 충분할까요?",
        required_points=[_point("언어는 맥락과 함께 이해된다")],
    )

    _, user_prompt = build_answer_evaluation_prompt(
        question=question,
        student_answer="시각적 맥락은 추가 정보를 줘요.",
        attempt_number=1,
        output_language="ko",
    )

    assert "The student may answer in Korean, English, or a mixture of both" in user_prompt
    assert "Evaluate the answer semantically, not by exact wording" in user_prompt
    assert "If the student expresses a required point in simpler, shorter, or slightly different words" in user_prompt
    assert "오랜만에 사용해도 시스템이 쉽게 기억나고 학습 부담이 적다" in user_prompt
    assert "Do not penalize the student for answering in Korean" in user_prompt


def test_question_generation_prompt_does_not_generate_optional_or_common_missing_points():
    concept = Concept(
        concept_id="concept_001",
        title="Multimodality",
        summary="Models process multiple modalities.",
        importance="Important for grounding.",
        source_pages=[1],
    )

    _, user_prompt = build_question_generation_prompt(
        concept=concept,
        document_excerpt="Visual context can add meaning.",
    )

    assert '"optional_points"' not in user_prompt
    assert '"common_missing_points"' not in user_prompt
    assert "Do not generate optional_points" in user_prompt
    assert "Do not generate common_missing_points" in user_prompt
    assert '"gentle_hint"' in user_prompt
    assert "Each required point object must contain its criterion text and both linked hints" in user_prompt


def test_question_generation_prompt_uses_concept_evidence():
    concept = Concept(
        concept_id="concept_001",
        title="Multimodality",
        summary="Models process multiple modalities.",
        importance="Important for grounding.",
        source_pages=[1],
        evidence_from_material=["Visual context can add meaning."],
    )

    _, user_prompt = build_question_generation_prompt(
        concept=concept,
        document_excerpt="Visual context can add meaning.",
    )

    assert "Visual context can add meaning." in user_prompt
    assert "Base questions on the concept summary, importance, evidence_from_material, source_pages" in user_prompt


def test_answer_evaluation_prompt_uses_required_points_only():
    question = Question(
        question_id="q_001_001",
        concept_id="concept_001",
        question_type="explanation",
        question="Explain overfitting.",
        required_points=[_point("generalization")],
    )

    _, user_prompt = build_answer_evaluation_prompt(
        question=question,
        student_answer="It hurts generalization.",
        attempt_number=1,
    )

    assert "Use required_points as the only grading criteria" in user_prompt
    assert "Do not use optional_points or common_missing_points to decide score, status, or next_action" in user_prompt
    assert "missing_points must include only unmet required_points" in user_prompt


def test_answer_evaluation_prompt_separates_feedback_note_and_followup():
    question = Question(
        question_id="q_001_001",
        concept_id="concept_001",
        question_type="explanation",
        question="Explain learnability.",
        required_points=[_point("easy to learn"), _point("why it matters", 2)],
    )

    _, user_prompt = build_answer_evaluation_prompt(
        question=question,
        student_answer="쉽게 배울 수 있는 정도입니다.",
        attempt_number=1,
    )

    assert "feedback_to_student must diagnose the current answer only" in user_prompt
    assert "Use improvement_note only when next_action is next_question" in user_prompt
    assert "Use socratic_follow_up only when next_action is ask_followup" in user_prompt
    assert "improvement_note must not repeat feedback_to_student" in user_prompt
    assert "feedback_to_student must diagnose the answer, not teach the missing required point directly" in user_prompt
    assert "Do not reveal the exact missing required point in feedback_to_student before the final attempt" in user_prompt
    assert "Put the reasoning path toward the missing idea in socratic_follow_up" in user_prompt
    assert "The feedback and the follow-up must not repeat the same sentence" in user_prompt
    assert "If reveal_missing_points is false, do not include missing_points verbatim or near-verbatim" in user_prompt


def test_answer_evaluation_prompt_documents_three_attempt_policy():
    question = Question(
        question_id="q_001_001",
        concept_id="concept_001",
        question_type="explanation",
        question="Explain memorability.",
        required_points=[_point("easy to remember after a long time")],
    )

    _, user_prompt = build_answer_evaluation_prompt(
        question=question,
        student_answer="It is easy to remember.",
        attempt_number=2,
    )

    assert "The maximum number of attempts per question is 3" in user_prompt
    assert "On attempt 2" in user_prompt
    assert "On attempt 3 or higher" in user_prompt
