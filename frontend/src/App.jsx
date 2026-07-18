import { BookOpen, FileUp, Landmark, Loader2, Search, Send, Settings, Scroll } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const BACKGROUND_MUSIC_SRC = "/audio/background_music.mp3";
const QUESTION_CHANGE_SOUND_SRC = "/audio/page-turn.mp3";
const MAX_ATTEMPTS_PER_QUESTION = 3;
const MAX_PDF_BYTES = 25 * 1024 * 1024;
const ACTIVE_SESSION_KEY = "socratic_tutor_active_session_id";

const initialForm = {
  difficulty: "normal",
  outputLanguage: "ko",
  model: "",
  sessionMode: "study",
};

/* ── SVG defs (ornaments) ────────────────────────────────────────────────── */

function SvgDefs() {
  return (
    <svg style={{ position: "absolute", width: 0, height: 0, overflow: "hidden" }} aria-hidden="true" focusable="false">
      <defs>
        {/* TopBar gradients & filters */}
        <linearGradient id="sltGold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#38220d" /><stop offset="0.22" stopColor="#8f6f3b" />
          <stop offset="0.45" stopColor="#c2a36b" /><stop offset="0.62" stopColor="#76582a" />
          <stop offset="0.82" stopColor="#b8985b" /><stop offset="1" stopColor="#2f1e0c" />
        </linearGradient>
        <linearGradient id="sltGoldV" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c2a36b" /><stop offset="0.45" stopColor="#8f6f3b" /><stop offset="1" stopColor="#3a250f" />
        </linearGradient>
        <filter id="sltGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="0.3" floodColor="#b89555" floodOpacity="0.22" />
          <feDropShadow dx="0" dy="1" stdDeviation="0.45" floodColor="#050302" floodOpacity="0.95" />
        </filter>
        <symbol id="sltCorner" viewBox="0 0 72 56">
          <g fill="none" stroke="#160d04" strokeWidth="3.2" strokeLinecap="square" strokeLinejoin="miter" opacity="0.95">
            <path d="M3 4.5H31M4.5 3V27"/><path d="M4.5 29V53M3 51.5H31"/>
            <rect x="6" y="6" width="20" height="20"/><rect x="10.5" y="10.5" width="11" height="11"/><rect x="14.5" y="14.5" width="3" height="3"/>
            <rect x="6" y="30" width="20" height="20"/><rect x="10.5" y="34.5" width="11" height="11"/><rect x="14.5" y="38.5" width="3" height="3"/>
            <path d="M28 5.5H70"/><path d="M28 50.5H70"/>
            <path d="M28 5.5V20.5H40.5V12.5H35.5V17"/><path d="M28 50.5V35.5H40.5V43.5H35.5V39"/>
            <path d="M33 25H54V19H48"/><path d="M33 31H54V37H48"/>
            <path d="M45 8.5C50 8.5 51.5 11 51.5 14C51.5 17 49.5 19 47 18.5C45 18 45.5 15 47.3 15.2" strokeLinecap="round"/>
            <path d="M45 47.5C50 47.5 51.5 45 51.5 42C51.5 39 49.5 37 47 37.5C45 38 45.5 41 47.3 40.8" strokeLinecap="round"/>
            <path d="M57 15V23M60 18H68"/><path d="M57 41V33M60 38H68"/>
          </g>
          <g fill="none" stroke="url(#sltGold)" strokeWidth="1.45" strokeLinecap="square" strokeLinejoin="miter" filter="url(#sltGlow)">
            <path d="M3 4.5H31M4.5 3V27"/><path d="M4.5 29V53M3 51.5H31"/>
            <rect x="6" y="6" width="20" height="20"/><rect x="10.5" y="10.5" width="11" height="11"/><rect x="14.5" y="14.5" width="3" height="3"/>
            <rect x="6" y="30" width="20" height="20"/><rect x="10.5" y="34.5" width="11" height="11"/><rect x="14.5" y="38.5" width="3" height="3"/>
            <path d="M28 5.5H70"/><path d="M28 50.5H70"/>
            <path d="M28 5.5V20.5H40.5V12.5H35.5V17"/><path d="M28 50.5V35.5H40.5V43.5H35.5V39"/>
            <path d="M33 25H54V19H48"/><path d="M33 31H54V37H48"/>
            <path d="M45 8.5C50 8.5 51.5 11 51.5 14C51.5 17 49.5 19 47 18.5C45 18 45.5 15 47.3 15.2" strokeLinecap="round"/>
            <path d="M45 47.5C50 47.5 51.5 45 51.5 42C51.5 39 49.5 37 47 37.5C45 38 45.5 41 47.3 40.8" strokeLinecap="round"/>
            <path d="M57 15V23M60 18H68"/><path d="M57 41V33M60 38H68"/>
          </g>
          <g fill="#b8985b" opacity="0.72" filter="url(#sltGlow)">
            <circle cx="39.5" cy="16.8" r="1.1"/><circle cx="39.5" cy="39.2" r="1.1"/>
            <circle cx="64.5" cy="22.6" r="0.9"/><circle cx="64.5" cy="33.4" r="0.9"/>
          </g>
        </symbol>
        <symbol id="sltIconAcademy" viewBox="0 0 32 32">
          <g transform="translate(0 1)" fill="#130c05" stroke="#130c05" strokeWidth="1.6" strokeLinejoin="round" opacity="0.96">
            <path d="M16 3.2 3.9 10.4h24.2L16 3.2Z"/>
            <rect x="5.2" y="11" width="21.6" height="2.2" rx="0.4"/>
            <rect x="7" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="12.2" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="17.4" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="22.6" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="5.2" y="23.4" width="21.6" height="2.4" rx="0.4"/>
            <rect x="3.6" y="26" width="24.8" height="2.7" rx="0.4"/>
          </g>
          <g transform="translate(0 1)" fill="url(#sltGoldV)" stroke="#4a3014" strokeWidth="0.55" strokeLinejoin="round" filter="url(#sltGlow)">
            <path d="M16 3.2 3.9 10.4h24.2L16 3.2Z"/>
            <rect x="5.2" y="11" width="21.6" height="2.2" rx="0.4"/>
            <rect x="7" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="12.2" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="17.4" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="22.6" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="5.2" y="23.4" width="21.6" height="2.4" rx="0.4"/>
            <rect x="3.6" y="26" width="24.8" height="2.7" rx="0.4"/>
          </g>
        </symbol>
        {/* LeftColumn */}
        <linearGradient id="slpGoldStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#37230e"/><stop offset="0.22" stopColor="#7f612e"/>
          <stop offset="0.46" stopColor="#b99a60"/><stop offset="0.66" stopColor="#6d5228"/>
          <stop offset="0.86" stopColor="#a9884c"/><stop offset="1" stopColor="#2b1b0a"/>
        </linearGradient>
        <linearGradient id="slpGoldFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c0a06a"/><stop offset="0.42" stopColor="#8b6c37"/><stop offset="1" stopColor="#33210d"/>
        </linearGradient>
        <filter id="slpGoldShadow" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="0" stdDeviation="0.26" floodColor="#b89555" floodOpacity="0.28"/>
          <feDropShadow dx="0" dy="1" stdDeviation="0.50" floodColor="#050302" floodOpacity="0.90"/>
        </filter>
        <symbol id="slpCorner" viewBox="0 0 32 32">
          <g fill="none" stroke="#120b04" strokeWidth="2.8" strokeLinecap="square" strokeLinejoin="miter" opacity="0.95">
            <path d="M2.6 29.4V2.6H29.4"/><path d="M6 26V6H26"/><path d="M10 22V10H22"/><path d="M14 18V14H18"/>
            <path d="M2.6 18H8.4M18 2.6V8.4"/><path d="M6 30H15M30 6V15"/>
          </g>
          <g fill="none" stroke="url(#slpGoldStroke)" strokeWidth="1.25" strokeLinecap="square" strokeLinejoin="miter" filter="url(#slpGoldShadow)">
            <path d="M2.6 29.4V2.6H29.4"/><path d="M6 26V6H26"/><path d="M10 22V10H22"/><path d="M14 18V14H18"/>
            <path d="M2.6 18H8.4M18 2.6V8.4"/><path d="M6 30H15M30 6V15"/>
          </g>
          <g fill="#b99a60" opacity="0.78" filter="url(#slpGoldShadow)">
            <circle cx="25" cy="7" r="0.82"/><circle cx="7" cy="25" r="0.82"/>
          </g>
        </symbol>
        <symbol id="slpTitleDivider" viewBox="0 0 188 12">
          <g fill="none" stroke="#150d05" strokeWidth="2" opacity="0.85">
            <path d="M3 6h78M107 6h78"/><path d="M83 6c3-4 8-4 11 0 3 4 8 4 11 0"/>
            <path d="M17 4c2-2 4-2 6 0M165 4c2-2 4-2 6 0"/>
          </g>
          <g fill="none" stroke="url(#slpGoldStroke)" strokeWidth="0.9" strokeLinecap="round" filter="url(#slpGoldShadow)">
            <path d="M3 6h78M107 6h78"/><path d="M83 6c3-4 8-4 11 0 3 4 8 4 11 0"/>
            <path d="M17 4c2-2 4-2 6 0M165 4c2-2 4-2 6 0"/>
          </g>
          <g fill="#b99a60" opacity="0.72">
            <circle cx="94" cy="6" r="1.15"/><circle cx="13" cy="6" r="0.75"/><circle cx="175" cy="6" r="0.75"/>
          </g>
        </symbol>
        <symbol id="slpCompass" viewBox="0 0 28 28">
          <g fill="none" stroke="#130c05" strokeWidth="2.4" strokeLinejoin="round" opacity="0.96">
            <circle cx="14" cy="14" r="11.2"/>
            <path d="M14 2.8v22.4M2.8 14h22.4M6.1 6.1l15.8 15.8M21.9 6.1 6.1 21.9"/>
            <path d="M14 5.3 17.1 14 14 22.7 10.9 14Z"/>
          </g>
          <g fill="none" stroke="url(#slpGoldStroke)" strokeWidth="1.25" strokeLinejoin="round" filter="url(#slpGoldShadow)">
            <circle cx="14" cy="14" r="11.2"/>
            <path d="M14 2.8v22.4M2.8 14h22.4M6.1 6.1l15.8 15.8M21.9 6.1 6.1 21.9" opacity="0.78"/>
            <path d="M14 5.3 17.1 14 14 22.7 10.9 14Z" fill="rgba(137,105,52,0.28)"/>
            <circle cx="14" cy="14" r="2.1"/>
          </g>
        </symbol>
        <symbol id="slpLock" viewBox="0 0 24 24">
          <path d="M7.25 10.2V8.15c0-2.95 2.07-5.1 4.75-5.1s4.75 2.15 4.75 5.1v2.05h1.2c.8 0 1.45.65 1.45 1.45v7.55c0 .8-.65 1.45-1.45 1.45H6.05c-.8 0-1.45-.65-1.45-1.45v-7.55c0-.8.65-1.45 1.45-1.45h1.2Zm2.3 0h4.9V8.15c0-1.62-.99-2.85-2.45-2.85S9.55 6.53 9.55 8.15v2.05Z" fill="#130c05" opacity="0.94"/>
          <path d="M7.25 10.2V8.15c0-2.95 2.07-5.1 4.75-5.1s4.75 2.15 4.75 5.1v2.05h1.2c.8 0 1.45.65 1.45 1.45v7.55c0 .8-.65 1.45-1.45 1.45H6.05c-.8 0-1.45-.65-1.45-1.45v-7.55c0-.8.65-1.45 1.45-1.45h1.2Zm2.3 0h4.9V8.15c0-1.62-.99-2.85-2.45-2.85S9.55 6.53 9.55 8.15v2.05Z" fill="url(#slpGoldFill)" stroke="#4a3014" strokeWidth="0.52" filter="url(#slpGoldShadow)"/>
          <circle cx="12" cy="15.2" r="1.25" fill="#2c1c0b" stroke="none" opacity="0.9"/>
          <path d="M12 16.1v2.2" stroke="#2c1c0b" strokeWidth="1" strokeLinecap="round"/>
        </symbol>
        <symbol id="slpChevron" viewBox="0 0 16 20">
          <path d="M4 3.2 12.4 10 4 16.8Z" fill="#170e05" opacity="0.94"/>
          <path d="M4 3.2 12.4 10 4 16.8Z" fill="url(#slpGoldFill)" stroke="#4a3014" strokeWidth="0.58" filter="url(#slpGoldShadow)"/>
        </symbol>

        {/* RightColumn */}
        <linearGradient id="srpGold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2f1f0d"/><stop offset="0.18" stopColor="#6a5028"/>
          <stop offset="0.42" stopColor="#b79b63"/><stop offset="0.58" stopColor="#7c5d2f"/>
          <stop offset="0.82" stopColor="#a98548"/><stop offset="1" stopColor="#2b1b0a"/>
        </linearGradient>
        <linearGradient id="srpBlue" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1d486b"/><stop offset="0.50" stopColor="#123455"/><stop offset="1" stopColor="#0b223a"/>
        </linearGradient>
        <filter id="srpGoldShadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="0.28" floodColor="#b89555" floodOpacity="0.22"/>
          <feDropShadow dx="0" dy="1" stdDeviation="0.55" floodColor="#060302" floodOpacity="0.9"/>
        </filter>
        <symbol id="srpCorner" viewBox="0 0 42 42">
          <g fill="none" stroke="#150e06" strokeWidth="3" strokeLinecap="square" strokeLinejoin="miter" opacity="0.92">
            <path d="M5 37V5H37"/><path d="M10 33V10H33"/><path d="M15 29V15H29"/><path d="M20 25V20H25"/>
          </g>
          <g fill="none" stroke="url(#srpGold)" strokeWidth="1.35" strokeLinecap="square" strokeLinejoin="miter" filter="url(#srpGoldShadow)">
            <path d="M5 37V5H37"/><path d="M10 33V10H33" opacity="0.78"/>
            <path d="M15 29V15H29" opacity="0.62"/><path d="M20 25V20H25" opacity="0.82"/>
          </g>
          <circle cx="8" cy="34" r="1.5" fill="#9b7539"/>
        </symbol>
        <symbol id="srpDivider" viewBox="0 0 360 14">
          <path d="M22 7H338" fill="none" stroke="#80683d" strokeWidth="1" opacity="0.48" vectorEffect="non-scaling-stroke"/>
          <path d="M38 7H322" fill="none" stroke="#3d2c15" strokeWidth="1" opacity="0.48" vectorEffect="non-scaling-stroke"/>
          <path d="M15 7l5-3 5 3-5 3-5-3ZM335 7l5-3 5 3-5 3-5-3Z" fill="#8d6f3b" stroke="#3a250f" strokeWidth="0.8" filter="url(#srpGoldShadow)"/>
        </symbol>
        <symbol id="srpInputFrame" viewBox="0 0 360 112">
          <path d="M14 3H346L357 14V98L346 109H14L3 98V14L14 3Z" fill="none" stroke="#2c2113" strokeWidth="3" vectorEffect="non-scaling-stroke" opacity="0.75"/>
          <path d="M15 4H345L356 15V97L345 108H15L4 97V15L15 4Z" fill="none" stroke="#837453" strokeWidth="1.4" vectorEffect="non-scaling-stroke" opacity="0.75"/>
          <path d="M19 8H341L352 19M8 19V93M19 104H341L352 93" fill="none" stroke="#ddd1aa" strokeWidth="0.7" vectorEffect="non-scaling-stroke" opacity="0.35"/>
        </symbol>
        <symbol id="srpSubmitFrame" viewBox="0 0 360 58">
          <path d="M16 4H344L356 16L348 54H12L4 16L16 4Z" fill="url(#srpBlue)" stroke="#111827" strokeWidth="2.6" vectorEffect="non-scaling-stroke"/>
          <path d="M18 7H342L352 17L345 51H15L8 17L18 7Z" fill="none" stroke="url(#srpGold)" strokeWidth="1.45" vectorEffect="non-scaling-stroke" filter="url(#srpGoldShadow)"/>
          <path d="M24 12H336L346 20L340 46H20L14 20L24 12Z" fill="none" stroke="#2e6792" strokeWidth="1" vectorEffect="non-scaling-stroke" opacity="0.9"/>
          <circle cx="16" cy="29" r="2.3" fill="#9a7538" stroke="#071827" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
          <circle cx="344" cy="29" r="2.3" fill="#9a7538" stroke="#071827" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
        </symbol>
      </defs>
    </svg>
  );
}

/* ── Corner helpers ──────────────────────────────────────────────────────── */

function SlpCorners() {
  return (<>
    <svg className="slp-corner slp-corner--tl" aria-hidden="true"><use href="#slpCorner"/></svg>
    <svg className="slp-corner slp-corner--tr" aria-hidden="true"><use href="#slpCorner"/></svg>
    <svg className="slp-corner slp-corner--bl" aria-hidden="true"><use href="#slpCorner"/></svg>
    <svg className="slp-corner slp-corner--br" aria-hidden="true"><use href="#slpCorner"/></svg>
  </>);
}

function SrpCorners() {
  return (<>
    <svg className="srp-corner srp-corner--tl" aria-hidden="true"><use href="#srpCorner"/></svg>
    <svg className="srp-corner srp-corner--tr" aria-hidden="true"><use href="#srpCorner"/></svg>
    <svg className="srp-corner srp-corner--bl" aria-hidden="true"><use href="#srpCorner"/></svg>
    <svg className="srp-corner srp-corner--br" aria-hidden="true"><use href="#srpCorner"/></svg>
  </>);
}

function SsbBC({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 17 17" fill="none" aria-hidden="true">
      <path d="M2 16V6Q2 2 6 2H16" stroke="#8d6f3b" strokeWidth="1.3"/>
      <path d="M7.5 7.5Q10.4 7.5 10.4 10.4" stroke="#8d6f3b" strokeWidth="1" opacity="0.85"/>
      <circle cx="7.4" cy="7.4" r="0.9" fill="#8d6f3b"/>
    </svg>
  );
}

/* ── TopBar ──────────────────────────────────────────────────────────────── */

function TopBar({ onAcademy, audioSettings }) {
  return (
    <header className="slt-topbar" role="banner">
      <span className="slt-edge slt-edge--top" aria-hidden="true"/>
      <span className="slt-edge slt-edge--bottom" aria-hidden="true"/>
      <span className="slt-hairline slt-hairline--top" aria-hidden="true"/>
      <span className="slt-hairline slt-hairline--bottom" aria-hidden="true"/>
      <svg className="slt-corner slt-corner--left" aria-hidden="true" focusable="false"><use href="#sltCorner"/></svg>
      <svg className="slt-corner slt-corner--right" aria-hidden="true" focusable="false"><use href="#sltCorner"/></svg>
      <h1 className="slt-title">Socratic Lecture Tutor</h1>
      <nav className="slt-nav" aria-label="상단 메뉴">
        {onAcademy && (
          <button type="button" className="slt-nav-button" onClick={onAcademy}>
            <svg className="slt-nav-icon" aria-hidden="true"><use href="#sltIconAcademy"/></svg>
            <span>학당</span>
          </button>
        )}
        {audioSettings}
      </nav>
    </header>
  );
}

/* ── Main App ────────────────────────────────────────────────────────────── */

export function App() {
  const [file, setFile] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [state, setState] = useState(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadingSteps, setLoadingSteps] = useState([]);
  const [dismissedTransitionAnswerId, setDismissedTransitionAnswerId] = useState(null);
  const [audioSettingsOpen, setAudioSettingsOpen] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(0.32);
  const [questionSoundVolume, setQuestionSoundVolume] = useState(0.72);
  const backgroundMusicRef = useRef(null);
  const questionChangeSoundRef = useRef(null);
  const previousQuestionIdRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`, { cache: "no-store" }).catch(() => {});
    const sessionId = window.localStorage.getItem(ACTIVE_SESSION_KEY);
    if (!sessionId) return;
    setBusy(true);
    fetch(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store" })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          if (response.status === 404) window.localStorage.removeItem(ACTIVE_SESSION_KEY);
          throw new Error(payload.detail || "이전 학습 세션을 불러오지 못했습니다.");
        }
        setState(payload);
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }, []);

  const concepts = state?.session?.concepts ?? [];
  const isConceptReview = state?.session_mode === "concept_review";
  const answers = isConceptReview ? (state?.session?.concept_answers ?? []) : (state?.session?.answers ?? []);
  const currentQuestion = state?.current_question;
  const lastAnswer = state?.last_answer;
  const answeredQuestion = lastAnswer
    ? state?.session?.questions?.find((question) => question.question_id === lastAnswer.question_id)
    : null;
  const progress = state ? Math.round((state.current_index / Math.max(state.total_questions, 1)) * 100) : 0;
  const lastAnswerIsForCurrentQuestion = lastAnswer?.question_id === currentQuestion?.question_id;
  const showFollowupEvaluation = !isConceptReview &&
    lastAnswer?.evaluation && lastAnswerIsForCurrentQuestion && lastAnswer.evaluation.status !== "sufficient";
  const showTransitionEvaluation = !isConceptReview &&
    lastAnswer?.evaluation && lastAnswer.evaluation.next_action === "next_question" &&
    lastAnswer.answer_text !== "/skip" && !lastAnswerIsForCurrentQuestion &&
    dismissedTransitionAnswerId !== lastAnswer.answer_id;
  const showEvaluationMessage = Boolean(showTransitionEvaluation || (!state?.completed && showFollowupEvaluation));
  const visibleQuestionId = showEvaluationMessage ? lastAnswer?.question_id : currentQuestion?.question_id;
  const adviceText = showEvaluationMessage ? getAdviceText(lastAnswer?.evaluation) : null;
  const visibleAttemptCount = showEvaluationMessage
    ? (lastAnswer?.attempt_number ?? 0)
    : answers.filter((item) => item.question_id === currentQuestion?.question_id).length;

  const currentConcept = useMemo(() => {
    if (!currentQuestion) return null;
    return concepts.find((concept) => concept.concept_id === currentQuestion.concept_id);
  }, [concepts, currentQuestion]);

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
  }, [backgroundMusicVolume]);

  useEffect(() => {
    if (questionChangeSoundRef.current) questionChangeSoundRef.current.volume = questionSoundVolume;
  }, [questionSoundVolume]);

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
    if (form.model) payload.append("model", form.model);

    const addStep = (label) => {
      setLoadingSteps((prev) => [...prev, { label, done: false }]);
    };
    const completeStep = (label) => {
      setLoadingSteps((prev) =>
        prev.map((s) => s.label === label && !s.done ? { ...s, done: true } : s)
      );
    };
    const updateStep = (newLabel) => {
      setLoadingSteps((prev) =>
        prev.map((s, i) => i === prev.length - 1 ? { ...s, label: newLabel } : s)
      );
    };

    try {
      const response = await fetch(`${API_BASE}/api/sessions/stream`, { method: "POST", body: payload });

      // 서버가 아직 /stream 엔드포인트를 모를 때 (배포 전) → 기존 방식으로 폴백
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
          try { evt = JSON.parse(text); } catch { continue; }

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
            setLoadingSteps((prev) => prev.map((s) => ({ ...s, done: true })));
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

  /* ── Start screen ────────────────────────────────────────────────────── */

  if (!state) {
    return (
      <div style={{ background: "#050504" }}>
        <SvgDefs/>
        <div className="app-bg">
          <div className="app-bg-overlay"/>
          <div className="start-socrates-abs">
            <img src="/theme-assets/socrates-start-new.png" alt="AI 소크라테스"/>
          </div>
          <div className="app-frame">
            <TopBar audioSettings={audioSettings}/>

            <div className="start-body">
              {/* Upload panel */}
              <section className="slp-panel slp-panel--upload" aria-label="학습 시작">
                <SlpCorners/>
                <div className="slp-upload-scroll-area" style={{ position: "relative", zIndex: 5 }}>
                  <div className="parch-stage-ribbon">1단계: 입문</div>
                  <p className="parch-upload-title">지식의 두루마리를 제출하세요</p>
                  <p className="parch-upload-desc">
                    공부할 강의 PDF를 제출하면 소크라테스가 두루마리를 해석하여 핵심 개념을 찾아냅니다.
                  </p>
                  {error && <div className="parch-error">{error}</div>}
                  <form onSubmit={startSession} className="parch-form">
                    <label className="parch-dropzone">
                      <input type="file" accept="application/pdf,.pdf" onChange={selectPdf}/>
                      <FileUp size={24} style={{ opacity: 0.7 }}/>
                      <span>{file ? file.name : "강의 PDF 선택"}</span>
                    </label>
                    <div className="parch-upload-hint">
                      여기에 PDF 파일을 드래그하거나 클릭하여 업로드하세요.
                    </div>
                    <div className="parch-segmented" aria-label="난이도">
                      {["easy", "normal", "hard"].map((v) => (
                        <button
                          key={v} type="button"
                          className={form.difficulty === v ? "active" : ""}
                          onClick={() => setForm({ ...form, difficulty: v })}
                        >{v}</button>
                      ))}
                    </div>
                    <div className="parch-segmented" aria-label="학습 방식">
                      <button type="button" className={form.sessionMode === "study" ? "active" : ""}
                        onClick={() => setForm({ ...form, sessionMode: "study" })}>질문 학습</button>
                      <button type="button" className={form.sessionMode === "concept_review" ? "active" : ""}
                        onClick={() => setForm({ ...form, sessionMode: "concept_review" })}>개념 리포트</button>
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
                        {loadingSteps.map((step, i) => (
                          <div key={i} className={`loading-step ${step.done ? "loading-step--done" : "loading-step--active"}`}>
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

              {/* Info panel */}
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
          </div>
        </div>
      </div>
    );
  }

  /* ── Study screen ────────────────────────────────────────────────────── */

  const questionText = state.completed
    ? "오늘의 학습 여정이 끝났네. 기록서를 살펴보게."
    : currentQuestion?.question ?? "";

  return (
    <div style={{ background: "#050504" }}>
      <SvgDefs/>
      <div className="app-bg">
        <div className="app-bg-overlay"/>
        <div className="app-frame">
          <TopBar
            onAcademy={() => {
              window.localStorage.removeItem(ACTIVE_SESSION_KEY);
              setState(null);
              setAnswer("");
            }}
            audioSettings={audioSettings}
          />

          {/* Socrates character */}
          <div className="study-socrates">
            <img src="/theme-assets/socrates.png" alt="AI 소크라테스"/>
          </div>

          <div className="app-body">
            {/* ── Left column ── */}
            <div className="slp-component">
              <div className="slp-sidebar">
                <section className="slp-panel slp-panel--lessons" aria-labelledby="gate-title">
                  <SlpCorners/>
                  <h2 className="slp-panel-title" id="gate-title">학문의 관문</h2>
                  <svg className="slp-title-divider" aria-hidden="true"><use href="#slpTitleDivider"/></svg>
                  <ol className="slp-lessons">
                    {concepts.map((concept, index) => {
                      const isActive = currentConcept?.concept_id === concept.concept_id;
                      const isPassed = state.current_index > index;
                      const lessonState = isPassed ? "complete" : isActive ? "active" : "locked";
                      const iconHref = lessonState === "complete" ? "#slpCompass" : lessonState === "active" ? "#slpChevron" : "#slpLock";
                      const iconCls = lessonState === "complete" ? "slp-state-icon slp-state-icon--compass" : lessonState === "active" ? "slp-state-icon slp-state-icon--chevron" : "slp-state-icon slp-state-icon--lock";
                      return (
                        <li key={concept.concept_id} className="slp-lesson-item">
                          <button
                            className={`slp-lesson-button is-${lessonState}`}
                            type="button"
                            disabled={lessonState === "locked"}
                            aria-current={isActive ? "step" : undefined}
                          >
                            <span className="slp-lesson-number">{index + 1}</span>
                            <span className="slp-lesson-label">{concept.title}</span>
                            <svg className={iconCls} aria-hidden="true"><use href={iconHref}/></svg>
                          </button>
                        </li>
                      );
                    })}
                  </ol>
                </section>

                <section className="slp-panel slp-panel--journey" aria-labelledby="journey-title">
                  <SlpCorners/>
                  <h2 className="slp-panel-title slp-panel-title--journey" id="journey-title">오늘의 여정</h2>
                  <div className="slp-progress-head">
                    <span>완료한 관문</span>
                    <strong>{Math.min(state.current_index, state.total_questions)} / {state.total_questions}</strong>
                  </div>
                  <div className="slp-progress-track" aria-label={`진행률 ${progress}%`}>
                    <span className="slp-progress-fill" style={{ width: `${progress}%` }}/>
                  </div>
                  <dl className="slp-stats">
                    <div className="slp-stat-row"><dt>답변 기록</dt><dd>{answers.length}</dd></div>
                    <div className="slp-stat-row">
                      <dt>현재 점수</dt>
                      <dd>{lastAnswer?.evaluation ? `${Math.round(lastAnswer.evaluation.score * 100)}점` : "-"}</dd>
                    </div>
                  </dl>
                </section>
              </div>
            </div>

            {/* ── Center column ── */}
            <div className="study-main">
              <div style={{ display: "flex", justifyContent: "center", paddingTop: 8 }}>
                <div className="ssb-component">
                  <div className="ssb-speech">
                    <div className="ssb-speech-name"><span>소크라테스</span></div>
                    <div className="ssb-speech-bubble">
                      {showEvaluationMessage ? (
                        <p className="ssb-speech-text">
                          <strong style={{ display: "block", marginBottom: 6 }}>
                            {Math.round(lastAnswer.evaluation.score * 100)}점 · {statusLabel(lastAnswer.evaluation.status)}
                          </strong>
                          {lastAnswer.evaluation.feedback_to_student}
                        </p>
                      ) : (
                        <p className="ssb-speech-text">{questionText}</p>
                      )}
                      <SsbBC cls="ssb-bc"/><SsbBC cls="ssb-bc ssb-bc--tr"/>
                      <SsbBC cls="ssb-bc ssb-bc--bl"/><SsbBC cls="ssb-bc ssb-bc--br"/>
                    </div>
                  </div>
                </div>
              </div>

              {showTransitionEvaluation && (
                <div style={{ display: "flex", justifyContent: "center" }}>
                  <button
                    type="button"
                    className="srp-submit-button"
                    style={{ maxWidth: 260, marginTop: 8 }}
                    onClick={() => setDismissedTransitionAnswerId(lastAnswer.answer_id)}
                  >
                    <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true">
                      <use href="#srpSubmitFrame"/>
                    </svg>
                    <span>{state.completed ? "기록서 보기" : "다음 질문으로"}</span>
                  </button>
                </div>
              )}

              {adviceText && (
                <div style={{ display: "flex", justifyContent: "center", paddingBottom: 8 }}>
                  <div className="adv-wrap">
                    <div className="adv-label">소크라테스의 조언</div>
                    <div className="adv-text">{adviceText}</div>
                  </div>
                </div>
              )}
            </div>

            {/* ── Right column ── */}
            <div className="srp-component">
              <div className="srp-right-stack">
                {/* Answer / Transition / Summary card */}
                <section className="srp-card srp-card--answer" aria-labelledby="answer-card-title">
                  <SrpCorners/>
                  <div className="srp-card-content">
                    {!state.completed && currentQuestion && !showTransitionEvaluation && (
                      <form onSubmit={submitAnswer}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                          <h2 className="srp-answer-title" id="answer-card-title">그대의 답변을 입력하세요.</h2>
                          <span className="attempt-badge">
                            {isConceptReview ? `개념 ${state.current_index + 1} / ${state.total_questions}` : `시도 ${visibleAttemptCount} / ${MAX_ATTEMPTS_PER_QUESTION}`}
                          </span>
                        </div>
                        <svg className="srp-divider" viewBox="0 0 360 14" preserveAspectRatio="none" aria-hidden="true"><use href="#srpDivider"/></svg>
                        <p className="srp-answer-copy">완벽하지 않아도 괜찮습니다.<br/>{isConceptReview ? "이 개념에 대해 이해한 내용을 자유롭게 적어보세요." : "생각을 드러내는 것이 먼저입니다."}</p>
                        <label className="srp-textarea-shell">
                          <span className="visually-hidden">답변 입력</span>
                          <textarea
                            className="srp-textarea"
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                            placeholder="여기에 답변을 입력하세요..."
                          />
                          <svg className="srp-input-frame" viewBox="0 0 360 112" preserveAspectRatio="none" aria-hidden="true"><use href="#srpInputFrame"/></svg>
                        </label>
                        <div className="srp-shortcuts">
                          <button type="button" className="srp-shortcut" disabled={busy} onClick={() => postAction("skip")}><strong>/skip</strong><span>건너뛰기</span></button>
                          <button type="button" className="srp-shortcut" disabled={busy} onClick={() => postAction("finish")}><strong>/quit</strong><span>종료</span></button>
                        </div>
                        <button className="srp-submit-button" type="submit" disabled={busy || !answer.trim()}>
                          <svg className="srp-submit-frame" viewBox="0 0 360 58" preserveAspectRatio="none" aria-hidden="true"><use href="#srpSubmitFrame"/></svg>
                          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            {busy ? <Loader2 className="spin" size={18}/> : <Send size={18}/>}
                            답변 제출
                          </span>
                        </button>
                      </form>
                    )}

                    {showTransitionEvaluation && answeredQuestion && (
                      <div>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                          <h2 className="srp-answer-title">이전 답변 평가</h2>
                          <span className="attempt-badge">시도 {visibleAttemptCount} / {MAX_ATTEMPTS_PER_QUESTION}</span>
                        </div>
                        <svg className="srp-divider" viewBox="0 0 360 14" preserveAspectRatio="none" aria-hidden="true"><use href="#srpDivider"/></svg>
                        <div style={{ marginTop: 8, padding: "8px 10px", background: "rgba(0,0,0,0.06)", borderRadius: 4, borderLeft: "2px solid rgba(99,75,42,.4)" }}>
                          <p style={{ margin: "0 0 4px", color: "#5b4020", fontSize: 14, fontWeight: 760, letterSpacing: "0.04em" }}>질문</p>
                          <p style={{ margin: 0, color: "#3a260f", fontSize: 16, lineHeight: 1.58, fontWeight: 620 }}>{answeredQuestion.question}</p>
                        </div>
                      </div>
                    )}

                    {state.completed && state.session.summary && (
                      <>
                        <h2 className="srp-summary-title">학습 기록서</h2>
                        <svg className="srp-divider" viewBox="0 0 360 14" preserveAspectRatio="none" aria-hidden="true"><use href="#srpDivider"/></svg>
                        <p className="srp-summary-text">{state.session.summary.overall_feedback}</p>
                        <div className="srp-summary-section">
                          <h3>강한 개념</h3>
                          {state.session.summary.strong_concepts.length
                            ? <ul>{state.session.summary.strong_concepts.map((i) => <li key={i}>{i}</li>)}</ul>
                            : <p className="srp-muted">기록 없음</p>}
                        </div>
                        {isConceptReview && (
                          <div className="srp-summary-section">
                            <h3>개념별 필수 요소 리포트</h3>
                            {concepts.map((concept) => (
                              <div key={concept.concept_id} style={{ marginBottom: 14 }}>
                                <strong>{concept.title}</strong>
                                {state.session.questions.filter((q) => q.concept_id === concept.concept_id).map((question) => {
                                  const result = state.session.answers.find((item) => item.question_id === question.question_id);
                                  return (
                                    <div key={question.question_id} style={{ marginTop: 8 }}>
                                      <p className="srp-muted">{question.question_type}</p>
                                      <p>충족: {result?.evaluation?.matched_points?.join(", ") || "없음"}</p>
                                      <p>미충족: {result?.evaluation?.missing_points?.join(", ") || "없음"}</p>
                                    </div>
                                  );
                                })}
                              </div>
                            ))}
                          </div>
                        )}
                        <div className="srp-summary-section">
                          <h3>복습 개념</h3>
                          {state.session.summary.weak_concepts.length
                            ? <ul>{state.session.summary.weak_concepts.map((i) => <li key={i}>{i}</li>)}</ul>
                            : <p className="srp-muted">기록 없음</p>}
                        </div>
                      </>
                    )}
                  </div>
                </section>

                {/* Records card */}
                <section className="srp-card srp-card--records" aria-labelledby="record-card-title">
                  <SrpCorners/>
                  <div className="srp-card-content">
                    <header className="srp-record-header">
                      <h2 className="srp-record-title" id="record-card-title">학습 기록서 <span>(이번 세션)</span></h2>
                    </header>
                    <svg className="srp-divider" viewBox="0 0 360 14" preserveAspectRatio="none" aria-hidden="true" style={{ height: 10, margin: "4px 0" }}><use href="#srpDivider"/></svg>
                    <dl className="srp-stats">
                      <div className="srp-stat-row"><dt>통과한 관문</dt><dd>{Math.min(state.current_index, state.total_questions)}</dd></div>
                      <div className="srp-stat-row"><dt>총 질문 수</dt><dd>{state.total_questions}</dd></div>
                      <div className="srp-stat-row"><dt>응답 수</dt><dd>{answers.length}</dd></div>
                    </dl>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── AudioSettings ───────────────────────────────────────────────────────── */

function AudioSettings({
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

/* ── helpers ─────────────────────────────────────────────────────────────── */

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
  if (!response.ok) throw new Error(payload.detail || "요청을 처리하지 못했습니다.");
  return payload;
}
