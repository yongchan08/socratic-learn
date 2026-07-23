import { Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";
import { WeekReportModal } from "../components/WeekReportModal.jsx";

function studySecondsFor(session) {
  if (!session?.started_at || !session?.ended_at) return null;
  const seconds = (new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 1000;
  return Number.isFinite(seconds) ? seconds : null;
}

function getAdviceText(evaluation) {
  if (!evaluation || evaluation.status === "sufficient") return null;
  return evaluation.socratic_follow_up || evaluation.hint || evaluation.improvement_note || null;
}

function statusLabel(status) {
  const labels = {
    sufficient: "충분함",
    partially_sufficient: "부분적으로 충분함",
    insufficient: "부족함",
    misconception: "오개념 있음",
  };
  return labels[status] ?? status;
}

export function StudyView({
  audioSettings,
  answers,
  busy,
  concepts,
  courseProgress,
  courseTitle,
  currentQuestion,
  dismissedTransitionAnswerId,
  onAcademy,
  onAnswerChange,
  onDismissTransition,
  onPostAction,
  onSubmitAnswer,
  progress,
  questionText,
  state,
  answer,
}) {
  const lastAnswer = state?.last_answer;
  const currentIndex = state?.current_index ?? 0;
  const totalQuestions = state?.total_questions ?? 0;
  const lastAnswerIsForCurrentQuestion = lastAnswer?.question_id === currentQuestion?.question_id;
  const showFollowupEvaluation = lastAnswer?.evaluation && lastAnswerIsForCurrentQuestion && lastAnswer.evaluation.status !== "sufficient";
  const showTransitionEvaluation = lastAnswer?.evaluation && lastAnswer.evaluation.next_action === "next_question" &&
    lastAnswer.answer_text !== "/skip" && !lastAnswerIsForCurrentQuestion &&
    dismissedTransitionAnswerId !== lastAnswer.answer_id;
  const showEvaluationMessage = Boolean(showTransitionEvaluation || (!state?.completed && showFollowupEvaluation));
  const adviceText = showEvaluationMessage ? getAdviceText(lastAnswer?.evaluation) : null;
  const showWeekReport = Boolean(state?.completed && state?.session?.summary);
  const paperTitle = questionText || "질문을 불러오는 중입니다.";
  const answerLimit = 1000;

  const reviewQuestion = showTransitionEvaluation
    ? state?.session?.questions?.find((question) => question.question_id === lastAnswer.question_id)
    : null;

  return (
    <>
      <ScreenShell
        className="study-bg"
        topBar={
          <TopBar
            onAcademy={onAcademy}
            academyLabel="로드맵 보기"
            audioSettings={audioSettings}
            courseTitle={courseTitle}
            progressPercent={courseProgress}
          />
        }
      >
        <div className="study-layout">
          <aside className="slp-component study-sidebar">
            <div className="slp-sidebar">
              <section className="slp-panel slp-panel--lessons" aria-labelledby="gate-title">
                <h2 className="slp-panel-title" id="gate-title">학문의 관문</h2>
                <svg className="slp-title-divider" aria-hidden="true"><use href="#slpTitleDivider"/></svg>
                <ol className="slp-lessons">
                  {concepts.map((concept, index) => {
                    const isActive = currentQuestion?.concept_id === concept.concept_id;
                    const isPassed = (state?.current_index ?? 0) > index;
                    const lessonState = isPassed ? "complete" : isActive ? "active" : "locked";
                    const iconHref = lessonState === "complete" ? "#slpCompass" : lessonState === "active" ? "#slpChevron" : "#slpLock";
                    const iconCls = lessonState === "complete" ? "slp-state-icon slp-state-icon--compass" : lessonState === "active" ? "slp-state-icon slp-state-icon--chevron" : "slp-state-icon slp-state-icon--lock";
                    return (
                      <li key={concept.concept_id} className="slp-lesson-item">
                        <button
                          className={`slp-lesson-button is-${lessonState}`}
                          type="button"
                          disabled={lessonState === "locked"}
                          aria-current={isActive ? "step" : undefined}
                        >
                          <span className="slp-lesson-number">{index + 1}</span>
                          <span className="slp-lesson-label">{concept.title}</span>
                          <svg className={iconCls} aria-hidden="true"><use href={iconHref}/></svg>
                        </button>
                      </li>
                    );
                  })}
                </ol>
                <blockquote className="ccp-quote study-quote">
                  "설명할 때에야 진짜로 아는 것이다."
                  <cite>— 소크라테스</cite>
                </blockquote>
              </section>
            </div>
          </aside>

          <main className="study-main-panel">
            <section className="study-paper">
              <div className="study-paper-content">
                <div className="study-paper-chip">
                  {totalQuestions ? `${Math.min(currentIndex + 1, totalQuestions)} / ${totalQuestions}` : "0 / 0"}
                </div>
                <h2 className="study-paper-title">{paperTitle}</h2>
                <p className="study-paper-desc">아래 영역에 자신의 언어로 설명해보세요.</p>

                {showEvaluationMessage && lastAnswer?.evaluation && (
                  <div className="study-feedback">
                    <strong>{Math.round(lastAnswer.evaluation.score * 100)}점 · {statusLabel(lastAnswer.evaluation.status)}</strong>
                    <p>{lastAnswer.evaluation.feedback_to_student}</p>
                  </div>
                )}

                {showTransitionEvaluation ? (
                  <>
                    <div className="study-transition-card">
                      <p className="study-transition-label">이전 답변 평가</p>
                      <p className="study-transition-question">{reviewQuestion?.question}</p>
                      {adviceText && <p className="study-transition-advice">{adviceText}</p>}
                    </div>
                    <div className="study-action-row">
                      <button
                        type="button"
                        className="study-basic-button"
                        disabled={busy}
                        onClick={() => onDismissTransition(lastAnswer.answer_id)}
                      >
                        <span>{state.completed ? "기록서 보기" : "다음 질문으로"}</span>
                      </button>
                    </div>
                  </>
                ) : !state.completed && currentQuestion ? (
                  <form onSubmit={onSubmitAnswer}>
                    <label className="study-textarea-shell">
                      <span className="visually-hidden">답변 입력</span>
                      <textarea
                        className="study-textarea"
                        value={answer}
                        onChange={(e) => onAnswerChange(e.target.value)}
                        placeholder="여기에 답변을 입력하세요..."
                        maxLength={answerLimit}
                      />
                    </label>
                    <div className="study-counter">{answer.length} / {answerLimit}</div>
                    <div className="study-action-row">
                      <button className="study-basic-button" type="submit" disabled={busy || !answer.trim()}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                          {busy ? <Loader2 className="spin" size={18}/> : null}
                          답변 제출
                        </span>
                      </button>
                    </div>
                  </form>
                ) : (
                  <p className="study-note">모든 질문을 완료했습니다.</p>
                )}
              </div>
            </section>
          </main>
        </div>
      </ScreenShell>
      {showWeekReport && (
        <WeekReportModal
          session={state.session}
          subtitle="학습 완료"
          studySeconds={studySecondsFor(state.session)}
          onReturnToRoadmap={onAcademy}
        />
      )}
    </>
  );
}
