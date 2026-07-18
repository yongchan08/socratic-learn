from __future__ import annotations

import re

from .models import AnswerEvaluation, Question, RequiredPoint
from .prompts import build_answer_evaluation_prompt


MAX_ATTEMPTS_PER_QUESTION = 3
SEMANTIC_KEYWORD_MATCH_RATIO = 0.55
DIRECT_ANSWER_KEYWORD_MATCH_RATIO = 0.5


def normalize_evaluation(
    evaluation: AnswerEvaluation,
    attempt_number: int | None = None,
    required_points: list[str] | None = None,
    student_answer: str | None = None,
    required_point_definitions: list[RequiredPoint] | None = None,
) -> AnswerEvaluation:
    data = evaluation.model_dump()
    required_points = required_points or []

    if required_points:
        matched_points = _matched_required_points(
            required_points=required_points,
            required_point_definitions=required_point_definitions or [],
            llm_matched_point_ids=data["matched_point_ids"],
            llm_matched_points=data["matched_points"],
            student_answer=student_answer or "",
        )
        missing_points = [point for point in required_points if point not in matched_points]
        score = len(matched_points) / len(required_points)
        data["matched_points"] = matched_points
        definition_by_text = {point.text: point.point_id for point in required_point_definitions or []}
        data["matched_point_ids"] = [
            definition_by_text[point] for point in matched_points if point in definition_by_text
        ]
        data["missing_points"] = missing_points
        data["score"] = score
    else:
        data["score"] = min(max(evaluation.score, 0.0), 1.0)

    if data["misconceptions"]:
        data["status"] = "misconception"
    elif not data["missing_points"]:
        data["status"] = "sufficient"
    elif data["matched_points"]:
        data["status"] = "partially_sufficient"
    else:
        data["status"] = "insufficient"

    current_attempt = attempt_number or 1
    if data["status"] == "sufficient":
        data["next_action"] = "next_question"
        data["reveal_missing_points"] = False
        data["hint"] = None
        data["socratic_follow_up"] = None
        data["improvement_note"] = None
        _normalize_sufficient_feedback(data)
    elif current_attempt < MAX_ATTEMPTS_PER_QUESTION:
        data["next_action"] = "ask_followup"
        data["reveal_missing_points"] = False
        data["improvement_note"] = None
        _normalize_followup_feedback(data, current_attempt, required_point_definitions or [])
    else:
        data["next_action"] = "next_question"
        data["reveal_missing_points"] = True
        data["socratic_follow_up"] = None
        data["improvement_note"] = None

    return AnswerEvaluation.model_validate(data)


def _normalize_followup_feedback(
    data: dict,
    attempt_number: int,
    required_points: list[RequiredPoint],
) -> None:
    if _reveals_missing_point(data["feedback_to_student"], data["missing_points"]):
        data["feedback_to_student"] = _broad_feedback_for_status(data["status"])

    follow_up = _linked_hint(data["missing_points"], required_points, attempt_number)
    follow_up = follow_up or data.get("socratic_follow_up") or data.get("hint")
    if not follow_up or _is_similar_text(data["feedback_to_student"], follow_up):
        follow_up = _fallback_follow_up()
    data["socratic_follow_up"] = follow_up


def _linked_hint(
    missing_points: list[str],
    required_points: list[RequiredPoint],
    attempt_number: int,
) -> str | None:
    if not missing_points:
        return None
    first_missing = missing_points[0]
    linked = next((point for point in required_points if point.text == first_missing), None)
    if linked is None:
        return None
    return linked.gentle_hint if attempt_number <= 1 else linked.direct_hint


def _normalize_sufficient_feedback(data: dict) -> None:
    if _feedback_mentions_gap(data["feedback_to_student"]):
        data["feedback_to_student"] = "그대는 이 물음의 핵심을 충분히 붙잡았네. 이제 다음 물음으로 나아가 보게."


def _feedback_mentions_gap(feedback: str) -> bool:
    feedback_norm = _normalize_text(feedback)
    gap_markers = {
        "부족",
        "빠졌",
        "빠진",
        "보완",
        "다시",
        "힌트",
        "missing",
        "insufficient",
        "lack",
        "weak",
        "improve",
        "try again",
    }
    return any(marker in feedback_norm for marker in gap_markers)


def _reveals_missing_point(feedback: str, missing_points: list[str]) -> bool:
    for point in missing_points:
        if _is_near_verbatim(point, feedback):
            return True
    return False


def _is_near_verbatim(source: str, text: str) -> bool:
    source_norm = _normalize_text(source)
    text_norm = _normalize_text(text)
    if not source_norm or not text_norm:
        return False
    source_joined = source_norm.replace(" ", "")
    text_joined = text_norm.replace(" ", "")
    if source_joined in text_joined:
        return True

    source_keywords = set(_keywords(source))
    if len(source_keywords) < 2:
        return False
    text_keywords = set(_keywords(text))
    return len(source_keywords & text_keywords) / len(source_keywords) >= 0.8


def _is_similar_text(left: str, right: str) -> bool:
    left_norm = _normalize_text(left)
    right_norm = _normalize_text(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    left_tokens = set(left_norm.split())
    right_tokens = set(right_norm.split())
    if not left_tokens or not right_tokens:
        return False
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens) >= 0.85


def _broad_feedback_for_status(status: str) -> str:
    if status == "misconception":
        return "그대의 답에는 다시 살펴볼 핵심 방향이 있네."
    if status == "partially_sufficient":
        return "그대는 핵심의 일부를 붙잡았네. 다만 아직 비어 있는 자리가 있네."
    return "그대의 출발은 보았네. 다만 핵심 설명이 아직 충분하지 않다네."


def _fallback_follow_up() -> str:
    return "이 개념을 실제 상황에 놓아 본다면, 그대는 무엇을 더 설명해야 하겠는가?"


def evaluate_answer(
    llm_client: object,
    question: Question,
    student_answer: str,
    attempt_number: int,
    output_language: str = "ko",
) -> AnswerEvaluation:
    system_prompt, user_prompt = build_answer_evaluation_prompt(
        question=question,
        student_answer=student_answer,
        attempt_number=attempt_number,
        output_language=output_language,
    )
    payload = llm_client.complete_json(system_prompt, user_prompt)
    return normalize_evaluation(
        AnswerEvaluation.model_validate(payload),
        attempt_number=attempt_number,
        required_points=question.required_point_texts,
        student_answer=student_answer,
        required_point_definitions=question.required_points,
    )


def _matched_required_points(
    required_points: list[str],
    required_point_definitions: list[RequiredPoint],
    llm_matched_point_ids: list[str],
    llm_matched_points: list[str],
    student_answer: str,
) -> list[str]:
    point_by_id = {point.point_id: point.text for point in required_point_definitions}
    llm_matched_by_id = {
        point_by_id[point_id] for point_id in llm_matched_point_ids if point_id in point_by_id
    }
    matched: list[str] = []
    for required_point in required_points:
        if (
            required_point in llm_matched_by_id
            or _is_semantic_match(required_point, llm_matched_points)
            or _has_obvious_keyword_overlap(required_point, student_answer)
        ):
            matched.append(required_point)
    return matched


def _is_semantic_match(required_point: str, candidates: list[str]) -> bool:
    required_norm = _normalize_text(required_point)
    if not required_norm:
        return False
    required_joined = required_norm.replace(" ", "")
    for candidate in candidates:
        candidate_norm = _normalize_text(candidate)
        candidate_joined = candidate_norm.replace(" ", "")
        if not candidate_joined:
            continue
        if required_joined in candidate_joined:
            return True
        required_keywords = set(_keywords(required_point))
        candidate_keywords = set(_keywords(candidate))
        if (
            required_keywords
            and candidate_keywords
            and candidate_joined in required_joined
            and len(candidate_joined) / len(required_joined) >= 0.6
        ):
            return True
        if required_keywords and len(required_keywords & candidate_keywords) / len(required_keywords) >= SEMANTIC_KEYWORD_MATCH_RATIO:
            return True
    return False


def _has_obvious_keyword_overlap(required_point: str, student_answer: str) -> bool:
    required_norm = _normalize_text(required_point)
    answer_norm = _normalize_text(student_answer)
    if not required_norm or not answer_norm:
        return False
    if required_norm.replace(" ", "") in answer_norm.replace(" ", ""):
        return True

    required_keywords = _keywords(required_point)
    answer_keywords = set(_keywords(student_answer))
    if not required_keywords or not answer_keywords:
        return False

    overlap = [keyword for keyword in required_keywords if keyword in answer_keywords]
    required_ratio = len(overlap) / len(required_keywords)
    min_overlap = 1 if len(required_keywords) <= 2 else 2
    return len(overlap) >= min_overlap and required_ratio >= DIRECT_ANSWER_KEYWORD_MATCH_RATIO


def _normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    without_punctuation = re.sub(r"[^\w\s가-힣]", " ", lowered)
    return " ".join(without_punctuation.split())


def _keywords(text: str) -> list[str]:
    stopwords = {
        "것",
        "수",
        "등",
        "및",
        "또는",
        "그리고",
        "the",
        "a",
        "an",
        "to",
        "of",
        "and",
        "or",
        "is",
        "are",
        "point",
        "required",
        "missing",
        "minor",
    }
    keywords: list[str] = []
    for token in _normalize_text(text).split():
        stem = _stem_token(token)
        if len(stem) >= 2 and stem not in stopwords:
            keywords.append(stem)
    return keywords


def _stem_token(token: str) -> str:
    suffixes = [
        "입니다",
        "합니다",
        "되는",
        "하는",
        "하게",
        "하고",
        "에도",
        "에서",
        "에게",
        "으로",
        "로서",
        "라는",
        "이다",
        "하다",
        "된다",
        "나는",
        "나고",
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "에",
        "도",
        "고",
    ]
    stem = token
    for suffix in suffixes:
        if stem.endswith(suffix) and len(stem) - len(suffix) >= 2:
            stem = stem[: -len(suffix)]
            break
    return stem
