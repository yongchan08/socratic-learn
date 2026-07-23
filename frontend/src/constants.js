export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
export const BACKGROUND_MUSIC_SRC = "/audio/background_music.mp3";
export const QUESTION_CHANGE_SOUND_SRC = "/audio/page-turn.mp3";
export const BUTTON_HOVER_SOUND_SRC = "/audio/button_hover_sound.mp3";
export const MAX_ATTEMPTS_PER_QUESTION = 3;
export const MAX_PDF_BYTES = 25 * 1024 * 1024;
export const ACTIVE_SESSION_KEY = "socratic_tutor_active_session_id";
export const ACTIVE_COURSE_KEY = "socratic_tutor_active_course_id";
export const ADMIN_AUTH_KEY = "socratic_tutor_admin_authenticated";
export const BACKGROUND_VOLUME_KEY = "socratic_tutor_background_music_volume";
export const EFFECT_VOLUME_KEY = "socratic_tutor_effect_volume";
export const ADMIN_PASSWORD = "1004";

export const initialForm = {
  difficulty: "normal",
  outputLanguage: "ko",
  model: "",
  sessionMode: "study",
};
