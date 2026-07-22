import { AlertTriangle, BookOpen, Check, FileUp, Flag, GraduationCap, Loader2, Lock } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

function stageStatus(stage, position, stages) {
  if (stage.completed) return "complete";
  const unlocked = position === 0 || stages[position - 1].completed;
  return unlocked ? "active" : "locked";
}

function StageIcon({ stage, status }) {
  if (status === "complete") return <Check/>;
  if (status === "locked") return <Lock/>;
  if (stage.kind === "checkpoint") return <GraduationCap/>;
  return <BookOpen/>;
}

export function RoadmapView({
  audioSettings,
  busy,
  course,
  error,
  onBack,
  onOpenStage,
}) {
  const stages = course?.stages ?? [];
  const completed = stages.filter((stage) => stage.completed).length;
  const progress = stages.length ? Math.round((completed / stages.length) * 100) : 0;
  const nextStage = stages.find((stage, index) => stageStatus(stage, index, stages) === "active");

  return (
    <ScreenShell
      className="roadmap-bg"
      topBar={
        <TopBar
          onAcademy={onBack}
          academyLabel="로드맵 목록"
          audioSettings={audioSettings}
          courseTitle={course?.title}
          progressPercent={progress}
        />
      }
    >
      <main className="rmw-shell">
        <section className="rmw-scroll">
          <header className="roadmap-heading">
            <span>✦</span><h1>학습 로드맵</h1><span>✦</span>
            <p>매주 학습을 완수하고 지혜의 길을 완성해 나가세요.</p>
          </header>
          {error && <div className="roadmap-error">{error}</div>}
          <div className="rmw-track">
            {stages.map((stage, index) => {
              const status = stageStatus(stage, index, stages);
              const isCheckpoint = stage.kind === "checkpoint";
              return (
                <button
                  type="button"
                  key={stage.stage_index}
                  className={`rmw-node-wrap ${isCheckpoint ? "rmw-node-wrap--checkpoint" : ""}`}
                  disabled={status === "locked" || busy}
                  onClick={() => onOpenStage(stage)}
                >
                  <span className={`rmw-node is-${status} ${isCheckpoint ? "rmw-node--checkpoint" : ""}`}>
                    {busy && stage.stage_index === nextStage?.stage_index
                      ? <Loader2 className="spin"/>
                      : <StageIcon stage={stage} status={status}/>}
                  </span>
                  <strong>{stage.title}</strong>
                  <span>{stage.kind === "week" ? (stage.document_title ?? "강의 PDF 등록") : "종합 리뷰"}</span>
                </button>
              );
            })}
            <div className="rmw-node-wrap rmw-node-wrap--flag">
              <span className={`rmw-node ${completed >= stages.length && stages.length > 0 ? "is-complete" : "is-locked"}`}>
                <Flag/>
              </span>
              <strong>강의 완료</strong>
              <span>축하합니다!</span>
            </div>
          </div>
        </section>

        <aside className="rmw-side">
          <div className="slp-panel slp-panel--lessons rmw-context">
            <div className="parch-stage-ribbon parch-stage-ribbon--right">
              {nextStage ? (nextStage.kind === "checkpoint" ? `${nextStage.title}` : `${nextStage.title}`) : "학습 진행"}
            </div>
            {nextStage ? (
              nextStage.kind === "week" ? (
                <>
                  <p className="parch-upload-title">지식의 두루마리를 제출하세요</p>
                  <p className="parch-upload-desc">
                    공부할 강의 PDF를 제출하면 소크라테스가 두루마리를 해석하여 핵심 개념을 찾아냅니다.
                  </p>
                  <button type="button" className="srp-submit-button" disabled={busy} onClick={() => onOpenStage(nextStage)}>
                    <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
                    <span style={{ display: "flex", alignItems: "center", gap: 8 }}><FileUp size={17}/> PDF 업로드하러 가기</span>
                  </button>
                </>
              ) : (
                <>
                  <p className="parch-upload-title">{nextStage.checkpoint_type === "midterm" ? "중간고사가 다가왔습니다" : "기말고사가 다가왔습니다"}</p>
                  <p className="parch-upload-desc">
                    지금까지 배운 개념들을 스스로의 언어로 다시 설명하며 이해를 점검합니다.
                  </p>
                  <button type="button" className="srp-submit-button" disabled={busy} onClick={() => onOpenStage(nextStage)}>
                    <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
                    <span style={{ display: "flex", alignItems: "center", gap: 8 }}><GraduationCap size={17}/> 시작하기</span>
                  </button>
                </>
              )
            ) : (
              <p className="parch-upload-desc">모든 단계를 완료했습니다.</p>
            )}
          </div>
          <div className="roadmap-guide">
            <AlertTriangle size={20}/>
            <p>앞 단계를 완료하면 다음 단계가 열립니다. 완료한 단계는 다시 확인할 수 있습니다.</p>
          </div>
        </aside>
      </main>
    </ScreenShell>
  );
}
