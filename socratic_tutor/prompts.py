from __future__ import annotations

import json

from .models import Concept, Question, StudySession


def build_concept_extraction_prompt(
    markdown: str,
    subject: str | None,
    difficulty: str,
    max_concepts: int,
    output_language: str = "ko",
) -> tuple[str, str]:
    language_name = _language_name(output_language)
    system_prompt = (
        "You are an expert learning designer and Socratic tutor.\n"
        "Your job is to analyze lecture material and extract the most important learnable concepts.\n"
        "You must base your output only on the provided lecture material.\n"
        "Do not invent concepts not supported by the material.\n"
        "Return valid JSON only."
    )
    user_prompt = f"""Analyze the lecture material below.

Subject:
{subject or "Not specified"}

Difficulty:
{difficulty}

Maximum number of concepts:
{max_concepts}

Output language:
{language_name}

Lecture material:
{markdown}

    Return JSON in this exact shape:

    {{
      "concepts": [
        {{
          "title": "string",
          "summary": "string",
          "importance": "string",
          "source_pages": [1],
          "evidence_from_material": ["string"]
        }}
      ]
}}

Rules:
- Extract 5 to {max_concepts} concepts unless the material is too short.
- Prefer concepts that are central to understanding the lecture.
- Do not output trivial section titles unless they are actual concepts.
- Generate all user-facing fields in Korean if output_language is "ko".
- Generate all user-facing fields in English if output_language is "en".
    - User-facing concept fields are title, summary, importance, and evidence_from_material.
    - Even if the lecture material is in English, user-facing concept fields must be written in the output language.
    - Preserve technical terms when appropriate, but explain them naturally in the output language.
    - source_pages may be approximate if exact page information is unavailable.
    - evidence_from_material must quote or paraphrase specific material from the lecture.
    - Do not generate prerequisites.
    - Do not generate common_misconceptions.
    - Return JSON only.
    """
    return system_prompt, user_prompt


def build_question_generation_prompt(
    concept: Concept,
    document_excerpt: str,
    questions_per_concept: int,
    output_language: str = "ko",
) -> tuple[str, str]:
    language_name = _language_name(output_language)
    concept_payload = {
        "concept_id": concept.concept_id,
        "title": concept.title,
        "summary": concept.summary,
        "importance": concept.importance,
        "source_pages": concept.source_pages,
        "evidence_from_material": concept.evidence_from_material,
    }
    system_prompt = (
        "You are a Socratic learning tutor.\n"
        "Generate questions that make the student explain, compare, and apply the concept.\n"
        "Do not generate simple memorization-only quiz questions.\n"
        "Return valid JSON only."
    )
    user_prompt = f"""Concept:
{json.dumps(concept_payload, ensure_ascii=False, indent=2)}

Relevant lecture excerpt:
{document_excerpt}

Generate {questions_per_concept} Socratic questions.

Output language:
{language_name}

Allowed question types:
- explanation
- comparison
- application

Return JSON in this exact shape:

{{
  "questions": [
    {{
      "question_type": "explanation",
      "question": "string",
      "required_points": ["string"],
      "hints": ["string"],
      "source_pages": [1]
    }}
  ]
}}

Question generation rules:
- Each question must be answerable from the lecture material.
- Base questions on the concept summary, importance, evidence_from_material, source_pages, and relevant lecture excerpt.
- Each question should ask one main thing only.
- Avoid compound questions connected by "and" when they require multiple distinct answers.
- Prefer smaller Socratic steps over broad essay-style questions.
- A question should be answerable in 2-4 sentences.
- If the concept is complex, generate a sequence from concrete intuition to abstract explanation.
- Generate all user-facing fields in Korean if output_language is "ko".
- Generate all user-facing fields in English if output_language is "en".
- Even if the lecture material is in English, questions must be written in the output language.
- Preserve technical terms when appropriate, but explain them naturally in the output language.
- User-facing question fields are question, required_points, and hints.
- Do not generate optional_points.
- Do not generate common_missing_points.
- required_points are the only grading criteria for this question.
- Hints must help the student infer missing required_points without revealing the full answer immediately.
- Generate no more than one question of the same type unless necessary.
- Return JSON only.
"""
    return system_prompt, user_prompt


def build_answer_evaluation_prompt(
    question: Question,
    student_answer: str,
    attempt_number: int,
    output_language: str = "ko",
) -> tuple[str, str]:
    language_name = _language_name(output_language)
    system_prompt = (
        "You are a supportive Socratic tutor.\n"
        "Evaluate the student's answer against the required points.\n"
        "Your goal is not to shame the student, but to help them improve.\n"
        "Do not reveal the complete model answer unless the student has already attempted multiple times.\n"
        "Return valid JSON only."
    )
    user_prompt = f"""Question:
{question.question}

Question type:
{question.question_type}

Required points:
{question.required_points}

Available hints:
{question.hints}

Student answer:
{student_answer}

Attempt number:
{attempt_number}

Output language:
{language_name}

Return JSON in this exact shape:

{{
  "matched_points": ["string"],
  "missing_points": ["string"],
  "misconceptions": ["string"],
  "score": 0.0,
  "status": "sufficient",
  "feedback_to_student": "string",
  "hint": "string or null",
  "improvement_note": "string or null",
  "socratic_follow_up": "string or null",
  "reveal_missing_points": false,
  "next_action": "next_question"
}}

Status rules:
- sufficient: all required_points are satisfied and no major misconception
- partially_sufficient: at least one required_point is satisfied, but one or more required_points are missing, and there is no major misconception
- insufficient: no required_points are satisfied and no major misconception
- misconception: answer contains an important incorrect idea

Next action rules:
- sufficient -> next_question
- partially_sufficient -> ask_followup on attempts 1-2, next_question on attempt 3 or higher
- insufficient -> ask_followup on attempts 1-2, next_question on attempt 3 or higher
- misconception -> ask_followup on attempts 1-2, next_question on attempt 3 or higher

Semantic grading rules:
- Evaluate semantic meaning, not exact wording.
- If the student expresses a required point in simpler, shorter, or slightly different words, count it as matched.
- Do not require elaborate explanations unless the required_point explicitly asks for reasoning.
- If the student directly mentions the key idea of a required point, mark it as matched.
- Do not mark a required point as missing if the same meaning appears anywhere in the student's answer.
- missing_points must include only required_points that are not semantically present in the answer.
- If every required_point is semantically present, missing_points must be empty.
- If missing_points is empty, status must be sufficient.
- Do not mark an answer sufficient if any required_point is missing.
- For short-answer CLI learning, concise answers should be accepted if they contain the required meaning.
- Do not reverse matched and missing points across attempts.
- If the student improves their answer by adding a previously missing required point, that point must move from missing_points to matched_points.
- missing_points must include only unmet required_points.
- Do not use optional_points or common_missing_points to decide score, status, or next_action.
- Treat score as advisory only; decide status and next_action from misconceptions, matched_points, missing_points, and attempt_number.

Semantic grading example:
- Required point: "오랜만에 사용해도 쉽게 기억나는 것"
- Student answer: "오랜만에 사용해도 시스템이 쉽게 기억나고 학습 부담이 적다"
- Correct evaluation: matched_points includes "오랜만에 사용해도 쉽게 기억나는 것"
- Incorrect evaluation: missing_points includes "오랜만에 사용해도 쉽게 기억나는 것"

Attempt policy:
- The maximum number of attempts per question is 3.
- On attempt 1, if the answer is insufficient or has a misconception, do not reveal missing_points to the student. Create a Socratic follow-up question.
- On attempt 2, if the answer is still insufficient or has a misconception, do not reveal missing_points yet. Create a more direct Socratic follow-up question or hint.
- On attempt 3 or higher, if the answer is still insufficient or has a misconception, reveal the missing required points and provide a brief direct explanation.
- Move to the next question before the maximum attempt only when missing_points is empty and there are no misconceptions.

Feedback rules:
- Be concise.
- Always acknowledge what the student got right, if anything.
- feedback_to_student must diagnose the current answer only: what is good and what is still weak.
- feedback_to_student must diagnose the answer, not teach the missing required point directly.
- feedback_to_student must not provide a long complete answer.
- Use required_points as the only grading criteria.
- Do not use optional_points or common_missing_points to decide score, status, or next_action.
- matched_points must include only satisfied required_points.
- missing_points must include only unmet required_points.
- If all required_points are satisfied and there are no misconceptions, missing_points must be empty, status must be sufficient, and next_action must be next_question.
- If any required_point is missing, do not set status to sufficient.
- If there are misconceptions, status must be misconception.
- Judge misconceptions from the student_answer, required_points, and question context only.
- Do not use concept-level common_misconceptions to decide status or next_action.
- For attempt 1 or 2 insufficient or misconception answers, do not reveal the full missing points to the student.
- For attempt 1 or 2 insufficient or misconception answers, feedback_to_student should not list all missing_points.
- Do not reveal the exact missing required point in feedback_to_student before the final attempt.
- If reveal_missing_points is false, do not include missing_points verbatim or near-verbatim in feedback_to_student.
- If some required_points are missing on attempt 1 or 2, create a socratic_follow_up using the hints.
- The Socratic follow-up should be a question, not an explanation.
- The Socratic follow-up should not contain the full correct answer.
- Put the reasoning path toward the missing idea in socratic_follow_up.
- The feedback and the follow-up must not repeat the same sentence.
- If next_action is ask_followup, feedback_to_student should be short and broad; socratic_follow_up should do the actual guidance.
- socratic_follow_up should be based on missing_points and hints.
- Use socratic_follow_up only when next_action is ask_followup.
- Use improvement_note only when next_action is next_question.
- improvement_note should explain what perspective would make the answer better.
- improvement_note must be explanatory, not a question.
- improvement_note must not repeat feedback_to_student.
- Use reveal_missing_points = false when attempt_number is 1 or 2 and status is insufficient or misconception.
- Use reveal_missing_points = true when attempt_number >= 3 and status is still insufficient or misconception.
- For partially_sufficient answers before attempt 3, set next_action to ask_followup and use socratic_follow_up instead of improvement_note.
- When next_action is next_question, socratic_follow_up must be null.
- When next_action is ask_followup, improvement_note must be null.
- On attempt 2, the hint or socratic_follow_up may be more direct, but missing points should still not be shown to the student.
- On attempt 3 or higher, missing points may be shown and the hint may be a brief direct explanation.

Language rules:
- The student may answer in Korean, English, or a mixture of both.
- Evaluate the answer semantically, not by exact wording.
- Do not penalize the student for answering in Korean when the lecture material or question concepts are originally in English.
- Return all user-facing feedback in Korean if output_language is "ko".
- Return all user-facing feedback in English if output_language is "en".
- User-facing evaluation fields are matched_points, missing_points, misconceptions, feedback_to_student, hint, improvement_note, and socratic_follow_up.
- Technical terms such as LLM, multimodality, attention, embedding, overfitting may remain in English if that is more natural, but explanations should be in the output language.
- Keep enum values in English: status and next_action must use the allowed English enum values.
- Return JSON only.
"""
    return system_prompt, user_prompt


def build_session_summary_prompt(
    session: StudySession,
    output_language: str = "ko",
) -> tuple[str, str]:
    language_name = _language_name(output_language)
    system_prompt = (
        "You are a learning coach.\n"
        "Summarize the student's learning session based on their answers and evaluations.\n"
        "Return valid JSON only."
    )
    user_prompt = f"""Study session:
{json.dumps(session.model_dump(mode="json"), ensure_ascii=False, indent=2)}

Output language:
{language_name}

Return JSON in this exact shape:

{{
  "strong_concepts": ["string"],
  "weak_concepts": ["string"],
  "frequently_missing_points": ["string"],
  "recommended_review_questions": ["string"],
  "overall_feedback": "string"
}}

Rules:
- strong_concepts should be concepts where most answers were sufficient.
- weak_concepts should be concepts where answers were insufficient or had misconceptions.
- recommended_review_questions should be actionable.
- overall_feedback should be supportive and specific.
- Write the session summary in Korean if output_language is "ko".
- Write the session summary in English if output_language is "en".
- Preserve technical terms in English when they are commonly used that way.
- Keep feedback concise, supportive, and specific.
- Return JSON only.
"""
    return system_prompt, user_prompt


def _language_name(output_language: str) -> str:
    if output_language == "ko":
        return 'Korean (output_language is "ko")'
    if output_language == "en":
        return 'English (output_language is "en")'
    return 'Korean (output_language is "ko")'
