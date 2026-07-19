import { BookOpen, Check, Flag, Landmark, Loader2, Lock } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function RoadmapView({
  audioSettings,
  busy,
  course,
  error,
  onBack,
  onStageOpen,
  onStartFinalReview,
  onSelectStage,
}) {
  const allStagesComplete = course?.stages?.every((stage) => stage.completed) ?? false;

  return (
    <ScreenShell
      className="roadmap-bg"
      topBar={<TopBar onAcademy={onBack} audioSettings={audioSettings}/>}
    >
      <main className="roadmap-shell">
        <section className="roadmap-scroll">
          <header className="roadmap-heading">
            <span>✦</span><h1>학습 로드맵</h1><span>✦</span>
            <p>각 단계의 강의 PDF를 학습하고 마지막 개념 리포트에 도전하세요.</p>
          </header>
          {error && <div className="roadmap-error">{error}</div>}
          <div className="roadmap-track">
            {(course?.stages ?? []).map((stage, index) => {
              const unlocked = index === 0 || course.stages[index - 1].completed;
              const active = unlocked && !stage.completed;
              return (
                <div className="roadmap-node-wrap" key={stage.stage_index}>
                  <button
                    type="button"
                    className={`roadmap-node ${stage.completed ? "is-complete" : active ? "is-active" : "is-locked"}`}
                    disabled={!unlocked || busy}
                    onClick={() => (stage.session_id ? onStageOpen(stage.session_id) : onSelectStage(stage))}
                  >
                    {stage.completed ? <Check/> : unlocked ? <BookOpen/> : <Lock/>}
                  </button>
                  <strong>{stage.stage_index}단계</strong>
                  <span>{stage.document_title ?? "강의 PDF 등록"}</span>
                </div>
              );
            })}
            <div className="roadmap-node-wrap roadmap-final-wrap">
              <button
                type="button"
                className={`roadmap-node roadmap-final ${allStagesComplete ? "is-active" : "is-locked"}`}
                disabled={!allStagesComplete || busy}
                onClick={onStartFinalReview}
              >
                {busy ? <Loader2 className="spin"/> : allStagesComplete ? <Flag/> : <Lock/>}
              </button>
              <strong>최종 단계</strong>
              <span>개념 리포트</span>
            </div>
          </div>
          <div className="roadmap-guide">
            <Landmark size={22}/>
            <p>앞 단계를 완료하면 다음 강의가 열립니다. 완료한 단계는 다시 확인할 수 있습니다.</p>
          </div>
        </section>
      </main>
    </ScreenShell>
  );
}
