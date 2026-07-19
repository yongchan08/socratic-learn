import { BookOpen, Loader2, Plus, Trash2 } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function LibraryView({
  audioSettings,
  courses,
  error,
  busy,
  onCreateCourse,
  onOpenCourse,
  onDeleteCourse,
}) {
  return (
    <ScreenShell
      className="library-bg"
      topBar={<TopBar audioSettings={audioSettings}/>}
    >
      <main className="library-shell">
        <header className="library-heading">
          <div><span>학당 서고</span><h1>나의 학습 로드맵</h1></div>
          <p>강의 묶음을 만들고 단계별 소크라테스 학습을 이어가세요.</p>
        </header>
        {error && <div className="roadmap-error library-error">{error}</div>}
        <section className="course-grid" aria-label="학습 로드맵 목록">
          <button type="button" className="course-card course-card-new" onClick={onCreateCourse} disabled={busy}>
            <span className="course-new-icon">{busy ? <Loader2 className="spin"/> : <Plus/>}</span>
            <strong>새 로드맵 만들기</strong>
            <small>3개의 강의 PDF로 학습 여정을 시작하세요.</small>
          </button>
          {courses.map((item, index) => {
            const completed = item.stages.filter((stage) => stage.completed).length;
            const documents = item.stages.filter((stage) => stage.document_title).length;
            const date = new Date(item.updated_at ?? item.created_at).toLocaleDateString("ko-KR");
            return (
              <article
                className={`course-card course-card-existing tone-${index % 4}`}
                key={item.course_id}
                onClick={() => onOpenCourse(item)}
              >
                <div className="course-card-top">
                  <span className="course-card-emblem">{["📜", "🏛️", "🦉", "⚡"][index % 4]}</span>
                  <button type="button" aria-label="로드맵 삭제" onClick={(event) => onDeleteCourse(event, item.course_id)}>
                    <Trash2/>
                  </button>
                </div>
                <h2>{item.title}</h2>
                <p>{date} · PDF {documents}개</p>
                <div className="course-card-progress"><span style={{ width: `${(completed / 3) * 100}%` }}/></div>
                <small>{completed}/3 단계 완료</small>
              </article>
            );
          })}
        </section>
      </main>
    </ScreenShell>
  );
}
