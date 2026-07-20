import { HelpCircle, Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { SlpCorners, SrpCorners } from "../components/Ornaments.jsx";
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
  const showReport = state.completed && Boolean(state.session.summary);

  return (
    <>
    <ScreenShell
      className=""
      topBar={
        <TopBar
          onAcademy={onAcademy}
          academyLabel="로드맵 보기"
          audioSettings={audioSettings}
          courseTitle={course?.title}
          progressPercent={progress}
          userLabel="지혜를 찾는 자"
        />
      }
    >
      <div className="ccp-shell">
        <aside className="slp-panel slp-panel--lessons ccp-sidebar">
          <SlpCorners/>
          <h2 className="slp-panel-title">{variant === "feynman" ? "회상할 개념 목록" : "점검 개념 목록"}</h2>
          <svg className="slp-title-divider" aria-hidden="true"><use href="#slpTitleDivider"/></svg>
          <div className="ccp-progress-head">
            <span>전체 진행률</span>
            <strong>{Math.min(currentIndex, total)} / {total}</strong>
          </div>
          <div className="slp-progress-track">
            <span className="slp-progress-fill" style={{ width: `${total ? Math.min(100, (currentIndex / total) * 100) : 0}%` }}/>
          </div>
          <ol className="ccp-concept-list">
            {concepts.map((concept, index) => {
              const status = index < currentIndex ? "done" : index === currentIndex ? "active" : "locked";
              const label = variant === "feynman"
                ? { done: "설명 완료", active: "설명 중", locked: "미설명" }[status]
                : { done: "완료", active: "진행 중", locked: "대기 중" }[status];
              return (
                <li key={concept.concept_id} className={`ccp-concept-row is-${status}`}>
                  <span className="ccp-concept-num">{index + 1}</span>
                  <span className="ccp-concept-title">{status === "locked" && variant === "feynman" ? "" : concept.title}</span>
                  <span className="ccp-concept-status">{label}</span>
                </li>
              );
            })}
          </ol>
          <blockquote className="ccp-quote">
            "설명할 때에야 진짜로 아는 것이다."
            <cite>— 소크라테스</cite>
          </blockquote>
        </aside>

        <div className="ccp-main">
          <section className="srp-card srp-card--answer ccp-card">
            <SrpCorners/>
            <div className="srp-card-content">
              {currentConcept && !state.completed && (
                <>
                  {variant === "feynman" ? (
                    <div className="ccp-child-row">
                      <span className="ccp-child-portrait" aria-hidden="true">👦</span>
                      <div className="ccp-child-bubble">
                        음… 머릿속이 하얘요.<br/>선생님, <strong>{currentConcept.title}</strong>이(가) 무엇인지 다시 알려주실 수 있나요?
                        <HelpCircle size={16} className="ccp-child-help"/>
                      </div>
                    </div>
                  ) : (
                    <div className="ccp-badge-row">
                      <span className="ccp-badge">{currentIndex + 1} / {total}</span>
                    </div>
                  )}

                  <p className="ccp-eyebrow">{variant === "feynman" ? "이 개념을 어린 소크라테스에게 설명해 주세요" : "지금 설명할 개념"}</p>
                  <h2 className="ccp-question">{variant === "feynman" ? "" : currentConcept.title}</h2>
                  <p className="ccp-hint">
                    {variant === "feynman"
                      ? "교과서가 아닌, 당신의 언어로 쉽게! 비유와 예시를 사용해도 좋아요."
                      : "아래 영역에 이 개념을 자신의 언어로 설명해보세요."}
                  </p>

                  <form onSubmit={onSubmitAnswer}>
                    <label className="srp-textarea-shell">
                      <span className="visually-hidden">답변 입력</span>
                      <textarea
                        className="srp-textarea"
                        value={answer}
                        maxLength={maxLength}
                        onChange={(event) => onAnswerChange(event.target.value)}
                        placeholder={variant === "feynman" ? "여기에 개념을 직접 설명해 주세요..." : "여기에 당신의 설명을 입력하세요..."}
                      />
                      <svg className="srp-input-frame" viewBox="0 0 360 112" preserveAspectRatio="none" aria-hidden="true"><use href="#srpInputFrame"/></svg>
                    </label>
                    <div className="ccp-counter">{answer.length} / {maxLength}</div>
                    <button className="srp-submit-button" type="submit" disabled={busy || !answer.trim()}>
                      <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
                      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {busy ? <Loader2 className="spin" size={18}/> : null}
                        {variant === "feynman" ? "기억 되살리기" : "제출하기"}
                      </span>
                    </button>
                    <p className="ccp-submit-note">
                      {variant === "feynman" ? "설명을 입력한 후 버튼을 눌러주세요" : "제출 후 바꿀 수 없습니다."}
                    </p>
                  </form>

                  {variant !== "feynman" && (
                    <div className="ccp-eval-row">
                      <span>평가 결과</span>
                      <span className="ccp-eval-pending"><HelpCircle size={14}/> 미확인</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>

          {variant === "feynman" && !state.completed && (
            <div className="ccp-no-hint-banner">
              <span>⏳ 이번 세션에서는 힌트 없이 설명합니다</span>
              <p>스스로의 언어로 설명해야 어린 소크라테스의 기억이 되살아납니다.</p>
            </div>
          )}
        </div>
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
