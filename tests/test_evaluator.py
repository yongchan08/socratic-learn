from socratic_tutor.evaluator import evaluate_answer, normalize_evaluation
from socratic_tutor.models import AnswerEvaluation, Question, RequiredPoint


class FakeLLMClient:
    def __init__(self, payload):
        self.payload = payload

    def complete_json(self, system_prompt: str, user_prompt: str, json_repair_retries: int = 1) -> dict:
        return self.payload


def test_score_normalization_clamps_below_zero_to_zero():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["x"],
        misconceptions=[],
        score=-1,
        status="insufficient",
        feedback_to_student="Try again.",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(evaluation)

    assert normalized.score == 0
    assert normalized.status == "insufficient"


def test_score_normalization_clamps_above_one_to_one():
    evaluation = AnswerEvaluation(
        matched_points=["x"],
        missing_points=[],
        misconceptions=[],
        score=2,
        status="sufficient",
        feedback_to_student="Good.",
        next_action="next_question",
    )

    normalized = normalize_evaluation(evaluation)

    assert normalized.score == 1
    assert normalized.status == "sufficient"


def test_misconception_forces_status_misconception():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=[],
        misconceptions=["Incorrect idea"],
        score=0.9,
        status="sufficient",
        feedback_to_student="Check this.",
        next_action="next_question",
    )

    normalized = normalize_evaluation(evaluation)

    assert normalized.status == "misconception"
    assert normalized.next_action == "ask_followup"


def test_no_missing_points_forces_sufficient_next_question():
    evaluation = AnswerEvaluation(
        matched_points=["required point"],
        missing_points=[],
        misconceptions=[],
        score=0.3,
        status="insufficient",
        feedback_to_student="Good.",
        socratic_follow_up="Should not be shown.",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=["required point"],
        student_answer="required point",
    )

    assert normalized.status == "sufficient"
    assert normalized.next_action == "next_question"
    assert normalized.socratic_follow_up is None
    assert normalized.improvement_note is None
    assert normalized.score >= 0.75


def test_sufficient_answer_clears_hint_and_gap_feedback():
    evaluation = AnswerEvaluation(
        matched_points=["required point"],
        missing_points=["required point"],
        misconceptions=[],
        score=0.2,
        status="insufficient",
        feedback_to_student="핵심은 맞지만 아직 부족한 점이 있어요.",
        hint="required point를 다시 생각해보세요.",
        improvement_note="더 보완하세요.",
        socratic_follow_up="무엇이 부족할까요?",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=["required point"],
        student_answer="required point",
    )

    assert normalized.status == "sufficient"
    assert normalized.score == 1
    assert normalized.hint is None
    assert normalized.socratic_follow_up is None
    assert normalized.improvement_note is None
    assert "부족" not in normalized.feedback_to_student
    assert "보완" not in normalized.feedback_to_student


def test_missing_required_point_keeps_followup_even_when_partially_sufficient():
    evaluation = AnswerEvaluation(
        matched_points=["required point"],
        missing_points=["minor required point"],
        misconceptions=[],
        score=0.6,
        status="partially_sufficient",
        feedback_to_student="방향은 맞아요.",
        improvement_note="중요성을 연결하면 더 좋아요.",
        socratic_follow_up="이 질문은 출력되면 안 됩니다.",
        next_action="next_question",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=["required point", "minor required point"],
        student_answer="required point",
    )

    assert normalized.status == "partially_sufficient"
    assert normalized.next_action == "ask_followup"
    assert normalized.reveal_missing_points is False
    assert normalized.improvement_note is None


def test_ask_followup_clears_improvement_note():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.4,
        status="insufficient",
        feedback_to_student="조금 부족해요.",
        improvement_note="이 문장은 출력되면 안 됩니다.",
        socratic_follow_up="어떤 점을 더 생각해볼 수 있을까요?",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(evaluation, attempt_number=1)

    assert normalized.next_action == "ask_followup"
    assert normalized.improvement_note is None
    assert normalized.socratic_follow_up == "어떤 점을 더 생각해볼 수 있을까요?"


def test_missing_points_keep_followup_on_first_attempt():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.4,
        status="insufficient",
        feedback_to_student="Try again.",
        socratic_follow_up="어떤 점을 더 생각해볼 수 있을까요?",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(evaluation, attempt_number=1)

    assert normalized.status == "insufficient"
    assert normalized.next_action == "ask_followup"
    assert normalized.reveal_missing_points is False
    assert normalized.socratic_follow_up == "어떤 점을 더 생각해볼 수 있을까요?"


def test_followup_feedback_does_not_reveal_missing_point_before_final_attempt():
    missing_point = "사용자가 빠르게 시스템을 익혀 효율적으로 사용할 수 있다는 점"
    evaluation = AnswerEvaluation(
        matched_points=["학습용이성은 쉽게 배우는 정도"],
        missing_points=[missing_point],
        misconceptions=[],
        score=0.5,
        status="partially_sufficient",
        feedback_to_student=f"{missing_point}이 빠졌습니다.",
        socratic_follow_up="처음 사용하는 사용자가 빨리 배운 뒤에는 어떤 이점이 생길까요?",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(evaluation, attempt_number=1)

    assert normalized.reveal_missing_points is False
    assert missing_point not in normalized.feedback_to_student
    assert "효율적으로 사용할 수" not in normalized.feedback_to_student


def test_followup_feedback_and_question_must_not_be_identical():
    repeated = "어떤 점을 더 생각해볼 수 있을까요?"
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student=repeated,
        socratic_follow_up=repeated,
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(evaluation, attempt_number=1)

    assert normalized.feedback_to_student != normalized.socratic_follow_up


def test_ask_followup_requires_socratic_follow_up():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student="조금 부족해요.",
        socratic_follow_up=None,
        hint=None,
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(evaluation, attempt_number=1)

    assert normalized.next_action == "ask_followup"
    assert normalized.socratic_follow_up


def test_semantic_match_short_korean_answer():
    required_point = "오랜만에 사용해도 쉽게 기억나는 것"
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=[required_point],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student="조금 부족해요.",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=[required_point],
        student_answer="오랜만에 사용해도 시스템이 쉽게 기억나고 학습 부담이 적다",
    )

    assert required_point in normalized.matched_points
    assert required_point not in normalized.missing_points


def test_llm_matched_point_id_is_not_cancelled_by_keyword_postprocessing():
    required_point = RequiredPoint(
        point_id="rp_001",
        text=(
            "Redis가 메모리 저장을 통해 응답 시간을 줄이는 이유와, 디스크 기반 DB에 대한 "
            "읽기 요청 부하가 줄어드는 결과를 연결해 설명해야 한다."
        ),
        gentle_hint="외부 요청 흐름을 생각해보게.",
        direct_hint="원본 DB 부하와 연결해보게.",
    )
    evaluation = AnswerEvaluation(
        matched_point_ids=["rp_001"],
        matched_points=[],
        missing_points=[required_point.text],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student="핵심을 짚었네.",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=[required_point.text],
        student_answer=(
            "자주 조회되는 데이터를 메모리에서 바로 꺼내면 외부 요청 흐름이 줄어들어 "
            "데이터베이스 부하가 낮아집니다."
        ),
        required_point_definitions=[required_point],
    )

    assert normalized.matched_point_ids == ["rp_001"]
    assert normalized.matched_points == [required_point.text]
    assert normalized.missing_points == []
    assert normalized.score == 1
    assert normalized.status == "sufficient"


def test_unknown_matched_point_id_is_ignored():
    required_point = RequiredPoint(
        point_id="rp_001",
        text="메모리 접근은 응답 시간을 줄인다.",
        gentle_hint="접근 위치를 생각해보게.",
        direct_hint="메모리 지연을 생각해보게.",
    )
    evaluation = AnswerEvaluation(
        matched_point_ids=["rp_999"],
        matched_points=[],
        missing_points=[],
        misconceptions=[],
        score=1.0,
        status="sufficient",
        feedback_to_student="충분하네.",
        next_action="next_question",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=[required_point.text],
        student_answer="관련 없는 답변",
        required_point_definitions=[required_point],
    )

    assert normalized.matched_point_ids == []
    assert normalized.score == 0
    assert normalized.status == "insufficient"


def test_added_required_point_moves_from_missing_to_matched():
    required_point = "다시 사용할 때 학습 부담이 적은 것"
    evaluation = AnswerEvaluation(
        matched_points=["오랜만에 사용해도 쉽게 기억나는 것"],
        missing_points=[required_point],
        misconceptions=[],
        score=0.5,
        status="partially_sufficient",
        feedback_to_student="보완됐어요.",
        next_action="next_question",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=2,
        required_points=["오랜만에 사용해도 쉽게 기억나는 것", required_point],
        student_answer="오랜만에 사용해도 쉽게 기억나고 다시 사용할 때 학습 부담이 적다",
    )

    assert required_point in normalized.matched_points
    assert required_point not in normalized.missing_points
    assert normalized.score == 1
    assert normalized.status == "sufficient"
    assert normalized.next_action == "next_question"


def test_attempt_1_insufficient_asks_followup():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student="Try again.",
        socratic_follow_up="무엇을 더 생각해볼까요?",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=["required point"],
        student_answer="unrelated answer",
    )

    assert normalized.status == "insufficient"
    assert normalized.next_action == "ask_followup"
    assert normalized.reveal_missing_points is False


def test_attempt_1_partially_sufficient_asks_followup():
    evaluation = AnswerEvaluation(
        matched_points=["required point"],
        missing_points=["missing point"],
        misconceptions=[],
        score=0.5,
        status="partially_sufficient",
        feedback_to_student="일부는 맞아요.",
        socratic_follow_up="무엇이 더 필요할까요?",
        next_action="next_question",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=1,
        required_points=["required point", "missing point"],
        student_answer="required point",
    )

    assert normalized.status == "partially_sufficient"
    assert normalized.next_action == "ask_followup"
    assert normalized.reveal_missing_points is False


def test_attempt_2_insufficient_still_asks_followup():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student="Try again.",
        socratic_follow_up="조금 더 직접적으로 생각해볼까요?",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=2,
        required_points=["required point"],
        student_answer="unrelated answer",
    )

    assert normalized.status == "insufficient"
    assert normalized.next_action == "ask_followup"
    assert normalized.reveal_missing_points is False


def test_first_attempt_uses_gentle_hint_linked_to_first_missing_point():
    evaluation = AnswerEvaluation(
        matched_points=["training fit"],
        missing_points=["generalization", "model complexity"],
        misconceptions=[],
        score=0.3,
        status="partially_sufficient",
        feedback_to_student="핵심의 일부를 붙잡았네.",
        socratic_follow_up="LLM이 만든 일반 질문",
        next_action="ask_followup",
    )
    required_point_definitions = [
        RequiredPoint(
            point_id="rp_001",
            text="generalization",
            gentle_hint="처음 보는 데이터에서는 어떨지 생각해보게.",
            direct_hint="훈련 성능과 테스트 성능을 비교해보게.",
        ),
        RequiredPoint(
            point_id="rp_002",
            text="model complexity",
            gentle_hint="모델이 너무 많은 규칙을 기억하면 어떨까?",
            direct_hint="모델 복잡도와 과적합의 관계를 생각해보게.",
        ),
    ]

    normalized = normalize_evaluation(
        evaluation, attempt_number=1, required_point_definitions=required_point_definitions
    )

    assert normalized.socratic_follow_up == "처음 보는 데이터에서는 어떨지 생각해보게."


def test_second_attempt_uses_direct_hint_linked_to_missing_point():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["generalization"],
        misconceptions=[],
        score=0,
        status="insufficient",
        feedback_to_student="아직 핵심 설명이 충분하지 않다네.",
        next_action="ask_followup",
    )
    required_point_definitions = [
        RequiredPoint(
            point_id="rp_001",
            text="generalization",
            gentle_hint="처음 보는 데이터에서는 어떨지 생각해보게.",
            direct_hint="훈련 성능과 테스트 성능을 비교해보게.",
        )
    ]

    normalized = normalize_evaluation(
        evaluation, attempt_number=2, required_point_definitions=required_point_definitions
    )

    assert normalized.socratic_follow_up == "훈련 성능과 테스트 성능을 비교해보게."


def test_attempt_3_insufficient_reveals_and_moves_next():
    evaluation = AnswerEvaluation(
        matched_points=[],
        missing_points=["required point"],
        misconceptions=[],
        score=0.0,
        status="insufficient",
        feedback_to_student="Try again.",
        hint="required point를 포함해야 합니다.",
        socratic_follow_up="Should be cleared.",
        next_action="ask_followup",
    )

    normalized = normalize_evaluation(
        evaluation,
        attempt_number=3,
        required_points=["required point"],
        student_answer="unrelated answer",
    )

    assert normalized.status == "insufficient"
    assert normalized.next_action == "next_question"
    assert normalized.reveal_missing_points is True
    assert normalized.socratic_follow_up is None


def test_evaluate_answer_uses_fake_llm_client():
    question = Question(
        question_id="q_001_001",
        concept_id="concept_001",
        question_type="explanation",
        question="Explain overfitting.",
        required_points=[RequiredPoint(
            point_id="rp_001", text="generalization",
            gentle_hint="Think about unseen data.", direct_hint="Compare train and test performance."
        )],
    )
    fake = FakeLLMClient(
        {
            "matched_point_ids": ["rp_001"],
            "missing_points": [],
            "misconceptions": [],
            "score": 0.8,
            "status": "sufficient",
            "feedback_to_student": "Good.",
            "hint": None,
            "next_action": "next_question",
        }
    )

    evaluation = evaluate_answer(fake, question, "It hurts generalization.", 1)

    assert evaluation.status == "sufficient"


def test_evaluate_answer_prefers_question_linked_hint_over_llm_followup():
    question = Question.model_validate(
        {
            "question_id": "q_001_001",
            "concept_id": "concept_001",
            "question_type": "explanation",
            "question": "Explain overfitting.",
            "required_points": [{
                "point_id": "rp_001",
                "text": "generalization",
                "gentle_hint": "처음 보는 데이터에서는 어떤 일이 생길까?",
                "direct_hint": "훈련 성능과 테스트 성능을 비교해보게.",
            }],
        }
    )
    fake = FakeLLMClient(
        {
            "matched_points": [],
            "missing_points": ["generalization"],
            "misconceptions": [],
            "score": 0,
            "status": "insufficient",
            "feedback_to_student": "아직 핵심 설명이 충분하지 않다네.",
            "hint": None,
            "socratic_follow_up": "LLM이 임의로 만든 질문",
            "next_action": "ask_followup",
        }
    )

    evaluation = evaluate_answer(fake, question, "training data", 1)

    assert evaluation.socratic_follow_up == "처음 보는 데이터에서는 어떤 일이 생길까?"
