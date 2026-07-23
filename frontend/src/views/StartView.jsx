import { FileCheck2, FileText, Landmark, Loader2, ShieldCheck, Upload } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

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

  return (
    <ScreenShell
      className="start-bg"
      topBar={
        <TopBar
          audioSettings={audioSettings}
          onAcademy={onBack}
          academyLabel={isWeekMode ? "로드맵으로" : "메인으로"}
        />
      }
    >
      <div className="syl-shell">
        <div className="syl-main">
          <header className="syl-heading">
            <h1>{heading}</h1>
            <p>{subtitle}</p>
          </header>

          {!isWeekMode && (
            <img src="/theme-assets/guide.png" alt="업로드 가이드" className="syl-guide-image"/>
          )}

          <div className="syl-body">
            <section className="syl-card">
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
                    <img src="/theme-assets/basic_button.png" alt="" aria-hidden="true" className="syl-button-image"/>
                    <input type="file" accept="application/pdf,.pdf" onChange={onFileChange}/>
                    <span className="syl-button-content"><Upload size={16}/> PDF 업로드</span>
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

                <button className="srp-submit-button syl-submit syl-basic-button" disabled={busy || !file} type="submit">
                  <img src="/theme-assets/basic_button.png" alt="" aria-hidden="true" className="syl-button-image"/>
                  <span className="syl-button-content">
                    {busy ? <Loader2 className="spin" size={18}/> : null}
                    {submitLabel}
                  </span>
                </button>
              </form>
            </section>
          </div>
        </div>
      </div>
    </ScreenShell>
  );
}
