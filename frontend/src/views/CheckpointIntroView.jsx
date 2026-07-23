import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function CheckpointIntroView({ audioSettings, busy, course, progress, onAcademy, onStart, onStartHover }) {
  return (
    <ScreenShell
      className="ckp-clean-shell"
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
      <div className="ckp-clean">
        <img
          src="/theme-assets/feynman_session.png"
          alt="feynman_session"
          className="ckp-clean-image"
        />
        <div className="ckp-clean-actions">
          <button type="button" className="ckp-start-button" onPointerEnter={onStartHover} onClick={onStart} disabled={busy}>
            <span>기억 되찾기 시작</span>
          </button>
        </div>
      </div>
    </ScreenShell>
  );
}
