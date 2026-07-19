import { Award, Brain, Hourglass, Landmark, Loader2, Map } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";
import { formatStudySeconds } from "../lib/reportDerivation.js";

export function CourseCompletionView({ audioSettings, busy, course, onReturnToRoadmap, summary }) {
  const weekCount = course?.week_count ?? summary?.progress?.total ?? 0;

  return (
    <ScreenShell
      className=""
      topBar={
        <TopBar
          audioSettings={audioSettings}
          courseTitle={course?.title}
          progressPercent={100}
          userLabel="지혜를 찾는 자"
        />
      }
    >
      <div className="ccv-shell">
        <div className="ccv-confetti" aria-hidden="true">
          {Array.from({ length: 18 }).map((_, index) => (
            <span key={index} className="ccv-confetti-piece" style={{ "--i": index }}/>
          ))}
        </div>

        <div className="ccv-card">
          <img src="/theme-assets/socrates.png" alt="" className="ccv-portrait"/>

          <div className="ccv-center">
            <div className="ccv-medal"><Award size={40}/></div>
            <h1 className="ccv-title">{weekCount ? `${weekCount}주 학습 완료!` : "학습 완료!"}</h1>
            <p className="ccv-subtitle">축하합니다.<br/>소크라테스와 함께한 학습 여정을 모두 마쳤습니다.</p>
            <div className="ccv-laurel" aria-hidden="true"><Landmark size={30}/></div>
            <blockquote className="ccv-quote">
              "그대는 끝까지 완주해냈군. 훌륭하네."
              <cite>— 소크라테스 —</cite>
            </blockquote>
          </div>

          <div className="ccv-stats">
            <div className="ccv-stat-card">
              <Landmark size={20}/>
              <strong>{summary ? `${summary.progress.completed} / ${summary.progress.total}` : "…"}</strong>
              <span>완료 단계</span>
              <small>모든 단계 완료!</small>
            </div>
            <div className="ccv-stat-card">
              <Hourglass size={20}/>
              <strong>{summary ? formatStudySeconds(summary.total_study_seconds) : "…"}</strong>
              <span>누적 학습 시간</span>
              <small>꾸준한 노력의 시간</small>
            </div>
            <div className="ccv-stat-card">
              <Brain size={20}/>
              <strong>{summary ? `${summary.concepts_understood_count}개` : "…"}</strong>
              <span>이해한 핵심 개념</span>
              <small>깊이 이해한 개념 수</small>
            </div>
          </div>
        </div>

        <button type="button" className="srp-submit-button ccv-return" onClick={onReturnToRoadmap} disabled={busy}>
          <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {busy ? <Loader2 className="spin" size={18}/> : <Map size={18}/>}
            로드맵으로 돌아가기
          </span>
        </button>
      </div>
    </ScreenShell>
  );
}
