const UNDERSTANDING_LEVELS = [
  { min: 95, label: "완벽" },
  { min: 80, label: "우수" },
  { min: 60, label: "보통" },
  { min: 0, label: "복습 필요" },
];

function levelForPercent(percent) {
  return UNDERSTANDING_LEVELS.find((level) => percent >= level.min).label;
}

function latestAnswersByQuestion(answers) {
  const latest = new Map();
  for (const answer of answers) {
    const current = latest.get(answer.question_id);
    if (!current || answer.attempt_number >= current.attempt_number) {
      latest.set(answer.question_id, answer);
    }
  }
  return latest;
}

export function perConceptUnderstanding(session) {
  const concepts = session?.concepts ?? [];
  const questions = session?.questions ?? [];
  const answers = session?.answers ?? [];
  const latest = latestAnswersByQuestion(answers);

  return concepts.map((concept) => {
    const conceptQuestions = questions.filter((question) => question.concept_id === concept.concept_id);
    const scores = conceptQuestions
      .map((question) => latest.get(question.question_id)?.evaluation?.score)
      .filter((score) => typeof score === "number");
    const percent = scores.length
      ? Math.round((scores.reduce((sum, score) => sum + score, 0) / scores.length) * 100)
      : 0;
    return {
      conceptId: concept.concept_id,
      title: concept.title,
      summary: concept.summary,
      sourcePages: concept.source_pages ?? [],
      percent,
      label: levelForPercent(percent),
      hasData: scores.length > 0,
    };
  });
}

export function missedQuestionReview(session) {
  const questions = session?.questions ?? [];
  const answers = session?.answers ?? [];
  const byQuestion = new Map();
  for (const answer of answers) {
    const list = byQuestion.get(answer.question_id) ?? [];
    list.push(answer);
    byQuestion.set(answer.question_id, list);
  }

  return questions
    .map((question) => {
      const attempts = (byQuestion.get(question.question_id) ?? [])
        .slice()
        .sort((a, b) => a.attempt_number - b.attempt_number);
      if (attempts.length === 0) {
        return { questionId: question.question_id, question: question.question, tag: "미완료" };
      }
      const last = attempts[attempts.length - 1];
      if (last.answer_text === "/skip") {
        return { questionId: question.question_id, question: question.question, tag: "미완료" };
      }
      if (last.evaluation?.status === "sufficient") {
        if (attempts.length > 1) {
          return { questionId: question.question_id, question: question.question, tag: "힌트 후 정답" };
        }
        return null;
      }
      return { questionId: question.question_id, question: question.question, tag: "미완료" };
    })
    .filter(Boolean);
}

export function highlightsAndGaps(session) {
  const answers = session?.answers ?? [];
  const latest = Array.from(latestAnswersByQuestion(answers).values());
  const highlights = latest.flatMap((answer) => answer.evaluation?.matched_points ?? []).filter(Boolean);
  const gaps = session?.summary?.frequently_missing_points ?? [];
  return { highlights: [...new Set(highlights)], gaps };
}

export function formatStudySeconds(totalSeconds) {
  const seconds = Math.max(0, Math.round(totalSeconds ?? 0));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  if (hours > 0) return `${hours}시간 ${minutes}분`;
  return `${minutes}분`;
}
