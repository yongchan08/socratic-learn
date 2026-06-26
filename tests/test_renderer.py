from socratic_tutor.models import AnswerEvaluation
from socratic_tutor.renderer import console, print_evaluation


def test_renderer_hides_missing_points_on_first_attempt():
    evaluation = AnswerEvaluation(
        matched_points=["visual context adds information"],
        missing_points=["language does not exist in isolation"],
        misconceptions=[],
        score=0.4,
        status="insufficient",
        feedback_to_student="좋은 출발이에요.",
        hint="Think about context.",
        socratic_follow_up="단어 말고 의미를 보완하는 정보에는 무엇이 있을까요?",
        reveal_missing_points=False,
        next_action="ask_followup",
    )

    with console.capture() as capture:
        print_evaluation(evaluation, attempt_number=1)

    output = capture.get()
    assert "보완할 내용" not in output
    assert "language does not exist in isolation" not in output
    assert "단어 말고 의미를 보완하는 정보에는 무엇이 있을까요?" in output


def test_renderer_does_not_show_missing_points_before_third_attempt():
    evaluation = AnswerEvaluation(
        matched_points=["visual context adds information"],
        missing_points=["language does not exist in isolation"],
        misconceptions=[],
        score=0.4,
        status="insufficient",
        feedback_to_student="좋아요. 일부는 이해했어요.",
        hint="텍스트만 보는 모델과 비교해보세요.",
        socratic_follow_up="무엇을 놓칠까요?",
        reveal_missing_points=False,
        next_action="ask_followup",
    )

    with console.capture() as capture:
        print_evaluation(evaluation, attempt_number=2)

    output = capture.get()
    assert "보완할 내용" not in output
    assert "language does not exist in isolation" not in output
    assert "무엇을 놓칠까요?" in output


def test_renderer_shows_missing_points_on_third_attempt():
    evaluation = AnswerEvaluation(
        matched_points=["visual context adds information"],
        missing_points=["language does not exist in isolation"],
        misconceptions=[],
        score=0.4,
        status="insufficient",
        feedback_to_student="좋아요. 일부는 이해했어요.",
        hint="텍스트만 보는 모델과 비교해보세요.",
        reveal_missing_points=True,
        next_action="next_question",
    )

    with console.capture() as capture:
        print_evaluation(evaluation, attempt_number=3)

    output = capture.get()
    assert "보완할 내용" in output
    assert "language does not exist in isolation" in output
    assert "힌트 또는 짧은 설명" in output


def test_renderer_next_question_prints_improvement_note_not_followup():
    evaluation = AnswerEvaluation(
        matched_points=["사용자가 시스템을 쉽게 배울 수 있는 정도"],
        missing_points=[],
        misconceptions=[],
        score=1.0,
        status="sufficient",
        feedback_to_student="학습용이성이 쉽게 배울 수 있는 정도라는 점은 잘 설명했어요.",
        improvement_note="초기 진입 장벽을 낮추고 더 효율적으로 사용할 수 있게 해준다는 점까지 연결하면 좋아요.",
        socratic_follow_up="왜 중요할까요?",
        next_action="next_question",
    )

    with console.capture() as capture:
        print_evaluation(evaluation, attempt_number=1)

    output = capture.get()
    assert "조금 더 보완하면 좋은 점" in output
    assert "초기 진입 장벽" in output
    assert "왜 중요할까요?" not in output


def test_renderer_skips_duplicate_improvement_note():
    evaluation = AnswerEvaluation(
        matched_points=["required point"],
        missing_points=[],
        misconceptions=[],
        score=1.0,
        status="sufficient",
        feedback_to_student="방향은 맞아요.",
        improvement_note="방향은 맞아요.",
        next_action="next_question",
    )

    with console.capture() as capture:
        print_evaluation(evaluation, attempt_number=1)

    output = capture.get()
    assert "조금 더 보완하면 좋은 점" not in output
