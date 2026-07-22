import { Brain, GraduationCap, Loader2, MessageSquareText, Scroll, ShieldOff, User } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { SlpCorners } from "../components/Ornaments.jsx";
import { TopBar } from "../components/TopBar.jsx";

const FLOW_STEPS = [
  { icon: <User size={16}/>, label: "소크라테스가 어려짐" },
  { icon: <Scroll size={16}/>, label: "내가 설명하기" },
  { icon: <Brain size={16}/>, label: "기억 회복" },
  { icon: <GraduationCap size={16}/>, label: "최종 피드백" },
];

const RULES = [
  { icon: <ShieldOff size={18}/>, title: "힌트 없이 설명하기", desc: "힌트나 정답 확인 없이 스스로 설명해 주세요." },
  { icon: <User size={18}/>, title: "학생이 직접 선생님 역할", desc: "당신이 선생님이 되어 소크라테스에게 설명합니다." },
  { icon: <MessageSquareText size={18}/>, title: "여러 개념 설명 후 최종 피드백", desc: "모든 개념을 설명한 뒤 피드백을 받습니다." },
];

export function CheckpointIntroView({ audioSettings, busy, course, progress, onLater, onStart }) {
  return (
    <ScreenShell
      className=""
      topBar={
        <TopBar
          audioSettings={audioSettings}
          courseTitle={course?.title}
          progressPercent={progress}
        />
      }
    >
      <div className="ckp-shell">
        <section className="slp-panel ckp-card">
          <SlpCorners/>
          <header className="ckp-heading">
            <span>⚜</span><h1>앗! 소크라테스가 어려졌어요!</h1><span>⚜</span>
            <p>무언의 이슈로 소크라테스가 어린아이로 돌아가 버렸습니다.<br/>이제 그대가 선생님이 되어 기억을 되찾아 주세요.</p>
          </header>

          <div className="ckp-body">
            <ol className="ckp-flow">
              {FLOW_STEPS.map((step, index) => (
                <li key={step.label}>
                  <span className="ckp-flow-num">{index + 1}</span>
                  <span className="ckp-flow-icon">{step.icon}</span>
                  <span>{step.label}</span>
                </li>
              ))}
            </ol>

            <div className="ckp-child">
              <div className="ckp-child-portrait" aria-hidden="true">👦</div>
              <div className="ckp-child-bubble">
                음… 아무것도 기억이 나지 않아요.<br/>선생님, 다시 알려주실 수 있나요?
              </div>
              <span className="ckp-child-event">이벤트 발생! 파인만 회상 세션 오픈</span>
            </div>

            <ul className="ckp-rules">
              {RULES.map((rule) => (
                <li key={rule.title}>
                  <span className="ckp-rule-icon">{rule.icon}</span>
                  <div>
                    <strong>{rule.title}</strong>
                    <p>{rule.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="ckp-actions">
            <button type="button" className="ckp-later" onClick={onLater} disabled={busy}>나중에 하기</button>
            <button type="button" className="srp-submit-button" onClick={onStart} disabled={busy}>
              <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {busy ? <Loader2 className="spin" size={18}/> : <Brain size={18}/>}
                기억 되찾기 시작
              </span>
            </button>
          </div>
        </section>
      </div>
    </ScreenShell>
  );
}
