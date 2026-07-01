import { BookOpen, FileUp, Landmark, Loader2, Search, Send, Settings, ScrollText, Scroll } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const BACKGROUND_MUSIC_SRC = "/audio/background_music.mp3";
const QUESTION_CHANGE_SOUND_SRC = "/audio/page-turn.mp3";
const MAX_ATTEMPTS_PER_QUESTION = 3;

const SOCRATES_MOTIONS = {
  talking: {
    loop: true,
    repeat: 3,
    frames: [
      "/motion-assets/talking/frame-01.png",
      "/motion-assets/talking/frame-02.png",
      "/motion-assets/talking/frame-03.png",
      "/motion-assets/talking/frame-02.png",
    ],
  },
  correct: {
    loop: true,
    repeat: 3,
    frames: [
      "/motion-assets/correct/frame-00.png",
      "/motion-assets/correct/frame-01.png",
      "/motion-assets/correct/frame-02.png",
      "/motion-assets/correct/frame-03.png",
      "/motion-assets/correct/frame-04.png",
      "/motion-assets/correct/frame-05.png",
      "/motion-assets/correct/frame-06.png",
    ],
  },
  failure: {
    loop: true,
    repeat: 3,
    frames: [
      "/motion-assets/failure/frame-01.png",
      "/motion-assets/failure/frame-02.png",
      "/motion-assets/failure/frame-03.png",
    ],
  },
};

const initialForm = {
  subject: "",
  difficulty: "normal",
  outputLanguage: "ko",
  maxConcepts: 7,
  questionsPerConcept: 3,
  model: "",
};

export function App() {
  const [file, setFile] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [state, setState] = useState(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dismissedTransitionAnswerId, setDismissedTransitionAnswerId] = useState(null);
  const [audioSettingsOpen, setAudioSettingsOpen] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(0.32);
  const [questionSoundVolume, setQuestionSoundVolume] = useState(0.72);
  const backgroundMusicRef = useRef(null);
  const questionChangeSoundRef = useRef(null);
  const previousQuestionIdRef = useRef(null);

  const concepts = state?.session?.concepts ?? [];
  const answers = state?.session?.answers ?? [];
  const currentQuestion = state?.current_question;
  const lastAnswer = state?.last_answer;
  const answeredQuestion = lastAnswer ? state?.session?.questions?.find((question) => question.question_id === lastAnswer.question_id) : null;
  const progress = state ? Math.round((state.current_index / Math.max(state.total_questions, 1)) * 100) : 0;
  const lastAnswerIsForCurrentQuestion = lastAnswer?.question_id === currentQuestion?.question_id;
  const showFollowupEvaluation =
    lastAnswer?.evaluation && lastAnswerIsForCurrentQuestion && lastAnswer.evaluation.status !== "sufficient";
  const showTransitionEvaluation =
    lastAnswer?.evaluation &&
    lastAnswer.evaluation.next_action === "next_question" &&
    lastAnswer.answer_text !== "/skip" &&
    !lastAnswerIsForCurrentQuestion &&
    dismissedTransitionAnswerId !== lastAnswer.answer_id;
  const showEvaluationMessage = Boolean(
    showTransitionEvaluation || (!state?.completed && showFollowupEvaluation),
  );
  const visibleQuestionId = showEvaluationMessage ? lastAnswer?.question_id : currentQuestion?.question_id;
  const socratesMotion = showEvaluationMessage ? getSocratesMotion(lastAnswer?.evaluation?.status) : SOCRATES_MOTIONS.talking;
  const socratesMotionKey = showEvaluationMessage ? lastAnswer?.answer_id : currentQuestion?.question_id ?? "start";
  const adviceText = showEvaluationMessage ? getAdviceText(lastAnswer?.evaluation) : null;
  const visibleAttemptCount = showEvaluationMessage
    ? lastAnswer?.attempt_number ?? 0
    : answers.filter((item) => item.question_id === currentQuestion?.question_id).length;

  useEffect(() => {
    const backgroundMusic = new Audio(BACKGROUND_MUSIC_SRC);
    const questionChangeSound = new Audio(QUESTION_CHANGE_SOUND_SRC);

    backgroundMusic.loop = true;
    backgroundMusic.volume = backgroundMusicVolume;
    questionChangeSound.volume = questionSoundVolume;

    backgroundMusicRef.current = backgroundMusic;
    questionChangeSoundRef.current = questionChangeSound;

    const startBackgroundMusic = () => {
      backgroundMusic.play().catch(() => {});
    };

    window.addEventListener("pointerdown", startBackgroundMusic, { once: true });
    window.addEventListener("keydown", startBackgroundMusic, { once: true });

    return () => {
      window.removeEventListener("pointerdown", startBackgroundMusic);
      window.removeEventListener("keydown", startBackgroundMusic);
      backgroundMusic.pause();
      backgroundMusicRef.current = null;
      questionChangeSoundRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (backgroundMusicRef.current) {
      backgroundMusicRef.current.volume = backgroundMusicVolume;
    }
  }, [backgroundMusicVolume]);

  useEffect(() => {
    if (questionChangeSoundRef.current) {
      questionChangeSoundRef.current.volume = questionSoundVolume;
    }
  }, [questionSoundVolume]);

  const currentConcept = useMemo(() => {
    if (!currentQuestion) return null;
    return concepts.find((concept) => concept.concept_id === currentQuestion.concept_id);
  }, [concepts, currentQuestion]);

  useEffect(() => {
    const currentQuestionId = visibleQuestionId ?? null;

    if (!currentQuestionId) {
      previousQuestionIdRef.current = null;
      return;
    }

    if (!previousQuestionIdRef.current) {
      previousQuestionIdRef.current = currentQuestionId;
      return;
    }
    if (previousQuestionIdRef.current === currentQuestionId) return;
    previousQuestionIdRef.current = currentQuestionId;

    const questionChangeSound = questionChangeSoundRef.current;
    if (!questionChangeSound) return;

    questionChangeSound.currentTime = 0;
    questionChangeSound.play().catch(() => {});
  }, [visibleQuestionId]);

  async function startSession(event) {
    event.preventDefault();
    if (!file) {
      setError("학습할 PDF를 선택해주세요.");
      return;
    }
    setBusy(true);
    setError("");
    const payload = new FormData();
    payload.append("pdf", file);
    payload.append("subject", form.subject);
    payload.append("difficulty", form.difficulty);
    payload.append("output_language", form.outputLanguage);
    payload.append("max_concepts", form.maxConcepts);
    payload.append("questions_per_concept", form.questionsPerConcept);
    if (form.model) {
      payload.append("model", form.model);
    }
    try {
      const next = await request("/api/sessions", { method: "POST", body: payload });
      setDismissedTransitionAnswerId(null);
      setState(next);
      setAnswer("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!state || !answer.trim()) return;
    setBusy(true);
    setError("");
    try {
      const next = await request(`/api/sessions/${state.session.session_id}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      setDismissedTransitionAnswerId(null);
      setState(next);
      setAnswer("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function postAction(action) {
    if (!state) return;
    setBusy(true);
    setError("");
    try {
      const next = await request(`/api/sessions/${state.session.session_id}/${action}`, { method: "POST" });
      setDismissedTransitionAnswerId(null);
      setState(next);
      setAnswer("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const setupForm = (
    <form onSubmit={startSession} className="setup-form">
      <label className="dropzone">
        <input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <FileUp size={28} />
        <span>{file ? file.name : "강의 PDF 선택"}</span>
      </label>
      <input
        value={form.subject}
        onChange={(event) => setForm({ ...form, subject: event.target.value })}
        placeholder="수업 주제"
      />
      <div className="segmented" aria-label="난이도">
        {["easy", "normal", "hard"].map((value) => (
          <button
            type="button"
            className={form.difficulty === value ? "active" : ""}
            key={value}
            onClick={() => setForm({ ...form, difficulty: value })}
          >
            {value}
          </button>
        ))}
      </div>
      <div className="grid-inputs">
        <label>
          개념 수
          <input
            type="number"
            min="1"
            max="10"
            value={form.maxConcepts}
            onChange={(event) => setForm({ ...form, maxConcepts: event.target.value })}
          />
        </label>
        <label>
          질문 수
          <input
            type="number"
            min="1"
            max="3"
            value={form.questionsPerConcept}
            onChange={(event) => setForm({ ...form, questionsPerConcept: event.target.value })}
          />
        </label>
      </div>
      <button className="primary" disabled={busy} type="submit">
        {busy && !state ? <Loader2 className="spin" size={18} /> : <BookOpen size={18} />}
        분석 시작
      </button>
    </form>
  );

  const audioSettings = (
    <AudioSettings
      isOpen={audioSettingsOpen}
      backgroundMusicVolume={backgroundMusicVolume}
      questionSoundVolume={questionSoundVolume}
      onToggle={() => setAudioSettingsOpen((current) => !current)}
      onBackgroundMusicVolumeChange={setBackgroundMusicVolume}
      onQuestionSoundVolumeChange={setQuestionSoundVolume}
    />
  );

  if (!state) {
    return (
      <main className="start-screen">
        <header className="start-topbar">
          <span>Socratic Lecture Tutor</span>
          {audioSettings}
        </header>
        <section className="start-stage">
          <aside className="parchment upload-scroll">
            <div className="scroll-tab">1단계: 입문</div>
            <h1>지식의 두루마리를 제출하세요</h1>
            <p>공부할 강의 PDF를 제출하면 소크라테스가 두루마리를 해석하여 핵심 개념을 찾아냅니다.</p>
            {error && <div className="error">{error}</div>}
            {setupForm}
            <div className="notice">텍스트가 포함된 PDF 파일만 지원됩니다. 스캔 이미지 PDF는 분석이 어려울 수 있습니다.</div>
          </aside>

          <div className="start-socrates">
            <img src="/theme-assets/socrates-start.png" alt="AI 소크라테스" />
          </div>

          <div className="right-column">
            <aside className="parchment journey-panel">
              <div className="scroll-tab">학습 여정 안내</div>
              <JourneyStep icon={<Landmark size={28} />} title="입문" text="지식의 두루마리를 제출하고 학습 여정을 시작합니다." />
              <JourneyStep icon={<Search size={28} />} title="해석" text="소크라테스가 핵심 개념과 학문의 관문을 찾아냅니다." />
              <JourneyStep icon={<BookOpen size={28} />} title="문답" text="각 관문에서 질문에 답하며 개념을 자신의 것으로 만듭니다." />
              <JourneyStep icon={<Scroll size={28} />} title="기록" text="학습이 끝나면 철학자의 기록으로 복습 방향을 확인합니다." />
            </aside>

            <blockquote className="quote-panel">
              <span>“답을 아는 것이 지혜가 아니라, 올바른 질문을 하는 것이 지혜의 시작이라네.”</span>
              <cite>소크라테스</cite>
            </blockquote>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="study-screen">
      <header className="study-topbar">
        <span>Socratic Lecture Tutor</span>
        <nav>
          <button type="button"><Landmark size={18} /> 학당</button>
          <button type="button"><ScrollText size={18} /> 기록서</button>
          <button type="button">도움말</button>
          {audioSettings}
        </nav>
      </header>

      <section className="study-stage">
        <aside className="gate-panel dark-panel">
          <div className="dark-title">학문의 관문</div>
          <div className="gate-list">
            {concepts.map((concept, index) => {
              const isActive = currentConcept?.concept_id === concept.concept_id;
              const isPassed = state.current_index > index;
              return (
                <article className={isActive ? "gate active" : isPassed ? "gate passed" : "gate"} key={concept.concept_id}>
                  <span className="gate-number">{index + 1}</span>
                  <div>
                    <strong>{concept.title}</strong>
                    <small>p. {concept.source_pages.join(", ") || "-"}</small>
                  </div>
                  <span className="gate-mark">{isActive ? "▶" : isPassed ? "✓" : "▣"}</span>
                </article>
              );
            })}
          </div>
        </aside>

        <aside className="journey-status dark-panel">
          <div className="dark-title">오늘의 여정</div>
          <div className="journey-row">
            <span>완료한 관문</span>
            <strong>{Math.min(state.current_index, state.total_questions)} / {state.total_questions}</strong>
          </div>
          <div className="study-progress"><span style={{ width: `${progress}%` }} /></div>
          <div className="journey-row">
            <span>답변 기록</span>
            <strong>{answers.length}</strong>
          </div>
          <div className="journey-row">
            <span>현재 점수</span>
            <strong>{lastAnswer?.evaluation ? `${Math.round(lastAnswer.evaluation.score * 100)}점` : "-"}</strong>
          </div>
        </aside>

        <div className="study-socrates">
          <AnimatedSocrates motion={socratesMotion} motionKey={socratesMotionKey} />
        </div>

        <div className="question-stack">
          <section className={showEvaluationMessage ? "question-bubble evaluation" : "question-bubble"}>
            <div className="scroll-tab">소크라테스</div>
            {showEvaluationMessage ? (
              <div className="evaluation-message">
                <strong>{Math.round(lastAnswer.evaluation.score * 100)}점 · {statusLabel(lastAnswer.evaluation.status)}</strong>
                <p>{lastAnswer.evaluation.feedback_to_student}</p>
              </div>
            ) : (
              <p>{state.completed ? "오늘의 학습 여정이 끝났네. 기록서를 살펴보게." : currentQuestion?.question}</p>
            )}
          </section>
          {showTransitionEvaluation && (
            <button type="button" className="evaluation-next" onClick={() => setDismissedTransitionAnswerId(lastAnswer.answer_id)}>
              {state.completed ? "기록서 보기" : "다음 질문으로"}
            </button>
          )}
        </div>

        {adviceText && (
          <section className="advice-panel dark-panel">
            <div className="dark-title">소크라테스의 조언</div>
            <p>{adviceText}</p>
          </section>
        )}

        <section className="answer-panel parchment">
          {!state.completed && currentQuestion && !showTransitionEvaluation && (
            <form className="answer-form" onSubmit={submitAnswer}>
              <div className="answer-head">
                <h2>그대의 답변을 입력하세요.</h2>
                <span className="attempt-badge">시도 {visibleAttemptCount} / {MAX_ATTEMPTS_PER_QUESTION}</span>
              </div>
              {visibleAttemptCount > 0 ? (
                <div className="answer-question">
                  <strong>질문</strong>
                  <p>{currentQuestion.question}</p>
                </div>
              ) : (
                <p>완벽하지 않아도 괜찮습니다. 생각을 드러내는 것이 먼저입니다.</p>
              )}
              <textarea
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                placeholder="여기에 답변을 입력하세요..."
                rows={6}
              />
              <div className="command-row">
                <button type="button" disabled={busy} onClick={() => postAction("skip")}>/skip 건너뛰기</button>
                <button type="button" disabled={busy} onClick={() => postAction("finish")}>/quit 종료</button>
              </div>
              <button type="submit" className="primary" disabled={busy || !answer.trim()}>
                {busy ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
                답변 제출
              </button>
            </form>
          )}

          {showTransitionEvaluation && answeredQuestion && (
            <div className="transition-question">
              <span className="attempt-badge">시도 {visibleAttemptCount} / {MAX_ATTEMPTS_PER_QUESTION}</span>
              <strong>질문</strong>
              <p>{answeredQuestion?.question}</p>
            </div>
          )}

          {state.completed && state.session.summary && (
            <div className="summary-card">
              <h2>학습 기록서</h2>
              <p>{state.session.summary.overall_feedback}</p>
              <SummaryList title="강한 개념" items={state.session.summary.strong_concepts} />
              <SummaryList title="복습 개념" items={state.session.summary.weak_concepts} />
            </div>
          )}
        </section>

        <section className="session-record parchment">
          <div className="record-head">
            <h2>학습 기록서</h2>
            <span>이번 세션</span>
          </div>
          <div className="record-row"><span>통과한 관문</span><strong>{Math.min(state.current_index, state.total_questions)}</strong></div>
          <div className="record-row"><span>총 질문 수</span><strong>{state.total_questions}</strong></div>
          <div className="record-row"><span>응답 수</span><strong>{answers.length}</strong></div>
        </section>
      </section>
      </main>
  );
}

function SummaryList({ title, items }) {
  return (
    <section>
      <h3>{title}</h3>
      {items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">기록 없음</p>}
    </section>
  );
}

function AudioSettings({
  isOpen,
  backgroundMusicVolume,
  questionSoundVolume,
  onToggle,
  onBackgroundMusicVolumeChange,
  onQuestionSoundVolumeChange,
}) {
  return (
    <div className="audio-settings">
      <button type="button" className="audio-settings-toggle" onClick={onToggle} aria-expanded={isOpen} aria-label="음량 설정">
        <Settings size={18} />
        설정
      </button>
      {isOpen && (
        <div className="audio-settings-panel">
          <label>
            배경음악
            <span>{Math.round(backgroundMusicVolume * 100)}</span>
            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(backgroundMusicVolume * 100)}
              onChange={(event) => onBackgroundMusicVolumeChange(Number(event.target.value) / 100)}
            />
          </label>
          <label>
            효과음
            <span>{Math.round(questionSoundVolume * 100)}</span>
            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(questionSoundVolume * 100)}
              onChange={(event) => onQuestionSoundVolumeChange(Number(event.target.value) / 100)}
            />
          </label>
        </div>
      )}
    </div>
  );
}

function JourneyStep({ icon, title, text }) {
  return (
    <div className="journey-step">
      <div className="journey-icon">{icon}</div>
      <div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </div>
  );
}

function AnimatedSocrates({ motion, motionKey }) {
  const [frameIndex, setFrameIndex] = useState(0);

  useEffect(() => {
    setFrameIndex(0);
    if (motion.frames.length <= 1) return undefined;

    const finalFrameIndex = motion.frames.length - 1;
    const finalLoopFrameIndex = motion.repeat ? motion.frames.length * motion.repeat - 1 : finalFrameIndex;
    const interval = window.setInterval(() => {
      setFrameIndex((current) => {
        if (!motion.loop) return Math.min(current + 1, finalFrameIndex);
        return Math.min(current + 1, finalLoopFrameIndex);
      });
    }, 180);

    return () => window.clearInterval(interval);
  }, [motion, motionKey]);

  return <img src={motion.frames[frameIndex % motion.frames.length]} alt="AI 소크라테스" />;
}

function getSocratesMotion(status) {
  if (status === "sufficient") return SOCRATES_MOTIONS.correct;
  if (status === "insufficient" || status === "misconception") return SOCRATES_MOTIONS.failure;
  return SOCRATES_MOTIONS.talking;
}

function getAdviceText(evaluation) {
  if (!evaluation || evaluation.status === "sufficient") return null;
  return evaluation.socratic_follow_up || evaluation.hint || evaluation.improvement_note || null;
}

function statusLabel(status) {
  const labels = {
    sufficient: "충분함",
    partially_sufficient: "부분적으로 충분함",
    insufficient: "부족함",
    misconception: "오개념 있음",
  };
  return labels[status] ?? status;
}

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "요청을 처리하지 못했습니다.");
  }
  return payload;
}
