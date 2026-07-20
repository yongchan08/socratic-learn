import { useState } from "react";
import { ArrowLeft, Landmark, Loader2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

function currentStageLabel(course) {
  const stages = course.stages ?? [];
  const active = stages.find((stage) => !stage.completed) ?? stages[stages.length - 1];
  if (!active) return "학습 대기 중";
  const label = active.kind === "week" ? (active.document_title ?? active.title) : active.title;
  return `${active.title} · ${label}`;
}

function progressLabel(course) {
  const stages = course.stages ?? [];
  const completed = stages.filter((stage) => stage.completed).length;
  return { completed, total: stages.length };
}

export function ContinueCourseView({ audioSettings, busy, courses, error, onBack, onOpenCourse }) {
  const [selectedId, setSelectedId] = useState(courses[0]?.course_id ?? null);
  const selectedCourse = courses.find((course) => course.course_id === selectedId) ?? courses[0] ?? null;

  return (
    <ScreenShell
      className="continue-bg"
      topBar={<TopBar audioSettings={audioSettings} userLabel="지혜를 찾는 자"/>}
    >
      <main className="ctn-shell">
        <section className="ctn-card">
          <header className="ctn-heading">
            <Landmark size={18}/>
            <h1>이어서 학습할 과목을 선택해 주세요</h1>
          </header>
          <p className="ctn-desc">이전 학습을 이어서 진행하거나 새로운 여정을 시작할 수 있습니다.</p>
          {error && <div className="roadmap-error">{error}</div>}

          <ul className="ctn-list">
            {courses.map((course, index) => {
              const { completed, total } = progressLabel(course);
              const percent = total ? Math.round((completed / total) * 100) : 0;
              const date = new Date(course.updated_at ?? course.created_at).toLocaleString("ko-KR", {
                year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
              });
              return (
                <li key={course.course_id}>
                  <button
                    type="button"
                    className={`ctn-row ${course.course_id === selectedCourse?.course_id ? "is-selected" : ""}`}
                    onClick={() => setSelectedId(course.course_id)}
                  >
                    <span className="ctn-row-num">{index + 1}</span>
                    <span className="ctn-row-body">
                      <span className="ctn-row-top">
                        <strong>{course.title}</strong>
                        <span className="ctn-row-date">{date}</span>
                      </span>
                      <span className="ctn-row-stage">{currentStageLabel(course)}</span>
                      <span className="ctn-row-progress">
                        <span className="ctn-row-progress-track">
                          <span className="ctn-row-progress-fill" style={{ width: `${percent}%` }}/>
                        </span>
                        <small>진행 상태 · {completed}/{total} 완료</small>
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
            {courses.length === 0 && <li className="ctn-empty">아직 생성된 학습 로드맵이 없습니다.</li>}
          </ul>

          <div className="ctn-actions">
            <button type="button" className="ttl-button ctn-back" onClick={onBack}>
              <ArrowLeft size={16}/> 뒤로가기
            </button>
            <button
              type="button"
              className="srp-submit-button"
              disabled={!selectedCourse || busy}
              onClick={() => onOpenCourse(selectedCourse)}
            >
              <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {busy ? <Loader2 className="spin" size={18}/> : <Landmark size={18}/>}
                로드맵 열기
              </span>
            </button>
          </div>
        </section>
      </main>
    </ScreenShell>
  );
}
