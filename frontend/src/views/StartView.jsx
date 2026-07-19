import { BookOpen, FileUp, Landmark, Loader2, Scroll, Search } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { SlpCorners } from "../components/Ornaments.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function StartView({
  audioSettings,
  busy,
  error,
  file,
  form,
  loadingSteps,
  onDifficultyChange,
  onFileChange,
  onSubmit,
  selectedStage,
}) {
  return (
    <ScreenShell
      className=""
      topBar={<TopBar audioSettings={audioSettings}/>}
      backgroundContent={
        <div className="start-socrates-abs">
          <img src="/theme-assets/socrates-start-new.png" alt="AI 소크라테스"/>
        </div>
      }
    >
      <div className="start-body">
        <section className="slp-panel slp-panel--upload" aria-label="학습 시작">
          <SlpCorners/>
          <div className="slp-upload-scroll-area" style={{ position: "relative", zIndex: 5 }}>
            <div className="parch-stage-ribbon">{selectedStage?.stage_index ?? 1}단계: 강의 등록</div>
            <p className="parch-upload-title">지식의 두루마리를 제출하세요</p>
            <p className="parch-upload-desc">
              공부할 강의 PDF를 제출하면 소크라테스가 두루마리를 해석하여 핵심 개념을 찾아냅니다.
            </p>
            {error && <div className="parch-error">{error}</div>}
            <form onSubmit={onSubmit} className="parch-form">
              <label className="parch-dropzone">
                <input type="file" accept="application/pdf,.pdf" onChange={onFileChange}/>
                <FileUp size={24} style={{ opacity: 0.7 }}/>
                <span>{file ? file.name : "강의 PDF 선택"}</span>
              </label>
              <div className="parch-upload-hint">
                여기에 PDF 파일을 드래그하거나 클릭하여 업로드하세요.
              </div>
              <div className="parch-segmented" aria-label="난이도">
                {["easy", "normal", "hard"].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={form.difficulty === value ? "active" : ""}
                    onClick={() => onDifficultyChange(value)}
                  >
                    {value}
                  </button>
                ))}
              </div>
              <div className="parch-setting-strip" aria-label="학습 설정 요약">
                <span>개념 추출</span>
                <span>질문 생성</span>
                <span>기록 저장</span>
              </div>
              <button className="srp-submit-button" disabled={busy} type="submit">
                <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true">
                  <use href="#srpSubmitFrame"/>
                </svg>
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  {busy ? <Loader2 className="spin" size={18}/> : <BookOpen size={18}/>}
                  분석 시작
                </span>
              </button>
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
            </form>
            {busy ? (
              <div className="loading-reassurance" role="status" aria-live="polite">
                📖 파일이 크면 시간이 걸릴 수 있어요. 소크라테스가 열심히 읽는 중이니 잠시만 기다려 주세요!
              </div>
            ) : (
              <div className="parch-notice">
                텍스트가 포함된 PDF 파일만 지원됩니다. 스캔 이미지 PDF는 분석이 어려울 수 있습니다.
              </div>
            )}
          </div>
        </section>

        <div className="start-center"/>

        <aside className="start-info">
          <section className="slp-panel slp-panel--lessons">
            <SlpCorners/>
            <div className="parch-stage-ribbon parch-stage-ribbon--right">학습 여정 안내</div>
            <svg className="slp-title-divider" aria-hidden="true"><use href="#slpTitleDivider"/></svg>
            <ul className="journey-step-list">
              <li className="journey-step-item">
                <span className="journey-step-icon"><Landmark size={16}/></span>
                <div>
                  <p className="journey-step-title">입문</p>
                  <p className="journey-step-desc">지식의 두루마리를 제출하고 학습 여정을 시작합니다.</p>
                </div>
              </li>
              <li className="journey-step-item">
                <span className="journey-step-icon"><Search size={16}/></span>
                <div>
                  <p className="journey-step-title">해석</p>
                  <p className="journey-step-desc">소크라테스가 핵심 개념과 학문의 관문을 찾아냅니다.</p>
                </div>
              </li>
              <li className="journey-step-item">
                <span className="journey-step-icon"><BookOpen size={16}/></span>
                <div>
                  <p className="journey-step-title">문답</p>
                  <p className="journey-step-desc">각 관문에서 질문에 답하며 개념을 자신의 것으로 만듭니다.</p>
                </div>
              </li>
              <li className="journey-step-item">
                <span className="journey-step-icon"><Scroll size={16}/></span>
                <div>
                  <p className="journey-step-title">기록</p>
                  <p className="journey-step-desc">학습이 끝나면 철학자의 기록으로 복습 방향을 확인합니다.</p>
                </div>
              </li>
            </ul>
          </section>

          <blockquote className="quote-block">
            <span className="quote-medallion" aria-hidden="true">
              <img src="/theme-assets/medallion.png" alt=""/>
            </span>
            <p>"답을 아는 것이 지혜가 아니라, 올바른 질문을 하는 것이 지혜의 시작이라네."</p>
            <cite>소크라테스</cite>
          </blockquote>
        </aside>
      </div>
    </ScreenShell>
  );
}
