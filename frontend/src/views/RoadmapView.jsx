import { AlertTriangle, Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

function stageStatus(stage, position, stages) {
  if (stage.completed) return "complete";
  const unlocked = position === 0 || stages[position - 1].completed;
  return unlocked ? "active" : "locked";
}

function stageIconMeta(stage, status, index, stages) {
  if (stage.kind === "checkpoint") {
    if (stage.checkpoint_type === "midterm") {
      return { src: "/theme-assets/roadmap_icon/midle_test.png", kind: "midle-test" };
    }
    return { src: "/theme-assets/roadmap_icon/final_test.png", kind: "final-test" };
  }
  if (status === "complete") return { src: "/theme-assets/roadmap_icon/check.png", kind: "check" };
  if (status === "locked") return { src: "/theme-assets/roadmap_icon/lock.png", kind: "lock" };
  if (status === "active") return { src: "/theme-assets/roadmap_icon/study.png", kind: "study" };
  if (index === stages.length - 1) return { src: "/theme-assets/roadmap_icon/fin.png", kind: "fin" };
  return { src: "/theme-assets/roadmap_icon/fin.png", kind: "fin" };
}

function stageBadgeLabel(stage, index) {
  return `${index + 1}주차`;
}

function getVisualLength(text) {
  return Array.from(text ?? "").reduce((length, char) => {
    if (char === " ") return length + 0.35;
    if (/[0-9]/.test(char)) return length + 0.72;
    if (/[A-Za-z]/.test(char)) return length + 0.78;
    return length + 1;
  }, 0);
}

function fitRoadmapText(text, { baseSize, minSize, threshold, shrinkStep, lineHeight, maxWidth }) {
  const visualLength = getVisualLength(text);
  const size = visualLength <= threshold
    ? baseSize
    : Math.max(minSize, baseSize - (visualLength - threshold) * shrinkStep);
  return {
    fontSize: `${size.toFixed(1)}px`,
    lineHeight,
    maxWidth,
    wordBreak: "keep-all",
    overflowWrap: "normal",
    hyphens: "none",
    whiteSpace: "normal",
  };
}

export function RoadmapView({
  audioSettings,
  busy,
  course,
  error,
  onBack,
  onActionStage,
  onUploadStagePdf,
  onOpenStage,
}) {
  const stages = course?.stages ?? [];
  const completed = stages.filter((stage) => stage.completed).length;
  const totalNodes = stages.length + 1;
  const progress = totalNodes ? Math.round(((completed + (completed >= stages.length && stages.length > 0 ? 1 : 0)) / totalNodes) * 100) : 0;
  const nextStage = stages.find((stage, index) => stageStatus(stage, index, stages) === "active");
  const ribbonLabel = nextStage ? nextStage.title : "학습 진행";
  const ribbonStyle = fitRoadmapText(ribbonLabel, {
    baseSize: 18,
    minSize: 12.5,
    threshold: 8,
    shrinkStep: 0.48,
    lineHeight: 1.16,
    maxWidth: "100%",
  });
  const rowCount = 3;
  const columnsPerRow = 7;

  function stagePosition(index) {
    const rowIndex = Math.floor(index / columnsPerRow);
    const colIndex = index % columnsPerRow;
    const rowLength = Math.min(columnsPerRow, totalNodes - rowIndex * columnsPerRow);
    const startSlot = Math.floor((columnsPerRow - rowLength) / 2);
    const slotIndex = startSlot + colIndex;
    const left = 12 + (slotIndex / (columnsPerRow - 1)) * 76;
    const top = rowCount <= 1 ? 56 : 34 + (Math.min(rowIndex, rowCount - 1) / (rowCount - 1)) * 46;
    return { left: `${left}%`, top: `${top}%` };
  }

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
        <section className="rmw-map-shell">
          {error && <div className="roadmap-error">{error}</div>}
          <div className="rmw-map">
            <img
              src="/theme-assets/roadmap.png"
              alt="학습 로드맵"
              className="rmw-map-image"
              draggable="false"
            />
            <div className="rmw-stage-layer" aria-label="학습 단계">
              {stages.map((stage, index) => {
                const status = stageStatus(stage, index, stages);
                const isCheckpoint = stage.kind === "checkpoint";
                const icon = stageIconMeta(stage, status, index, stages);
                const position = stagePosition(index);
                const stageTitleStyle = fitRoadmapText(stage.title, {
                  baseSize: 13.5,
                  minSize: 10.8,
                  threshold: 5,
                  shrinkStep: 0.35,
                  lineHeight: 1.22,
                  maxWidth: "120px",
                });
                const stageDetail = stage.kind === "week" ? (stage.document_title ?? "강의 PDF 등록") : "종합 리뷰";
                const stageDetailStyle = fitRoadmapText(stageDetail, {
                  baseSize: 11.5,
                  minSize: 8.6,
                  threshold: 8,
                  shrinkStep: 0.24,
                  lineHeight: 1.18,
                  maxWidth: "120px",
                });
                return (
                  <button
                    type="button"
                    key={stage.stage_index}
                    className={`rmw-node-wrap ${isCheckpoint ? "rmw-node-wrap--checkpoint" : ""}`}
                    style={position}
                    title={`${stage.title} · ${stageDetail}`}
                    disabled={status === "locked" || busy || !stage.session_id}
                    onClick={() => onOpenStage(stage)}
                  >
                    <span className="rmw-node-badge">{stageBadgeLabel(stage, index, stages)}</span>
                    <span className={`rmw-node is-${status} ${isCheckpoint ? "rmw-node--checkpoint" : ""}`}>
                      {busy && stage.stage_index === nextStage?.stage_index
                        ? <Loader2 className="spin"/>
                        : (
                          <img
                            src={icon.src}
                            alt=""
                            aria-hidden="true"
                            className={`rmw-node-image rmw-node-image--${icon.kind}`}
                            draggable="false"
                          />
                        )}
                    </span>
                    {stage.kind === "week" && <strong style={stageTitleStyle}>{stage.title}</strong>}
                    {stage.kind === "week" && <span style={stageDetailStyle}>{stageDetail}</span>}
                  </button>
                );
              })}
              <div
                className="rmw-node-wrap rmw-node-wrap--flag"
                style={stagePosition(stages.length)}
                aria-hidden="true"
                >
                <span className="rmw-node-badge">완료</span>
                <span className="rmw-node is-complete">
                  <img
                    src="/theme-assets/roadmap_icon/fin.png"
                    alt=""
                    aria-hidden="true"
                    className="rmw-node-image rmw-node-image--fin"
                    draggable="false"
                  />
                </span>
                <strong>강의 완료</strong>
              </div>
            </div>
          </div>
        </section>

        <aside className="rmw-side">
          <div className="slp-panel slp-panel--lessons rmw-context">
            <div className="parch-stage-ribbon parch-stage-ribbon--right" title={ribbonLabel}>
              <span style={ribbonStyle}>{ribbonLabel}</span>
            </div>
            {nextStage ? (
              nextStage.kind === "week" ? (
                <>
                  <p className="parch-upload-title">지식의 두루마리를 제출하세요</p>
                  <p className="parch-upload-desc">
                    공부할 강의 PDF를 제출하면 소크라테스가 두루마리를 해석하여 핵심 개념을 찾아냅니다.
                  </p>
                  <button type="button" className="srp-submit-button srp-submit-button--basic" disabled={busy} onClick={() => onUploadStagePdf(nextStage)}>
                    <span>PDF 업로드하러 가기</span>
                  </button>
                </>
              ) : (
                <>
                  <p className="parch-upload-title">{nextStage.checkpoint_type === "midterm" ? "중간고사가 다가왔습니다" : "기말고사가 다가왔습니다"}</p>
                  <p className="parch-upload-desc">
                    지금까지 배운 개념들을 스스로의 언어로 다시 설명하며 이해를 점검합니다.
                  </p>
                  <button type="button" className="srp-submit-button srp-submit-button--basic" disabled={busy} onClick={() => onActionStage(nextStage)}>
                    <span>시작하기</span>
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
