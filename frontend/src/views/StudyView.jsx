import { Loader2, Send } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { SsbBC, SrpCorners, SlpCorners } from "../components/Ornaments.jsx";
import { TopBar } from "../components/TopBar.jsx";
import { WeekReportModal } from "../components/WeekReportModal.jsx";
import { MAX_ATTEMPTS_PER_QUESTION } from "../constants.js";

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
  const lastAnswerIsForCurrentQuestion = lastAnswer?.question_id === currentQuestion?.question_id;
  const showFollowupEvaluation = lastAnswer?.evaluation && lastAnswerIsForCurrentQuestion && lastAnswer.evaluation.status !== "sufficient";
  const showTransitionEvaluation = lastAnswer?.evaluation && lastAnswer.evaluation.next_action === "next_question" &&
    lastAnswer.answer_text !== "/skip" && !lastAnswerIsForCurrentQuestion &&
    dismissedTransitionAnswerId !== lastAnswer.answer_id;
  const showEvaluationMessage = Boolean(showTransitionEvaluation || (!state?.completed && showFollowupEvaluation));
  const visibleAttemptCount = showEvaluationMessage
    ? (lastAnswer?.attempt_number ?? 0)
    : answers.filter((item) => item.question_id === currentQuestion?.question_id).length;
  const adviceText = showEvaluationMessage ? getAdviceText(lastAnswer?.evaluation) : null;
  const showWeekReport = state.completed && Boolean(state.session.summary);

  return (
    <>
    <ScreenShell
      className=""
      topBar={
        <TopBar
          onAcademy={onAcademy}
          academyLabel="로드맵 보기"
          audioSettings={audioSettings}
          courseTitle={courseTitle}
          progressPercent={courseProgress}
          userLabel="지혜를 찾는 자"
        />
      }
      backgroundContent={
        <div className="study-socrates">
          <img src="/theme-assets/socrates.png" alt="AI 소크라테스"/>
        </div>
      }
    >
      <div className="app-body">
        <div className="slp-component">
          <div className="slp-sidebar">
            <section className="slp-panel slp-panel--lessons" aria-labelledby="gate-title">
              <SlpCorners/>
              <h2 className="slp-panel-title" id="gate-title">학문의 관문</h2>
              <svg className="slp-title-divider" aria-hidden="true"><use href="#slpTitleDivider"/></svg>
              <ol className="slp-lessons">
                {concepts.map((concept, index) => {
                  const isActive = currentQuestion?.concept_id === concept.concept_id;
                  const isPassed = state.current_index > index;
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
            </section>

            <section className="slp-panel slp-panel--journey" aria-labelledby="journey-title">
              <SlpCorners/>
              <h2 className="slp-panel-title slp-panel-title--journey" id="journey-title">오늘의 여정</h2>
              <div className="slp-progress-head">
                <span>완료한 관문</span>
                <strong>{Math.min(state.current_index, state.total_questions)} / {state.total_questions}</strong>
              </div>
              <div className="slp-progress-track" aria-label={`진행률 ${progress}%`}>
                <span className="slp-progress-fill" style={{ width: `${progress}%` }}/>
              </div>
              <dl className="slp-stats">
                <div className="slp-stat-row">
                  <dt>질문 수</dt>
                  <dd>{state.total_questions}</dd>
                </div>
                <div className="slp-stat-row"><dt>응답 수</dt><dd>{answers.length}</dd></div>
              </dl>
            </section>
          </div>
        </div>

        <div className="study-main">
          <div style={{ display: "flex", justifyContent: "center", paddingTop: 8 }}>
            <div className="ssb-component">
              <div className="ssb-speech">
                <div className="ssb-speech-name"><span>소크라테스</span></div>
                <div className="ssb-speech-bubble">
                  {showEvaluationMessage ? (
                    <p className="ssb-speech-text">
                      <strong style={{ display: "block", marginBottom: 6 }}>
                        {Math.round(lastAnswer.evaluation.score * 100)}점 · {statusLabel(lastAnswer.evaluation.status)}
                      </strong>
                      {lastAnswer.evaluation.feedback_to_student}
                    </p>
                  ) : (
                    <p className="ssb-speech-text">{questionText}</p>
                  )}
                  <SsbBC cls="ssb-bc"/><SsbBC cls="ssb-bc ssb-bc--tr"/>
                  <SsbBC cls="ssb-bc ssb-bc--bl"/><SsbBC cls="ssb-bc ssb-bc--br"/>
                </div>
              </div>
            </div>
          </div>

          {showTransitionEvaluation && (
            <div style={{ display: "flex", justifyContent: "center" }}>
              <button
                type="button"
                className="srp-submit-button"
                style={{ maxWidth: 260, marginTop: 8 }}
                onClick={() => onDismissTransition(lastAnswer.answer_id)}
              >
                <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true">
                  <use href="#srpSubmitFrame"/>
                </svg>
                <span>{state.completed ? "기록서 보기" : "다음 질문으로"}</span>
              </button>
            </div>
          )}

          {adviceText && (
            <div style={{ display: "flex", justifyContent: "center", paddingBottom: 8 }}>
              <div className="adv-wrap">
                <div className="adv-label">소크라테스의 조언</div>
                <div className="adv-text">{adviceText}</div>
              </div>
            </div>
          )}
        </div>

        <div className="srp-component">
          <div className="srp-right-stack">
            <section className="srp-card srp-card--answer" aria-labelledby="answer-card-title">
              <SrpCorners/>
              <div className="srp-card-content">
                {!state.completed && currentQuestion && !showTransitionEvaluation && (
                  <form onSubmit={onSubmitAnswer}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                      <h2 className="srp-answer-title" id="answer-card-title">그대의 답변을 입력하세요.</h2>
                      <span className="attempt-badge">시도 {visibleAttemptCount} / {MAX_ATTEMPTS_PER_QUESTION}</span>
                    </div>
                    <svg className="srp-divider" viewBox="0 0 360 14" preserveAspectRatio="none" aria-hidden="true"><use href="#srpDivider"/></svg>
                    <p className="srp-answer-copy">완벽하지 않아도 괜찮습니다.<br/>생각을 드러내는 것이 먼저입니다.</p>
                    <label className="srp-textarea-shell">
                      <span className="visually-hidden">답변 입력</span>
                      <textarea
                        className="srp-textarea"
                        value={answer}
                        onChange={(e) => onAnswerChange(e.target.value)}
                        placeholder="여기에 답변을 입력하세요..."
                      />
                      <svg className="srp-input-frame" viewBox="0 0 360 112" preserveAspectRatio="none" aria-hidden="true"><use href="#srpInputFrame"/></svg>
                    </label>
                    <div className="srp-shortcuts">
                      <button type="button" className="srp-shortcut" disabled={busy} onClick={() => onPostAction("skip")}><strong>/skip</strong><span>건너뛰기</span></button>
                      <button type="button" className="srp-shortcut" disabled={busy} onClick={() => onPostAction("finish")}><strong>/quit</strong><span>종료</span></button>
                    </div>
                    <button className="srp-submit-button" type="submit" disabled={busy || !answer.trim()}>
                      <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
                      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {busy ? <Loader2 className="spin" size={18}/> : <Send size={18}/>}
                        답변 제출
                      </span>
                    </button>
                  </form>
                )}

                {showTransitionEvaluation && (() => {
                  const answeredQuestion = state?.session?.questions?.find(
                    (question) => question.question_id === lastAnswer.question_id,
                  );
                  if (!answeredQuestion) return null;
                  return (
                    <div>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                        <h2 className="srp-answer-title">이전 답변 평가</h2>
                        <span className="attempt-badge">시도 {visibleAttemptCount} / {MAX_ATTEMPTS_PER_QUESTION}</span>
                      </div>
                      <svg className="srp-divider" viewBox="0 0 360 14" preserveAspectRatio="none" aria-hidden="true"><use href="#srpDivider"/></svg>
                      <div style={{ marginTop: 8, padding: "8px 10px", background: "rgba(0,0,0,0.06)", borderRadius: 4, borderLeft: "2px solid rgba(99,75,42,.4)" }}>
                        <p style={{ margin: "0 0 4px", color: "#5b4020", fontSize: 14, fontWeight: 760, letterSpacing: "0.04em" }}>질문</p>
                        <p style={{ margin: 0, color: "#3a260f", fontSize: 16, lineHeight: 1.58, fontWeight: 620 }}>{answeredQuestion.question}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </section>
          </div>
        </div>
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
