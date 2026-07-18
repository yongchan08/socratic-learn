# 프론트엔드 API와 학습 기능별 동작

이 문서는 프론트엔드가 사용하는 API와 소크라테스 학습 기능(`study`), 파인만 학습 기능(`concept_review`)의 요청별 동작을 설명한다. 공통 데이터 모델과 두 학습 기능의 데이터 흐름은 [a-b-data-flow.md](./a-b-data-flow.md)를 참고한다.

프론트엔드는 FastAPI 서버와 HTTP 및 SSE(Server-Sent Events)로 통신한다. API 기본 주소는 프론트엔드의 `API_BASE` 설정을 사용한다.

현재 프론트엔드가 직접 호출하는 API는 다음과 같다.

| 메서드 | 경로 | 용도 |
| --- | --- | --- |
| `GET` | `/api/health` | 서버 콜드 스타트 완화 및 상태 확인 |
| `POST` | `/api/sessions/stream` | PDF 업로드, 소크라테스/파인만 학습 세션 생성, 진행 상황 수신 |
| `POST` | `/api/sessions/{session_id}/answers` | 현재 질문 또는 개념에 대한 답변 제출 |
| `POST` | `/api/sessions/{session_id}/skip` | 현재 질문 또는 개념 건너뛰기 |
| `POST` | `/api/sessions/{session_id}/finish` | 현재까지의 답변으로 세션 종료 및 요약 생성 |

서버에는 일반 세션 생성 및 조회 API도 있지만 현재 프론트엔드에서는 직접 호출하지 않는다.

| 메서드 | 경로 | 현재 프론트 사용 여부 |
| --- | --- | --- |
| `POST` | `/api/sessions` | 사용하지 않음. 스트리밍 없는 세션 생성 API |
| `GET` | `/api/sessions/{session_id}` | 새로고침 후 저장된 세션 snapshot 복구 |

## 1. 서버 상태 확인

```http
GET /api/health
```

프론트엔드가 처음 마운트될 때 한 번 호출한다.

```json
{
  "status": "ok"
}
```

이 요청은 학습 데이터를 생성하지 않는다. 배포 서버가 유휴 상태에서 내려간 경우 서버를 미리 깨우고 연결 가능 여부를 확인하는 역할을 한다. 프론트엔드는 이 요청의 실패를 화면에 표시하지 않는다.

## 2. 소크라테스/파인만 학습 세션 생성

```http
POST /api/sessions/stream
Content-Type: multipart/form-data
```

프론트엔드는 다음 필드를 `FormData`로 전송한다.

| 필드 | 형식 | 설명 |
| --- | --- | --- |
| `pdf` | PDF 파일 | 학습할 원본 PDF, 최대 25MB |
| `difficulty` | `easy`, `normal`, `hard` | 질문과 평가 난이도 |
| `output_language` | `ko`, `en` | 질문·피드백·요약 언어 |
| `session_mode` | `study`, `concept_review` | 소크라테스 또는 파인만 학습 선택 |
| `model` | 문자열, 선택 | 지정하지 않으면 서버 기본 모델 사용 |

소크라테스 학습 기능을 시작하는 요청의 논리적 형태는 다음과 같다.

```text
pdf = Redis.pdf
difficulty = normal
output_language = ko
session_mode = study
```

파인만 학습 기능을 시작할 때는 다음 값만 달라진다.

```text
session_mode = concept_review
```

서버는 업로드된 PDF를 `uploads/<random_id>/<filename>.pdf`에 임시 저장하고 처리 완료 또는 실패 후 삭제한다.

#### 소크라테스 학습 생성 흐름

```text
POST /api/sessions/stream
→ PostgreSQL에서 PDF 파싱 결과 조회 또는 새로 파싱
→ PostgreSQL에서 Concept 조회 또는 새로 생성
→ PostgreSQL에서 Question 조회 또는 새로 생성
→ StudySession 생성
→ 완료 snapshot 반환
```

#### 파인만 학습 생성 흐름

```text
POST /api/sessions/stream
→ PDF 파싱 또는 캐시 로드
→ document_id 확인
→ PostgreSQL에서 기존 Concept/Question 로드
→ StudySession 생성
→ 완료 snapshot 반환
```

파인만 학습 기능에서는 Concept과 Question을 새로 생성하지 않는다. 동일한 PDF 해시·난이도·언어의 소크라테스 학습 자료가 PostgreSQL에 없으면 SSE의 `error` 이벤트로 실패한다.

## 3. SSE 진행 이벤트

`/api/sessions/stream` 응답의 Content-Type은 `text/event-stream`이다. 각 이벤트는 다음 형태로 전달된다.

```text
data: {"step":"parsing","message":"📜 두루마리를 해독하는 중..."}
```

프론트엔드가 처리하는 `step` 값은 다음과 같다.

| `step` | 의미 | 주요 필드 |
| --- | --- | --- |
| `parsing` | PDF 처리 시작 | `message` |
| `concepts` | PDF 파싱 완료, 개념 단계 진입 | `message` |
| `questions_start` | 개념 생성 완료, 질문 생성 시작 | `message` |
| `questions` | 개념별 질문 생성 진행 | `message`, `done`, `total` |
| `done` | 세션 생성 완료 | `payload` |
| `error` | 세션 생성 실패 | `message` |

`questions` 이벤트의 `done`과 `total`은 질문 개수가 아니라 질문 생성을 완료한 Concept 개수와 전체 Concept 개수다.

연결 유지를 위해 서버는 15초마다 다음 heartbeat comment를 보낼 수 있다.

```text
: heartbeat
```

heartbeat는 학습 데이터가 아니며 프론트엔드는 무시한다.

## 4. 세션 snapshot

세션 생성, 답변, 건너뛰기, 종료 API는 모두 최신 화면 상태를 나타내는 snapshot을 반환한다.

#### 소크라테스 학습 snapshot

```json
{
  "session": {
    "session_id": "session_...",
    "document_id": "doc_...",
    "concepts": [],
    "questions": [],
    "concept_answers": [],
    "answers": [],
    "summary": null,
    "started_at": "...",
    "ended_at": null
  },
  "current_question": {},
  "current_index": 0,
  "total_questions": 10,
  "last_answer": null,
  "completed": false
}
```

- `current_question`: 현재 화면에 표시할 실제 Question
- `current_index`: 현재 Question 인덱스
- `total_questions`: 전체 Question 수
- `last_answer`: 가장 최근 StudentAnswer
- `completed`: 세션 종료 여부

#### 파인만 학습 snapshot

```json
{
  "session": {},
  "session_mode": "concept_review",
  "current_question": {
    "question_id": "concept_prompt_concept_001",
    "concept_id": "concept_001",
    "question_type": "explanation",
    "question": "Redis 영속성",
    "required_points": [],
    "source_pages": [12, 13]
  },
  "current_index": 0,
  "total_questions": 5,
  "last_answer": null,
  "completed": false
}
```

파인만 학습의 `current_question`은 저장된 실제 Question이 아니다. 프론트엔드의 기존 질문 화면을 재사용하기 위해 Concept 제목으로 만든 임시 표시 객체다.

파인만 학습에서 `total_questions`라는 응답 필드명은 유지되지만 실제 의미는 전체 Concept 수다.

## 5. 답변 제출

```http
POST /api/sessions/{session_id}/answers
Content-Type: application/json
```

```json
{
  "answer": "사용자의 답변"
}
```

#### 소크라테스 학습에서의 처리

```text
현재 Question 조회
→ 사용자 답변 LLM 평가
→ StudentAnswer 추가
→ 평가 결과에 따라 같은 질문 유지 또는 다음 질문 이동
→ 최신 소크라테스 학습 snapshot 반환
```

#### 파인만 학습에서의 처리

```text
현재 Concept 조회
→ ConceptAnswer 추가
→ 다음 Concept으로 이동
→ 마지막 Concept이면 전체 답변 일괄 평가 및 요약
→ 최신 파인만 학습 snapshot 반환
```

파인만 학습의 개념 답변 수집 중에는 LLM을 호출하지 않는다. 마지막 Concept 답변을 제출하여 세션이 종료될 때 각 ConceptAnswer를 연결된 두 Question으로 일괄 평가한다.

## 6. 건너뛰기

```http
POST /api/sessions/{session_id}/skip
```

요청 본문은 없다.

#### 소크라테스 학습에서의 처리

현재 Question에 대해 다음 StudentAnswer를 기록하고 다음 Question으로 이동한다.

```text
answer_text = /skip
matched_points = []
missing_points = 현재 Question의 모든 required_points[].text
score = 0
status = insufficient
```

#### 파인만 학습에서의 처리

현재 Concept의 ConceptAnswer에 `answer_text = /skip`을 기록하고 다음 Concept으로 이동한다. 세션 종료 시 해당 개념의 두 Question 모두 미충족 평가로 변환된다.

## 7. 세션 종료

```http
POST /api/sessions/{session_id}/finish
```

요청 본문은 없다.

#### 소크라테스 학습 종료

```text
현재까지의 StudentAnswer
→ SessionSummary 생성
→ ended_at 기록
→ PostgreSQL의 web_study_sessions에 최종 상태 저장
→ completed = true snapshot 반환
```

#### 파인만 학습 종료

```text
현재까지의 ConceptAnswer
→ 연결된 Question별 일괄 평가
→ SessionSummary 생성
→ ended_at 기록
→ PostgreSQL의 web_study_sessions에 최종 상태 저장
→ completed = true snapshot 반환
```

`finish`는 사용자가 중간 종료 버튼을 눌렀을 때도 사용한다. 마지막 답변 제출 시에는 서버가 내부적으로 자동 종료할 수도 있다.

## 8. 오류 응답

일반 JSON API 오류는 FastAPI의 `detail` 필드를 사용한다.

```json
{
  "detail": "학습 세션을 찾을 수 없습니다."
}
```

프론트엔드의 공통 `request()` 함수는 HTTP 상태가 성공이 아니면 `detail`을 사용자 오류 메시지로 표시한다.

세션 생성 스트림에서 작업 도중 발생한 오류는 HTTP 응답을 새로 만들 수 없으므로 SSE 이벤트로 전달한다.

```text
data: {"step":"error","message":"오류 내용"}
```

주요 오류 상황은 다음과 같다.

- PDF 확장자 또는 파일 시그니처가 올바르지 않음
- PDF가 25MB를 초과함
- OpenAI API 키가 없음
- LLM 호출 실패 또는 시간 초과
- 파인만 학습에 필요한 소크라테스 학습의 Concept/Question DB 레코드가 없음
- `DATABASE_URL` 미설정 상태에서 서버가 재시작되어 메모리의 `session_id`가 사라짐

## 9. API와 WebStudyManager의 연결

FastAPI 엔드포인트는 직접 학습 로직을 구현하지 않고 `WebStudyManager`에 위임한다.

```text
POST /api/sessions/stream
→ WebStudyManager.create_session()

POST /answers
→ WebStudyManager.answer()

POST /skip
→ WebStudyManager.skip()

POST /finish
→ WebStudyManager.finish()

API 응답 생성
→ WebStudyManager.snapshot()
```

프론트엔드는 활성 `session_id`를 `localStorage`에 보관하고, 마운트 시 `GET /api/sessions/{session_id}`로 snapshot을 복구한다. 사용자가 학당 버튼으로 시작 화면으로 돌아가면 저장된 활성 `session_id`를 제거한다.

`DATABASE_URL`이 설정된 경우 `WebStudyManager`는 StudySession, 현재 인덱스, 설정과 학습 모드를 PostgreSQL의 `web_study_sessions` 테이블에 JSONB로 저장한다. 메모리에 세션이 없으면 데이터베이스에서 복원하므로 브라우저 새로고침과 서버 재시작 후에도 이어갈 수 있다. API 키는 데이터베이스에 저장하지 않고 복원 시 서버 환경에서 다시 읽는다. `DATABASE_URL`이 없으면 기존처럼 서버 메모리만 사용한다.

웹에서 파싱한 문서는 `learning_documents`에 PDF SHA-256 해시와 `ParsedDocument` JSONB로 저장한다. Concept과 Question은 `learning_materials`에 PDF 해시·난이도·출력 언어 조합별 JSONB로 저장하며, 이후 같은 조합의 업로드에서 생성 캐시로 재사용한다. 따라서 `DATABASE_URL`이 설정된 웹 흐름은 `outputs/`와 `cache/` 폴더를 읽거나 쓰지 않는다. 원본 PDF는 DB에 저장하지 않고 분석 완료 후 삭제한다.
