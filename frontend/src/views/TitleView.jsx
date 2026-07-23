import { Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function TitleView({ audioSettings, busy, error, onButtonHover, onContinue, onStartNew }) {
  return (
    <ScreenShell
      className="title-bg"
      topBar={<TopBar audioSettings={audioSettings}/>}
    >
      <div className="ttl-shell">
        <div className="ttl-card">
          <img src="/theme-assets/title.png" alt="소크라테스 문답법" className="ttl-title-image"/>
          {error && <div className="parch-error ttl-error">{error}</div>}
          <div className="ttl-actions">
            <button type="button" className="ttl-button" onPointerEnter={onButtonHover} onClick={onStartNew} disabled={busy}>
              <img src="/theme-assets/button.png" alt="" aria-hidden="true" className="ttl-button-image"/>
              <span className="ttl-button-content">
                {busy ? <Loader2 className="spin" size={17}/> : null}
                처음부터
              </span>
            </button>
            <button type="button" className="ttl-button" onPointerEnter={onButtonHover} onClick={onContinue} disabled={busy}>
              <img src="/theme-assets/button.png" alt="" aria-hidden="true" className="ttl-button-image"/>
              <span className="ttl-button-content">이어서</span>
            </button>
          </div>
        </div>
      </div>
    </ScreenShell>
  );
}
