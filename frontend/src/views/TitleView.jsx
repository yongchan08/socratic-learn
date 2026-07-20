import { Landmark, Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function TitleView({ audioSettings, busy, error, onContinue, onStartNew }) {
  return (
    <ScreenShell
      className="title-bg"
      topBar={<TopBar audioSettings={audioSettings}/>}
    >
      <div className="ttl-shell">
        <div className="ttl-card">
          <div className="ttl-emblem"><Landmark size={34}/></div>
          <h1 className="ttl-title">소크라테스 문답법</h1>
          <p className="ttl-subtitle">질문을 통해 스스로 답에 이르는 학습 여정</p>
          {error && <div className="parch-error ttl-error">{error}</div>}
          <div className="ttl-actions">
            <button type="button" className="ttl-button" onClick={onStartNew} disabled={busy}>
              {busy ? <Loader2 className="spin" size={17}/> : null}
              처음부터
            </button>
            <button type="button" className="ttl-button" onClick={onContinue} disabled={busy}>
              이어서
            </button>
          </div>
        </div>
      </div>
    </ScreenShell>
  );
}
