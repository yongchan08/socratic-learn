-- schema.sql
-- 정규화된 관계형 데이터베이스 스키마 초안

-- 1. Documents & Materials (학습 자료)
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    file_hash TEXT UNIQUE NOT NULL,
    title TEXT,
    source_path TEXT NOT NULL,
    markdown_content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PDF의 각 페이지 정보를 분리 저장 (선택 사항, 기존 pages 리스트 대응)
CREATE TABLE IF NOT EXISTS document_pages (
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    markdown TEXT NOT NULL,
    PRIMARY KEY (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    difficulty TEXT NOT NULL,
    output_language TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    importance TEXT NOT NULL,
    source_pages INTEGER[] NOT NULL DEFAULT '{}',
    evidence_from_material TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    question_type TEXT NOT NULL, -- 'explanation', 'comparison', 'application'
    question_text TEXT NOT NULL,
    source_pages INTEGER[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS required_points (
    point_id TEXT NOT NULL,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    gentle_hint TEXT NOT NULL,
    direct_hint TEXT NOT NULL,
    PRIMARY KEY (point_id, question_id)
);


-- 2. Sessions & Answers (사용자 학습 데이터)
CREATE TABLE IF NOT EXISTS study_sessions (
    session_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    session_mode TEXT NOT NULL,
    difficulty TEXT NOT NULL DEFAULT 'normal',
    output_language TEXT NOT NULL DEFAULT 'ko',
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    completion_status TEXT, -- 'completed', 'ended_early'
    end_reason TEXT,        -- 'all_answered', 'user_quit'
    document_title TEXT,
    config_data JSONB,      -- 유연한 설정 저장을 위해 남겨둠
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS concept_answers (
    answer_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES study_sessions(session_id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_answers (
    answer_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES study_sessions(session_id) ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    answer_text TEXT NOT NULL,
    score FLOAT NOT NULL,
    status TEXT NOT NULL, -- 'sufficient', 'partially_sufficient', 'insufficient', 'misconception'
    feedback_to_student TEXT NOT NULL,
    hint TEXT,
    improvement_note TEXT,
    socratic_follow_up TEXT,
    reveal_missing_points BOOLEAN NOT NULL DEFAULT FALSE,
    next_action TEXT NOT NULL, -- 'next_question', 'ask_followup'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS answer_evaluations (
    evaluation_id SERIAL PRIMARY KEY,
    answer_id TEXT NOT NULL REFERENCES student_answers(answer_id) ON DELETE CASCADE,
    matched_point_ids TEXT[] NOT NULL DEFAULT '{}',
    matched_points TEXT[] NOT NULL DEFAULT '{}',
    missing_points TEXT[] NOT NULL DEFAULT '{}',
    misconceptions TEXT[] NOT NULL DEFAULT '{}'
);

-- 3. Courses (학습 로드맵)
-- (Courses 테이블은 여러 세션을 묶는 용도이므로 간단히 유지하거나 추가 확장 가능)
CREATE TABLE IF NOT EXISTS learning_courses (
    course_id TEXT PRIMARY KEY,
    course_data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
