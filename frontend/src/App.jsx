import { useEffect, useRef, useState } from "react";
import { AdminLoginView } from "./views/AdminLoginView.jsx";
import { CheckpointIntroView } from "./views/CheckpointIntroView.jsx";
import { ConceptCheckpointView } from "./views/ConceptCheckpointView.jsx";
import { ContinueCourseView } from "./views/ContinueCourseView.jsx";
import { CourseCompletionView } from "./views/CourseCompletionView.jsx";
import { RoadmapView } from "./views/RoadmapView.jsx";
import { StartView } from "./views/StartView.jsx";
import { StudyView } from "./views/StudyView.jsx";
import { TitleView } from "./views/TitleView.jsx";
import { AudioSettings } from "./components/TopBar.jsx";
import { SvgDefs } from "./components/Ornaments.jsx";
import {
  ACTIVE_COURSE_KEY,
  ACTIVE_SESSION_KEY,
  ADMIN_AUTH_KEY,
  ADMIN_PASSWORD,
  BACKGROUND_MUSIC_SRC,
  BACKGROUND_VOLUME_KEY,
  BUTTON_HOVER_SOUND_SRC,
  EFFECT_VOLUME_KEY,
  API_BASE,
  initialForm,
  MAX_PDF_BYTES,
  QUESTION_CHANGE_SOUND_SRC,
} from "./constants.js";
import { request } from "./lib/api.js";
import { storedVolume } from "./lib/storage.js";

const DEFAULT_WEEK_COUNT = 13;

function courseProgressPercent(courseObj) {
  const stages = courseObj?.stages ?? [];
  if (!stages.length) return 0;
  const completedCount = stages.filter((stage) => stage.completed).length;
  return Math.round((completedCount / stages.length) * 100);
}

function isCourseComplete(courseObj) {
  const stages = courseObj?.stages ?? [];
  const last = stages[stages.length - 1];
  return Boolean(last && last.kind === "checkpoint" && last.completed);
}

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
  const [newCourseUploadMode, setNewCourseUploadMode] = useState(false);
  const [showContinueList, setShowContinueList] = useState(false);
  const [pendingCheckpoint, setPendingCheckpoint] = useState(null);
  const [checkpointVariant, setCheckpointVariant] = useState(null);
  const [courseSummary, setCourseSummary] = useState(null);
  const [showCompletion, setShowCompletion] = useState(false);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadingSteps, setLoadingSteps] = useState([]);
  const [dismissedTransitionAnswerId, setDismissedTransitionAnswerId] = useState(null);
  const [audioSettingsOpen, setAudioSettingsOpen] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(
    () => storedVolume(BACKGROUND_VOLUME_KEY, 0.5),
  );
  const [questionSoundVolume, setQuestionSoundVolume] = useState(
    () => storedVolume(EFFECT_VOLUME_KEY, 0.5),
  );
  const backgroundMusicRef = useRef(null);
  const questionChangeSoundRef = useRef(null);
  const buttonHoverSoundRef = useRef(null);
  const weekUploadInputRef = useRef(null);
  const weekUploadStageRef = useRef(null);
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
    if (!existingCourseId && !sessionId) return;
    setBusy(true);
    Promise.all([
      sessionId ? fetch(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store" }) : null,
      existingCourseId ? fetch(`${API_BASE}/api/courses/${encodeURIComponent(existingCourseId)}`) : null,
    ])
      .then(async ([sessionResponse, courseResponse]) => {
        let restoredCourse = null;
        if (courseResponse?.ok) {
          restoredCourse = await courseResponse.json();
          setCourse(restoredCourse);
        }
        if (sessionResponse) {
          const sessionPayload = await sessionResponse.json().catch(() => ({}));
          if (!sessionResponse.ok) throw new Error(sessionPayload.detail || "이전 학습 세션을 불러오지 못했습니다.");
          if (sessionPayload.session_mode === "concept_review" && restoredCourse) {
            const stage = restoredCourse.stages.find(
              (item) => item.session_id === sessionPayload.session.session_id,
            );
            setCheckpointVariant(stage?.checkpoint_type === "midterm" ? "feynman" : "plain");
          }
          setState(sessionPayload);
        }
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

  function beginNewCourseUpload() {
    setFile(null); setError("");
    setNewCourseUploadMode(true);
    setShowContinueList(false);
  }

  async function submitSyllabus(event) {
    event.preventDefault();
    if (!file) { setError("강의계획서 PDF를 선택해주세요."); return; }
    setBusy(true); setError("");
    try {
      const payload = new FormData();
      payload.append("pdf", file);
      const newCourse = await request("/api/courses/from-syllabus", { method: "POST", body: payload });
      setCourses((current) => [newCourse, ...current]);
      window.localStorage.setItem(ACTIVE_COURSE_KEY, newCourse.course_id);
      setCourse(newCourse);
      setSelectedStage(null);
      setNewCourseUploadMode(false);
      setFile(null);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  function openCourseFromContinue(nextCourse) {
    window.localStorage.setItem(ACTIVE_COURSE_KEY, nextCourse.course_id);
    setCourse(nextCourse);
    setSelectedStage(null);
    setShowContinueList(false);
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
    setShowContinueList(true);
    setShowCompletion(false); setCourseSummary(null);
    setPendingCheckpoint(null); setCheckpointVariant(null);
  }

  function returnToMain() {
    window.localStorage.removeItem(ACTIVE_COURSE_KEY);
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    setCourse(null);
    setState(null);
    setSelectedStage(null);
    setAnswer("");
    setError("");
    setShowContinueList(false);
    setShowCompletion(false);
    setCourseSummary(null);
    setPendingCheckpoint(null);
    setCheckpointVariant(null);
    setNewCourseUploadMode(false);
  }

  async function refreshCourse() {
    const courseId = course?.course_id ?? window.localStorage.getItem(ACTIVE_COURSE_KEY);
    if (!courseId) return null;
    const nextCourse = await request(`/api/courses/${encodeURIComponent(courseId)}`);
    setCourse(nextCourse);
    setCourses((current) => current.map((item) => item.course_id === nextCourse.course_id ? nextCourse : item));
    return nextCourse;
  }

  async function returnToRoadmap() {
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    setState(null);
    setSelectedStage(null);
    setCheckpointVariant(null);
    setPendingCheckpoint(null);
    setAnswer("");
    try {
      const nextCourse = await refreshCourse();
      if (isCourseComplete(nextCourse)) {
        const summary = await request(`/api/courses/${encodeURIComponent(nextCourse.course_id)}/summary`);
        setCourseSummary(summary);
        setShowCompletion(true);
      }
    } catch (err) { setError(err.message); }
  }

  function backToRoadmapFromCompletion() {
    setShowCompletion(false);
    setCourseSummary(null);
  }

  function backToTitleFromSyllabusUpload() {
    window.localStorage.removeItem(ACTIVE_COURSE_KEY);
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    setFile(null); setError("");
    setCourse(null);
    setSelectedStage(null);
    setNewCourseUploadMode(false);
    setShowContinueList(false);
  }

  function backFromWeekUpload() {
    setFile(null); setError("");
    setSelectedStage(null);
  }

  function openExistingSession(sessionId, checkpointType) {
    setBusy(true); setError("");
    request(`/api/sessions/${encodeURIComponent(sessionId)}`)
      .then((next) => {
        window.localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
        setCheckpointVariant(checkpointType === "midterm" ? "feynman" : checkpointType === "final" ? "plain" : null);
        setDismissedTransitionAnswerId(null);
        setState(next);
        setAnswer("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }

  async function startCheckpoint(stage) {
    if (!course) return;
    setBusy(true); setError("");
    try {
      const next = await request(
        `/api/courses/${encodeURIComponent(course.course_id)}/checkpoints/${stage.stage_index}`,
        { method: "POST" },
      );
      window.localStorage.setItem(ACTIVE_SESSION_KEY, next.session.session_id);
      setCheckpointVariant(stage.checkpoint_type === "midterm" ? "feynman" : "plain");
      setPendingCheckpoint(null);
      setState(next);
      setAnswer("");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  function openRoadmapStage(stage) {
    setError("");
    if (stage.session_id) {
      openExistingSession(stage.session_id, stage.checkpoint_type);
    }
  }

  function actionRoadmapStage(stage) {
    setError("");
    if (stage.checkpoint_type === "midterm") {
      setPendingCheckpoint(stage);
    } else {
      startCheckpoint(stage);
    }
  }

  function promptRoadmapPdfUpload(stage) {
    weekUploadStageRef.current = stage;
    setError("");
    weekUploadInputRef.current?.click();
  }

  async function handleRoadmapPdfChange(event) {
    const selected = event.target.files?.[0] ?? null;
    event.target.value = "";
    if (!selected) return;
    if (selected.size > MAX_PDF_BYTES) {
      setError("PDF 파일은 최대 25MB까지 업로드할 수 있습니다.");
      return;
    }
    const stage = weekUploadStageRef.current;
    if (!stage) {
      setError("업로드할 학습 단계를 찾지 못했습니다.");
      return;
    }
    setFile(selected);
    await submitSessionUpload(selected, stage);
  }

  useEffect(() => {
    const backgroundMusic = new Audio(BACKGROUND_MUSIC_SRC);
    const questionChangeSound = new Audio(QUESTION_CHANGE_SOUND_SRC);
    const buttonHoverSound = new Audio(BUTTON_HOVER_SOUND_SRC);
    backgroundMusic.loop = true;
    backgroundMusic.volume = backgroundMusicVolume;
    questionChangeSound.volume = questionSoundVolume;
    buttonHoverSound.volume = questionSoundVolume;
    buttonHoverSound.preload = "auto";
    backgroundMusicRef.current = backgroundMusic;
    questionChangeSoundRef.current = questionChangeSound;
    buttonHoverSoundRef.current = buttonHoverSound;
    const startBackgroundMusic = () => { backgroundMusic.play().catch(() => {}); };
    window.addEventListener("pointerdown", startBackgroundMusic, { once: true });
    window.addEventListener("keydown", startBackgroundMusic, { once: true });
    return () => {
      window.removeEventListener("pointerdown", startBackgroundMusic);
      window.removeEventListener("keydown", startBackgroundMusic);
      backgroundMusic.pause();
      backgroundMusicRef.current = null;
      questionChangeSoundRef.current = null;
      buttonHoverSoundRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (backgroundMusicRef.current) backgroundMusicRef.current.volume = backgroundMusicVolume;
    window.localStorage.setItem(BACKGROUND_VOLUME_KEY, String(backgroundMusicVolume));
  }, [backgroundMusicVolume]);

  useEffect(() => {
    if (questionChangeSoundRef.current) questionChangeSoundRef.current.volume = questionSoundVolume;
    if (buttonHoverSoundRef.current) buttonHoverSoundRef.current.volume = questionSoundVolume;
    window.localStorage.setItem(EFFECT_VOLUME_KEY, String(questionSoundVolume));
  }, [questionSoundVolume]);

  function playButtonHoverSound() {
    const hoverSound = buttonHoverSoundRef.current;
    if (!hoverSound) return;
    hoverSound.currentTime = 0;
    hoverSound.play().catch(() => {});
  }

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

  async function submitSessionUpload(selectedFile, stage = null) {
    if (!selectedFile) { setError("학습할 PDF를 선택해주세요."); return; }
    setBusy(true); setError(""); setLoadingSteps([]);

    const payload = new FormData();
    payload.append("pdf", selectedFile);
    payload.append("difficulty", form.difficulty);
    payload.append("output_language", form.outputLanguage);
    payload.append("session_mode", form.sessionMode);
    if (course?.course_id && stage) {
      payload.set("session_mode", "study");
      payload.append("course_id", course.course_id);
      payload.append("stage_index", String(stage.stage_index));
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
            if (course?.course_id) {
              refreshCourse().catch(() => {});
            }
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

  async function startSession(event) {
    event.preventDefault();
    await submitSessionUpload(file, selectedStage);
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
    if (newCourseUploadMode) {
      return (
        <>
          <SvgDefs/>
          <StartView
            audioSettings={audioSettings}
            busy={busy}
            error={error}
            file={file}
            loadingSteps={loadingSteps}
            mode="syllabus"
            onBack={backToTitleFromSyllabusUpload}
            onFileChange={selectPdf}
            onSubmit={submitSyllabus}
          />
        </>
      );
    }
    return (
      <>
        <SvgDefs/>
        {showContinueList ? (
          <ContinueCourseView
            audioSettings={audioSettings}
            courses={courses}
            error={error}
            onMain={returnToMain}
            onOpenCourse={openCourseFromContinue}
          />
        ) : (
        <TitleView
          audioSettings={audioSettings}
          busy={busy}
          error={error}
          onButtonHover={playButtonHoverSound}
          onStartNew={beginNewCourseUpload}
          onContinue={() => setShowContinueList(true)}
        />
        )}
      </>
    );
  }

  if (showCompletion) {
    return (
      <>
        <SvgDefs/>
        <CourseCompletionView
          audioSettings={audioSettings}
          busy={busy}
          course={course}
          summary={courseSummary}
          onReturnToRoadmap={backToRoadmapFromCompletion}
        />
      </>
    );
  }

  if (pendingCheckpoint) {
    return (
      <>
        <SvgDefs/>
        <CheckpointIntroView
          audioSettings={audioSettings}
          busy={busy}
          course={course}
          progress={courseProgressPercent(course)}
          onAcademy={returnToRoadmap}
          onStartHover={playButtonHoverSound}
          onStart={() => startCheckpoint(pendingCheckpoint)}
        />
      </>
    );
  }

  if (!state && !selectedStage) {
    return (
      <>
        <SvgDefs/>
        <input
          ref={weekUploadInputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handleRoadmapPdfChange}
          style={{ display: "none" }}
        />
        <RoadmapView
          audioSettings={audioSettings}
          busy={busy}
          course={course}
          error={error}
          onBack={returnToLibrary}
          onOpenStage={openRoadmapStage}
          onActionStage={actionRoadmapStage}
          onUploadStagePdf={promptRoadmapPdfUpload}
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
          loadingSteps={loadingSteps}
          mode="week"
          selectedStage={selectedStage}
          onBack={backFromWeekUpload}
          onFileChange={selectPdf}
          onSubmit={startSession}
        />
      </>
    );
  }

  if (state.session_mode === "concept_review") {
    return (
      <>
        <SvgDefs/>
        <ConceptCheckpointView
          audioSettings={audioSettings}
          answer={answer}
          busy={busy}
          course={course}
          onAcademy={returnToRoadmap}
          onAnswerChange={setAnswer}
          onSubmitAnswer={submitAnswer}
          progress={courseProgressPercent(course)}
          state={state}
          variant={checkpointVariant ?? "plain"}
        />
      </>
    );
  }

  const concepts = state?.session?.concepts ?? [];
  const answers = state?.session?.answers ?? [];
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
        courseProgress={courseProgressPercent(course)}
        courseTitle={course?.title}
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
