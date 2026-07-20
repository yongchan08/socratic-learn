import { AlertTriangle, CheckCircle2, FileText, X } from "lucide-react";
import {
  formatStudySeconds,
  highlightsAndGaps,
  missedQuestionReview,
  perConceptUnderstanding,
} from "../lib/reportDerivation.js";

const CHIP_CLASS_BY_LABEL = {
  "완벽": "wrp-chip--perfect",
  "우수": "wrp-chip--good",
  "보통": "wrp-chip--fair",
  "복습 필요": "wrp-chip--weak",
};

function UnderstandingRing({ percent }) {
  const angle = Math.max(0, Math.min(100, percent)) * 3.6;
  return (
    <div
      className="wrp-ring"
      style={{ background: `conic-gradient(#3f9f5f ${angle}deg, rgba(63,74,44,.28) ${angle}deg)` }}
    >
      <span className="wrp-ring-inner">{percent}%</span>
    </div>
  );
}

export function WeekReportModal({ session, title, subtitle, studySeconds, onReturnToRoadmap }) {
  if (!session) return null;

  const concepts = perConceptUnderstanding(session);
  const missed = missedQuestionReview(session);
  const { highlights, gaps } = highlightsAndGaps(session);
  const completedAt = session.ended_at
    ? new Date(session.ended_at).toLocaleString("ko-KR", {
        year: "numeric", month: "2-digit", day: "2-digit", weekday: "short", hour: "2-digit", minute: "2-digit",
      })
    : null;

  return (
    <div className="wrp-overlay" role="dialog" aria-modal="true" aria-labelledby="wrp-title">
      <div className="wrp-modal">
        <button type="button" className="wrp-close" aria-label="닫기" onClick={onReturnToRoadmap}>
          <X size={18}/>
        </button>
        <div className="wrp-badge">{title ?? "학습 완료 리포트"}</div>
        <h2 id="wrp-title" className="wrp-heading">{subtitle ?? session.document_id ?? "학습 완료"}</h2>
        {completedAt && <p className="wrp-completed-at">학습 완료일: {completedAt}</p>}

        <div className="wrp-row wrp-row--top">
          <section className="wrp-panel">
            <h3 className="wrp-panel-title">핵심 개념 이해도</h3>
            <ul className="wrp-concept-list">
              {concepts.map((concept) => (
                <li key={concept.conceptId} className="wrp-concept-row">
                  <UnderstandingRing percent={concept.percent}/>
                  <div className="wrp-concept-text">
                    <strong>{concept.title}</strong>
                    <span>{concept.hasData ? `${concept.label} 이해했습니다.` : "아직 평가되지 않았습니다."}</span>
                  </div>
                  <span className={`wrp-chip ${CHIP_CLASS_BY_LABEL[concept.label] ?? ""}`}>{concept.label}</span>
                </li>
              ))}
              {concepts.length === 0 && <li className="wrp-muted">평가된 개념이 없습니다.</li>}
            </ul>
          </section>

          <section className="wrp-panel wrp-panel--verdict">
            <h3 className="wrp-panel-title">소크라테스 총평</h3>
            <div className="wrp-verdict-body">
              <img src="/theme-assets/socrates.png" alt="" className="wrp-verdict-portrait"/>
              <blockquote className="wrp-verdict-quote">
                {session.summary?.overall_feedback ?? "아직 총평이 준비되지 않았습니다."}
              </blockquote>
            </div>
          </section>
        </div>

        <div className="wrp-row">
          <section className="wrp-panel">
            <h3 className="wrp-panel-title">학습 하이라이트</h3>
            <ul className="wrp-bullet-list wrp-bullet-list--good">
              {highlights.slice(0, 5).map((point) => (
                <li key={point}><CheckCircle2 size={15}/><span>{point}</span></li>
              ))}
              {highlights.length === 0 && <li className="wrp-muted">기록된 하이라이트가 없습니다.</li>}
            </ul>
          </section>
          <section className="wrp-panel">
            <h3 className="wrp-panel-title">아쉬웠던 부분</h3>
            <ul className="wrp-bullet-list wrp-bullet-list--warn">
              {gaps.slice(0, 5).map((point) => (
                <li key={point}><AlertTriangle size={15}/><span>{point}</span></li>
              ))}
              {gaps.length === 0 && <li className="wrp-muted">기록된 아쉬운 점이 없습니다.</li>}
            </ul>
          </section>
        </div>

        {missed.length > 0 && (
          <section className="wrp-panel">
            <h3 className="wrp-panel-title">주요 오답 복기</h3>
            <ul className="wrp-review-list">
              {missed.map((item) => (
                <li key={item.questionId}>
                  <span>Q. {item.question}</span>
                  <span className={`wrp-tag wrp-tag--${item.tag === "미완료" ? "muted" : "hint"}`}>{item.tag}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="wrp-panel">
          <h3 className="wrp-panel-title">관련 자료 다시 보기</h3>
          <div className="wrp-materials">
            {concepts.map((concept) => (
              <div key={concept.conceptId} className="wrp-material-card">
                <FileText size={16}/>
                <div>
                  <strong>{concept.title}</strong>
                  {concept.sourcePages.length > 0 && (
                    <span>관련 페이지 (p.{Math.min(...concept.sourcePages)}~{Math.max(...concept.sourcePages)})</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {studySeconds != null && (
          <p className="wrp-muted wrp-time">이번 학습 소요 시간: {formatStudySeconds(studySeconds)}</p>
        )}

        <div className="wrp-actions">
          <button type="button" className="srp-submit-button" onClick={onReturnToRoadmap}>
            <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
            <span>로드맵으로 돌아가기</span>
          </button>
        </div>
      </div>
    </div>
  );
}
