import { Settings } from "lucide-react";

export function TopBar({ onAcademy, academyLabel = "학당", audioSettings, courseTitle, progressPercent }) {
  const showCourseBlock = Boolean(courseTitle) || typeof progressPercent === "number";
  return (
    <header className="slt-topbar" role="banner">
      <span className="slt-edge slt-edge--top" aria-hidden="true"/>
      <span className="slt-edge slt-edge--bottom" aria-hidden="true"/>
      <span className="slt-hairline slt-hairline--top" aria-hidden="true"/>
      <span className="slt-hairline slt-hairline--bottom" aria-hidden="true"/>
      {showCourseBlock && (
        <div className="slt-course" aria-label="현재 학습 진행 상태">
          {courseTitle && <span className="slt-course-title">{courseTitle}</span>}
          {typeof progressPercent === "number" && (
            <span className="slt-course-progress">
              <span className="slt-course-progress-track">
                <span className="slt-course-progress-fill" style={{ width: `${Math.max(0, Math.min(100, progressPercent))}%` }}/>
              </span>
              <span className="slt-course-progress-label">{Math.round(progressPercent)}%</span>
            </span>
          )}
        </div>
      )}
      <nav className="slt-nav" aria-label="상단 메뉴">
        {onAcademy && (
          <button type="button" className="slt-nav-button" onClick={onAcademy}>
            <svg className="slt-nav-icon" aria-hidden="true"><use href="#sltIconAcademy"/></svg>
            <span>{academyLabel}</span>
          </button>
        )}
        {audioSettings}
      </nav>
    </header>
  );
}

export function AudioSettings({
  isOpen, backgroundMusicVolume, questionSoundVolume,
  onToggle, onBackgroundMusicVolumeChange, onQuestionSoundVolumeChange,
}) {
  return (
    <div className="audio-settings">
      <button type="button" className="slt-nav-button audio-settings-toggle" onClick={onToggle} aria-expanded={isOpen} aria-label="음량 설정">
        <Settings size={15}/>
        <span>설정</span>
      </button>
      {isOpen && (
        <div className="audio-settings-panel">
          <label>
            배경음악
            <span>{Math.round(backgroundMusicVolume * 100)}</span>
            <input
              type="range" min="0" max="100"
              value={Math.round(backgroundMusicVolume * 100)}
              onChange={(e) => onBackgroundMusicVolumeChange(Number(e.target.value) / 100)}
            />
          </label>
          <label>
            효과음
            <span>{Math.round(questionSoundVolume * 100)}</span>
            <input
              type="range" min="0" max="100"
              value={Math.round(questionSoundVolume * 100)}
              onChange={(e) => onQuestionSoundVolumeChange(Number(e.target.value) / 100)}
            />
          </label>
        </div>
      )}
    </div>
  );
}
