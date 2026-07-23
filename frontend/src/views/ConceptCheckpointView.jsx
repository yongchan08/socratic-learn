import { Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";
import { WeekReportModal } from "../components/WeekReportModal.jsx";

const MAX_LENGTH_BY_VARIANT = { plain: 1000, feynman: 2000 };

function studySecondsFor(session) {
  if (!session?.started_at || !session?.ended_at) return null;
  const seconds = (new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 1000;
  return Number.isFinite(seconds) ? seconds : null;
}

export function ConceptCheckpointView({
  audioSettings,
  answer,
  busy,
  course,
  onAcademy,
  onAnswerChange,
  onSubmitAnswer,
  progress,
  stageTitle,
  state,
  variant = "plain",
}) {
  const concepts = state?.session?.concepts ?? [];
  const currentIndex = state?.current_index ?? 0;
  const total = state?.total_questions ?? concepts.length;
  const currentConcept = concepts[currentIndex];
  const maxLength = MAX_LENGTH_BY_VARIANT[variant] ?? 1000;
  const showReport = Boolean(state?.completed && state?.session?.summary);
  const questionTitle = currentConcept?.title ?? stageTitle ?? "질문을 불러오는 중입니다.";

  return (
    <>
      <ScreenShell
        className="study-bg concept-feynman-bg"
        topBar={
          <TopBar
            onAcademy={onAcademy}
            academyLabel="로드맵 보기"
            audioSettings={audioSettings}
            courseTitle={course?.title}
            progressPercent={progress}
          />
        }
      >
        <div className="study-layout">
          <aside className="slp-component study-sidebar">
            <div className="slp-sidebar">
              <section className="slp-panel slp-panel--lessons" aria-labelledby="gate-title">
                <h2 className="slp-panel-title" id="gate-title">{variant === "feynman" ? "회상할 개념 목록" : "점검 개념 목록"}</h2>
                <svg className="slp-title-divider" aria-hidden="true"><use href="#slpTitleDivider"/></svg>
                <ol className="slp-lessons">
                  {concepts.map((concept, index) => {
                    const status = index < currentIndex ? "done" : index === currentIndex ? "active" : "locked";
                    const iconHref = status === "done" ? "#slpCompass" : status === "active" ? "#slpChevron" : "#slpLock";
                    const iconCls = status === "done"
                      ? "slp-state-icon slp-state-icon--compass"
                      : status === "active"
                        ? "slp-state-icon slp-state-icon--chevron"
                        : "slp-state-icon slp-state-icon--lock";
                    return (
                      <li key={concept.concept_id} className="slp-lesson-item">
                        <button
                          className={`slp-lesson-button is-${status}`}
                          type="button"
                          disabled={status === "locked"}
                          aria-current={index === currentIndex ? "step" : undefined}
                        >
                          <span className="slp-lesson-number">{index + 1}</span>
                          <span className="slp-lesson-label">{status === "locked" && variant === "feynman" ? "" : concept.title}</span>
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
                  {total ? `${Math.min(currentIndex + 1, total)} / ${total}` : "0 / 0"}
                </div>
                <h2 className="study-paper-title">{questionTitle}</h2>
                <p className="study-paper-desc">
                  {variant === "feynman"
                    ? "이 개념을 어린 소크라테스에게 설명해 주세요."
                    : "아래 영역에 이 개념을 자신의 언어로 설명해보세요."}
                </p>

                {variant === "feynman" && !state?.completed && currentConcept && (
                  <div className="study-feedback">
                    <strong>{questionTitle}</strong>
                    <p>
                      이 개념이 무엇인지 다시 알려주실 수 있나요?
                    </p>
                  </div>
                )}

                {currentConcept && !state?.completed ? (
                  <form onSubmit={onSubmitAnswer}>
                    <label className="study-textarea-shell">
                      <span className="visually-hidden">답변 입력</span>
                      <textarea
                        className="study-textarea"
                        value={answer}
                        maxLength={maxLength}
                        onChange={(event) => onAnswerChange(event.target.value)}
                        placeholder={variant === "feynman" ? "여기에 개념을 직접 설명해 주세요..." : "여기에 당신의 설명을 입력하세요..."}
                      />
                    </label>
                    <div className="study-counter">{answer.length} / {maxLength}</div>
                    <div className="study-action-row">
                      <button className="study-basic-button" type="submit" disabled={busy || !answer.trim()}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                          {busy ? <Loader2 className="spin" size={18}/> : null}
                          {variant === "feynman" ? "기억 되살리기" : "제출하기"}
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
      {showReport && (
        <WeekReportModal
          session={state.session}
          title={stageTitle ?? (variant === "feynman" ? "중간고사 완료 리포트" : "기말고사 완료 리포트")}
          subtitle="학습 완료"
          studySeconds={studySecondsFor(state.session)}
          onReturnToRoadmap={onAcademy}
        />
      )}
    </>
  );
}
