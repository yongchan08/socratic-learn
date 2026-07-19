import { useEffect, useRef, useState } from "react";
import { AdminLoginView } from "./views/AdminLoginView.jsx";
import { LibraryView } from "./views/LibraryView.jsx";
import { RoadmapView } from "./views/RoadmapView.jsx";
import { StartView } from "./views/StartView.jsx";
import { StudyView } from "./views/StudyView.jsx";
import { AudioSettings } from "./components/TopBar.jsx";
import { SvgDefs } from "./components/Ornaments.jsx";
import {
  ACTIVE_COURSE_KEY,
  ACTIVE_SESSION_KEY,
  ADMIN_AUTH_KEY,
  ADMIN_PASSWORD,
  BACKGROUND_MUSIC_SRC,
  BACKGROUND_VOLUME_KEY,
  EFFECT_VOLUME_KEY,
  API_BASE,
  initialForm,
  MAX_PDF_BYTES,
  QUESTION_CHANGE_SOUND_SRC,
} from "./constants.js";
import { request } from "./lib/api.js";
import { storedVolume } from "./lib/storage.js";

export function App() {
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(
    () => window.sessionStorage.getItem(ADMIN_AUTH_KEY) === "true",
  );
  const [adminPassword, setAdminPassword] = useState("");
  const [adminError, setAdminError] = useState("");
  const [file, setFile] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [state, setState] = useState(null);
  const [course, setCourse] = useState(null);
  const [courses, setCourses] = useState([]);
  const [selectedStage, setSelectedStage] = useState(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadingSteps, setLoadingSteps] = useState([]);
  const [dismissedTransitionAnswerId, setDismissedTransitionAnswerId] = useState(null);
  const [audioSettingsOpen, setAudioSettingsOpen] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(
    () => storedVolume(BACKGROUND_VOLUME_KEY, 0.32),
  );
  const [questionSoundVolume, setQuestionSoundVolume] = useState(
    () => storedVolume(EFFECT_VOLUME_KEY, 0.72),
  );
  const backgroundMusicRef = useRef(null);
  const questionChangeSoundRef = useRef(null);
  const previousQuestionIdRef = useRef(null);

  useEffect(() => {
    if (!isAdminAuthenticated) return;
    fetch(`${API_BASE}/api/health`, { cache: "no-store" }).catch(() => {});
    const existingCourseId = window.localStorage.getItem(ACTIVE_COURSE_KEY);
    fetch(`${API_BASE}/api/courses`)
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "학습 로드맵 목록을 불러오지 못했습니다.");
        setCourses(payload);
      })
      .catch((err) => setError(err.message));
    const sessionId = window.localStorage.getItem(ACTIVE_SESSION_KEY);
    if (!sessionId) return;
    setBusy(true);
    Promise.all([
      fetch(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store" }),
      existingCourseId ? fetch(`${API_BASE}/api/courses/${encodeURIComponent(existingCourseId)}`) : null,
    ])
      .then(async ([sessionResponse, courseResponse]) => {
        const sessionPayload = await sessionResponse.json().catch(() => ({}));
        if (!sessionResponse.ok) throw new Error(sessionPayload.detail || "이전 학습 세션을 불러오지 못했습니다.");
        if (courseResponse?.ok) setCourse(await courseResponse.json());
        setState(sessionPayload);
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }, [isAdminAuthenticated]);

  function submitAdminPassword(event) {
    event.preventDefault();
    if (adminPassword !== ADMIN_PASSWORD) {
      setAdminError("비밀번호가 올바르지 않습니다.");
      return;
    }
    window.sessionStorage.setItem(ADMIN_AUTH_KEY, "true");
    setIsAdminAuthenticated(true);
    setAdminPassword("");
    setAdminError("");
  }

  async function createNewCourse() {
    const title = window.prompt("새 학습 로드맵의 이름을 입력하세요.", "새 학습 로드맵");
    if (title === null) return;
    setBusy(true); setError("");
    try {
      const nextCourse = await request("/api/courses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() || "새 학습 로드맵" }),
      });
      setCourses((current) => [nextCourse, ...current]);
      window.localStorage.setItem(ACTIVE_COURSE_KEY, nextCourse.course_id);
      setCourse(nextCourse);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  function openCourse(nextCourse) {
    window.localStorage.setItem(ACTIVE_COURSE_KEY, nextCourse.course_id);
    setCourse(nextCourse);
    setSelectedStage(null);
    setError("");
  }

  async function deleteCourse(event, courseId) {
    event.stopPropagation();
    if (!window.confirm("이 로드맵과 연결된 학습 기록을 삭제할까요?")) return;
    setBusy(true); setError("");
    try {
      await request(`/api/courses/${encodeURIComponent(courseId)}`, { method: "DELETE" });
      setCourses((current) => current.filter((item) => item.course_id !== courseId));
      if (window.localStorage.getItem(ACTIVE_COURSE_KEY) === courseId) {
        window.localStorage.removeItem(ACTIVE_COURSE_KEY);
      }
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  function returnToLibrary() {
    window.localStorage.removeItem(ACTIVE_COURSE_KEY);
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    setCourse(null); setState(null); setSelectedStage(null); setAnswer(""); setError("");
  }

  async function refreshCourse() {
    const courseId = course?.course_id ?? window.localStorage.getItem(ACTIVE_COURSE_KEY);
    if (!courseId) return;
    const nextCourse = await request(`/api/courses/${encodeURIComponent(courseId)}`);
    setCourse(nextCourse);
    setCourses((current) => current.map((item) => item.course_id === nextCourse.course_id ? nextCourse : item));
  }

  async function returnToRoadmap() {
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    setState(null);
    setSelectedStage(null);
    setAnswer("");
    try { await refreshCourse(); } catch (err) { setError(err.message); }
  }

  useEffect(() => {
    const backgroundMusic = new Audio(BACKGROUND_MUSIC_SRC);
    const questionChangeSound = new Audio(QUESTION_CHANGE_SOUND_SRC);
    backgroundMusic.loop = true;
    backgroundMusic.volume = backgroundMusicVolume;
    questionChangeSound.volume = questionSoundVolume;
    backgroundMusicRef.current = backgroundMusic;
    questionChangeSoundRef.current = questionChangeSound;
    const startBackgroundMusic = () => { backgroundMusic.play().catch(() => {}); };
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
    if (backgroundMusicRef.current) backgroundMusicRef.current.volume = backgroundMusicVolume;
    window.localStorage.setItem(BACKGROUND_VOLUME_KEY, String(backgroundMusicVolume));
  }, [backgroundMusicVolume]);

  useEffect(() => {
    if (questionChangeSoundRef.current) questionChangeSoundRef.current.volume = questionSoundVolume;
    window.localStorage.setItem(EFFECT_VOLUME_KEY, String(questionSoundVolume));
  }, [questionSoundVolume]);

  const visibleQuestionId = state?.last_answer?.question_id === state?.current_question?.question_id
    ? state?.last_answer?.question_id
    : state?.current_question?.question_id;

  useEffect(() => {
    const currentQuestionId = visibleQuestionId ?? null;
    if (!currentQuestionId) { previousQuestionIdRef.current = null; return; }
    if (!previousQuestionIdRef.current) { previousQuestionIdRef.current = currentQuestionId; return; }
    if (previousQuestionIdRef.current === currentQuestionId) return;
    previousQuestionIdRef.current = currentQuestionId;
    const questionChangeSound = questionChangeSoundRef.current;
    if (!questionChangeSound) return;
    questionChangeSound.currentTime = 0;
    questionChangeSound.play().catch(() => {});
  }, [visibleQuestionId]);

  async function startSession(event) {
    event.preventDefault();
    if (!file) { setError("학습할 PDF를 선택해주세요."); return; }
    setBusy(true); setError(""); setLoadingSteps([]);

    const payload = new FormData();
    payload.append("pdf", file);
    payload.append("difficulty", form.difficulty);
    payload.append("output_language", form.outputLanguage);
    payload.append("session_mode", form.sessionMode);
    if (course?.course_id && selectedStage) {
      payload.set("session_mode", "study");
      payload.append("course_id", course.course_id);
      payload.append("stage_index", String(selectedStage.stage_index));
    }
    if (form.model) payload.append("model", form.model);

    const addStep = (label) => {
      setLoadingSteps((prev) => [...prev, { label, done: false }]);
    };
    const completeStep = (label) => {
      setLoadingSteps((prev) =>
        prev.map((step) => (step.label === label && !step.done ? { ...step, done: true } : step)),
      );
    };
    const updateStep = (newLabel) => {
      setLoadingSteps((prev) =>
        prev.map((step, index) => (index === prev.length - 1 ? { ...step, label: newLabel } : step)),
      );
    };

    try {
      const response = await fetch(`${API_BASE}/api/sessions/stream`, { method: "POST", body: payload });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "요청을 처리하지 못했습니다.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          const text = line.replace(/^data: /, "").trim();
          if (!text) continue;
          let evt;
          try {
            evt = JSON.parse(text);
          } catch {
            continue;
          }

          if (evt.step === "parsing") {
            addStep(evt.message);
          } else if (evt.step === "concepts") {
            completeStep("📜 두루마리를 해독하는 중...");
            addStep(evt.message);
          } else if (evt.step === "questions_start") {
            completeStep("🔍 핵심 개념 발굴 중...");
            addStep(evt.message);
          } else if (evt.step === "questions") {
            updateStep(evt.message);
          } else if (evt.step === "done") {
            setLoadingSteps((prev) => prev.map((step) => ({ ...step, done: true })));
            setDismissedTransitionAnswerId(null);
            setState(evt.payload);
            window.localStorage.setItem(ACTIVE_SESSION_KEY, evt.payload.session.session_id);
            setAnswer("");
          } else if (evt.step === "error") {
            throw new Error(evt.message);
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function startFinalReview() {
    if (!course) return;
    setBusy(true); setError("");
    try {
      const next = course.final_review_session_id
        ? await request(`/api/sessions/${encodeURIComponent(course.final_review_session_id)}`)
        : await request(`/api/courses/${encodeURIComponent(course.course_id)}/final-review`, { method: "POST" });
      window.localStorage.setItem(ACTIVE_SESSION_KEY, next.session.session_id);
      setState(next);
      setAnswer("");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  function selectPdf(event) {
    const selected = event.target.files?.[0] ?? null;
    if (selected && selected.size > MAX_PDF_BYTES) {
      setFile(null);
      setError("PDF 파일은 최대 25MB까지 업로드할 수 있습니다.");
      event.target.value = "";
      return;
    }
    setFile(selected);
    setError("");
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!state || !answer.trim()) return;
    setBusy(true); setError("");
    try {
      const next = await request(`/api/sessions/${state.session.session_id}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      setDismissedTransitionAnswerId(null); setState(next); setAnswer("");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function postAction(action) {
    if (!state) return;
    setBusy(true); setError("");
    try {
      const next = await request(`/api/sessions/${state.session.session_id}/${action}`, { method: "POST" });
      setDismissedTransitionAnswerId(null); setState(next); setAnswer("");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

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

  if (!isAdminAuthenticated) {
    return (
      <>
        <SvgDefs/>
        <AdminLoginView
          audioSettings={audioSettings}
          adminPassword={adminPassword}
          adminError={adminError}
          onPasswordChange={(event) => {
            setAdminPassword(event.target.value);
            if (adminError) setAdminError("");
          }}
          onSubmit={submitAdminPassword}
        />
      </>
    );
  }

  if (!state && !course) {
    return (
      <>
        <SvgDefs/>
        <LibraryView
          audioSettings={audioSettings}
          courses={courses}
          error={error}
          busy={busy}
          onCreateCourse={createNewCourse}
          onOpenCourse={openCourse}
          onDeleteCourse={deleteCourse}
        />
      </>
    );
  }

  if (!state && !selectedStage) {
    return (
      <>
        <SvgDefs/>
        <RoadmapView
          audioSettings={audioSettings}
          busy={busy}
          course={course}
          error={error}
          onBack={returnToLibrary}
          onStageOpen={(sessionId) => {
            request(`/api/sessions/${sessionId}`)
              .then((next) => {
                window.localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
                setState(next);
              })
              .catch((err) => setError(err.message));
          }}
          onStartFinalReview={startFinalReview}
          onSelectStage={setSelectedStage}
        />
      </>
    );
  }

  if (!state) {
    return (
      <>
        <SvgDefs/>
        <StartView
          audioSettings={audioSettings}
          busy={busy}
          error={error}
          file={file}
          form={form}
          loadingSteps={loadingSteps}
          onDifficultyChange={(value) => setForm({ ...form, difficulty: value })}
          onFileChange={selectPdf}
          onSubmit={startSession}
          selectedStage={selectedStage}
        />
      </>
    );
  }

  const concepts = state?.session?.concepts ?? [];
  const answers = state?.session_mode === "concept_review"
    ? (state?.session?.concept_answers ?? [])
    : (state?.session?.answers ?? []);
  const currentQuestion = state?.current_question;
  const questionText = state.completed
    ? "오늘의 학습 여정이 끝났네. 기록서를 살펴보게."
    : currentQuestion?.question ?? "";
  const progress = state ? Math.round((state.current_index / Math.max(state.total_questions, 1)) * 100) : 0;

  return (
    <>
      <SvgDefs/>
      <StudyView
        audioSettings={audioSettings}
        answers={answers}
        busy={busy}
        concepts={concepts}
        currentQuestion={currentQuestion}
        dismissedTransitionAnswerId={dismissedTransitionAnswerId}
        onAcademy={returnToRoadmap}
        onAnswerChange={setAnswer}
        onDismissTransition={setDismissedTransitionAnswerId}
        onPostAction={postAction}
        onSubmitAnswer={submitAnswer}
        progress={progress}
        questionText={questionText}
        state={state}
        answer={answer}
      />
    </>
    );
  }
