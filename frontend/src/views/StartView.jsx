import { FileCheck2, FileText, Landmark, Loader2, ShieldCheck, Upload } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { SlpCorners } from "../components/Ornaments.jsx";
import { TopBar } from "../components/TopBar.jsx";

const GUIDE_STEPS = [
  { icon: <Landmark size={20}/>, title: "유세인트 접속", desc: "학교 포털이나 LMS에서 유세인트에 접속합니다." },
  { icon: <FileText size={20}/>, title: "강의계획서 열기", desc: "강의정보 메뉴에서 강의계획서를 엽니다." },
  { icon: <FileCheck2 size={20}/>, title: "PDF 저장", desc: "열린 페이지를 PDF로 저장하여 업로드 준비를 완료합니다." },
];

export function StartView({
  audioSettings,
  busy,
  error,
  file,
  loadingSteps,
  mode = "syllabus",
  selectedStage,
  onBack,
  onFileChange,
  onSubmit,
}) {
  const isWeekMode = mode === "week";
  const weekLabel = selectedStage?.title ?? `${selectedStage?.stage_index ?? 1}주차`;
  const heading = isWeekMode ? `${weekLabel} 강의 PDF를 올려주세요` : "강의계획서를 올려주세요";
  const subtitle = isWeekMode
    ? "이번 주차 강의 PDF를 분석하여 소크라테스 문답을 준비합니다."
    : "강의계획서를 분석하여 맞춤형 학습 로드맵을 만들어 드립니다.";
  const cardTitle = isWeekMode ? `${weekLabel} 강의 PDF를 업로드하세요` : "강의계획서 PDF를 업로드하세요";
  const submitLabel = isWeekMode ? "학습 시작" : "로드맵 생성";
  const submitNote = file
    ? (isWeekMode ? "클릭하여 학습을 시작하세요." : "클릭하여 로드맵 생성을 시작하세요.")
    : "분석이 완료되면 클릭할 수 있습니다.";

  return (
    <ScreenShell
      className=""
      topBar={
        <TopBar
          audioSettings={audioSettings}
          onAcademy={onBack}
          academyLabel={isWeekMode ? "로드맵으로" : "메인으로"}
          userLabel="지혜를 찾는 자"
        />
      }
    >
      <div className="syl-shell">
        <img src="/theme-assets/socrates-start-new.png" alt="AI 소크라테스" className="syl-portrait"/>

        <div className="syl-main">
          <header className="syl-heading">
            <span>⚜</span><h1>{heading}</h1><span>⚜</span>
            <p>{subtitle}</p>
          </header>

          {!isWeekMode && (
            <div className="syl-guide">
              <span className="syl-guide-label">업로드 가이드</span>
              {GUIDE_STEPS.map((step, index) => (
                <div className="syl-guide-step" key={step.title}>
                  {index > 0 && <span className="syl-guide-arrow" aria-hidden="true"/>}
                  <span className="syl-guide-icon">{step.icon}</span>
                  <div>
                    <strong>{index + 1} {step.title}</strong>
                    <p>{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="syl-body">
            <section className="slp-panel syl-card">
              <SlpCorners/>
              <h2 className="syl-card-title">{cardTitle}</h2>
              <p className="syl-card-desc">드래그&드롭 또는 버튼을 클릭하여 파일을 선택하세요.</p>
              {error && <div className="parch-error">{error}</div>}
              <form onSubmit={onSubmit}>
                <label className="syl-dropzone">
                  <input type="file" accept="application/pdf,.pdf" onChange={onFileChange}/>
                  <FileText size={40} className="syl-dropzone-icon"/>
                  <span>여기에 PDF 파일을 드롭하세요<br/>또는 아래 버튼을 클릭하세요.</span>
                </label>
                <div className="syl-upload-row">
                  <label className="syl-upload-button">
                    <input type="file" accept="application/pdf,.pdf" onChange={onFileChange}/>
                    <Upload size={16}/> PDF 업로드
                  </label>
                  <span className="syl-filename">{file?.name ?? ""}</span>
                </div>
                <p className="syl-safety-note"><ShieldCheck size={14}/> 파일은 안전하게 처리되며 저장되지 않습니다.</p>

                {busy && loadingSteps.length > 0 && (
                  <div className="loading-steps" aria-live="polite">
                    {loadingSteps.map((step, index) => (
                      <div
                        key={`${step.label}-${index}`}
                        className={`loading-step ${step.done ? "loading-step--done" : "loading-step--active"}`}
                      >
                        <span className="loading-step-icon">
                          {step.done ? "✅" : <Loader2 className="spin" size={13}/>}
                        </span>
                        <span className="loading-step-label">{step.label}</span>
                      </div>
                    ))}
                  </div>
                )}
                {busy && (
                  <div className="loading-reassurance" role="status" aria-live="polite">
                    📖 파일이 크면 시간이 걸릴 수 있어요. 소크라테스가 열심히 읽는 중이니 잠시만 기다려 주세요!
                  </div>
                )}

                <button className="srp-submit-button syl-submit" disabled={busy || !file} type="submit">
                  <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true">
                    <use href="#srpSubmitFrame"/>
                  </svg>
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    {busy ? <Loader2 className="spin" size={18}/> : <Landmark size={18}/>}
                    {submitLabel}
                  </span>
                </button>
                <p className="syl-submit-note">{submitNote}</p>
              </form>
            </section>
          </div>
        </div>
      </div>
    </ScreenShell>
  );
}
