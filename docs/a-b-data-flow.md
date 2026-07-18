# 소크라테스/파인만 학습 기능의 데이터 구조와 상호작용

이 문서는 소크라테스 학습 기능과 파인만 학습 기능이 PDF에서 생성된 데이터를 어떻게 생성하고 공유하며 평가에 사용하는지 설명합니다.

## 전체 흐름

```text
PDF
 │
 ▼
ParsedDocument
 │
 ├─ 전체·페이지별 PDF 본문
 │
 ▼
Concept 최대 5개
 │
 ▼
Concept당 Question 2개
 │
 ├──────────────────────────────┐
 ▼                              ▼
소크라테스 학습 기능          파인만 학습 기능
질문별 답변·즉시 평가         개념별 자유 답변·일괄 평가
```

파인만 학습 기능은 개념과 질문을 새로 생성하지 않는다. 소크라테스 학습 기능이 생성한 Concept과 Question을 재사용한다. 웹은 PostgreSQL을, CLI는 `outputs/` 파일을 공용 학습 자료 저장소로 사용한다.

## 1. ParsedDocument

`ParsedDocument`는 PDF를 파싱한 결과 전체를 나타낸다.

```json
{
  "document_id": "doc_dbb41790",
  "source_path": "./Redis.pdf",
  "title": "Redis",
  "markdown": "PDF 전체 본문",
  "pages": [
    {
      "page_number": 1,
      "markdown": "1페이지 본문"
    }
  ],
  "created_at": "..."
}
```

- `document_id`: 같은 PDF의 소크라테스/파인만 학습 결과를 연결한다.
- `markdown`: Concept 생성에 사용한다.
- `pages`: Question 생성 시 관련 페이지 본문을 찾는 데 사용한다.

```text
ParsedDocument.markdown
→ Concept 생성

Concept.source_pages
+ ParsedDocument.pages
→ 관련 PDF 본문 추출
→ Question 생성
```

답변 평가 단계에서는 PDF 본문을 다시 사용하지 않는다.

## 2. Concept

LLM은 PDF에서 중요한 개념을 최대 5개까지 선정한다.

```json
{
  "concept_id": "concept_001",
  "title": "Redis 영속성",
  "summary": "Redis는 RDB와 AOF 방식으로 데이터를 보존한다.",
  "importance": "장애 복구 전략을 이해하는 핵심이다.",
  "source_pages": [12, 13],
  "evidence_from_material": [
    "RDB는 일정 시점의 데이터 스냅샷을 생성한다."
  ]
}
```

`concept_id`는 Question과 ConceptAnswer를 Concept에 연결하는 키다.

```text
Concept.concept_id
 ├─ Question.concept_id
 └─ ConceptAnswer.concept_id
```

## 3. Question과 RequiredPoint

각 Concept마다 정확히 두 개의 Question을 생성한다.

1. `explanation` 질문 한 개
2. `comparison` 또는 `application` 질문 한 개

```json
{
  "question_id": "q_001_001",
  "concept_id": "concept_001",
  "question_type": "explanation",
  "question": "Redis의 두 영속성 방식을 설명해보게.",
  "required_points": [
    {
      "point_id": "rp_001",
      "text": "RDB는 특정 시점의 스냅샷을 저장한다.",
      "gentle_hint": "특정 시점의 상태를 저장하는 방식을 생각해보게.",
      "direct_hint": "RDB가 메모리 상태의 스냅샷을 저장한다는 점을 생각해보게."
    },
    {
      "point_id": "rp_002",
      "text": "AOF는 실행된 쓰기 명령을 기록한다.",
      "gentle_hint": "Redis가 실행한 명령을 남기는 방식을 생각해보게.",
      "direct_hint": "AOF가 쓰기 명령을 순서대로 기록한다는 점을 생각해보게."
    }
  ],
  "source_pages": [12, 13]
}
```

`required_points[].text`가 실제 채점 기준이다. `required_points` 개수는 고정되어 있지 않다.

`point_id`는 질문 내부의 필수 요소를 안정적으로 식별하며 `rp_001`, `rp_002` 순서로 부여된다. 각 RequiredPoint는 채점 문장과 첫 번째·두 번째 재시도용 힌트를 함께 소유한다.

## 4. 소크라테스 학습 기능

### 학습 자료 생성

```text
PDF
 ↓
ParsedDocument
 ↓
Concept 최대 5개
 ↓
Concept당 Question 2개
```

웹 소크라테스 학습 기능은 다음 PostgreSQL 레코드를 저장한다.

```text
learning_documents[file_hash]
└─ ParsedDocument JSONB

learning_materials[file_hash, difficulty, output_language]
├─ Concept[] JSONB
└─ Question[] JSONB
```

CLI는 다음 공용 학습 자료를 파일로 저장한다.

```text
outputs/<문서 폴더>/
├─ parsed_<document_id>.json
├─ parsed_<document_id>.md
├─ concepts_<document_id>.json
└─ questions_<document_id>.json
```

웹 파인만 학습은 `learning_materials`를, CLI 파인만 학습은 `concepts_<document_id>.json`과 `questions_<document_id>.json`을 재사용한다.

### 질문 진행과 StudentAnswer

소크라테스 학습 기능은 Question을 하나씩 사용자에게 보여주고 답변을 즉시 평가한다.

```text
Question
 ↓
사용자 답변
 ↓
LLM 평가
 ↓
StudentAnswer
```

```json
{
  "answer_id": "ans_ab12cd34",
  "question_id": "q_001_001",
  "attempt_number": 1,
  "answer_text": "RDB는 스냅샷을 만들고 AOF는 명령을 기록합니다.",
  "evaluation": {
    "matched_points": [
      "RDB는 특정 시점의 스냅샷을 저장한다.",
      "AOF는 실행된 쓰기 명령을 기록한다."
    ],
    "missing_points": [],
    "misconceptions": [],
    "score": 1.0,
    "status": "sufficient",
    "feedback_to_student": "두 방식의 핵심을 잘 붙잡았네.",
    "next_action": "next_question"
  },
  "created_at": "..."
}
```

StudentAnswer는 `question_id`를 통해 Question과 연결된다.

```text
StudentAnswer.question_id
→ Question.question_id
```

### 평가와 재시도

```text
Question.required_points[].text
+ 사용자 답변
→ matched_points
→ missing_points
→ misconceptions
→ score/status
```

- `matched_points`: 답변에 포함된 필수 요소
- `missing_points`: 답변에서 빠진 필수 요소
- `misconceptions`: 답변에 포함된 잘못된 이해
- `score`: 충족한 필수 요소 수를 전체 필수 요소 수로 나눈 값

오개념이 발견되면 평가 상태는 `misconception`이 된다.

재시도 흐름은 다음과 같다.

```text
1차 부족
→ 첫 번째 누락 RequiredPoint의 gentle_hint

2차 부족
→ 같은 RequiredPoint의 direct_hint

3차 부족
→ missing_points 공개
→ 다음 질문
```

동일한 질문에 여러 번 답하면 같은 `question_id`를 가진 StudentAnswer가 여러 개 생성된다.

## 5. 파인만 학습 기능

### 소크라테스 학습 자료 불러오기

웹 파인만 학습은 PDF 해시·난이도·언어로 `learning_materials`의 Concept과 Question을 불러온다. CLI는 PDF의 `document_id`로 출력 폴더를 찾고 다음 파일을 불러온다.

```text
concepts_<document_id>.json
questions_<document_id>.json
```

해당 저장소에 Concept이나 Question 중 하나라도 없으면 파인만 학습 기능을 시작할 수 없다. 파인만 학습 기능은 PDF 본문에서 Concept이나 Question을 다시 생성하지 않는다.

### ConceptAnswer 수집

파인만 학습 기능은 사용자에게 `Concept.title`만 보여준다. 답변 전에는 다음 정보를 보여주지 않는다.

- `Concept.summary`
- 실제 Question 문장
- `required_points`
- 힌트

사용자가 개념 하나를 자유롭게 설명하면 ConceptAnswer가 생성된다.

```json
{
  "answer_id": "concept_ans_ab12cd34",
  "concept_id": "concept_001",
  "answer_text": "Redis의 영속성에는 RDB와 AOF가 있으며...",
  "created_at": "..."
}
```

ConceptAnswer는 `concept_id`로 Concept과 연결된다. 파인만 학습 기능에서는 개념당 자유 답변 하나를 받는다.

### 일괄 평가

모든 개념 답변을 수집한 다음 LLM 평가를 시작한다.

```text
ConceptAnswer.concept_id
        ↓
같은 concept_id를 가진 Question 검색
        ↓
explanation Question
comparison/application Question
```

하나의 개념 답변을 두 Question의 RequiredPoint에 각각 대조한다.

```text
ConceptAnswer 1개
 ├─ explanation.required_points 기준 평가
 └─ comparison/application.required_points 기준 평가
```

각 평가 결과는 기존 StudentAnswer 구조로 저장된다. 따라서 개념 하나당 다음 데이터가 생성된다.

```text
ConceptAnswer 원본 답변 1개
StudentAnswer 질문별 평가 2개
```

개념이 5개라면 ConceptAnswer는 최대 5개, StudentAnswer 평가 결과는 최대 10개다.

## 6. StudySession

소크라테스 학습 기능과 파인만 학습 기능은 실행 중 전체 상태를 담는 공통 StudySession 모델을 사용한다.

```text
StudySession
├─ concepts
├─ questions
├─ concept_answers
├─ answers
├─ summary
├─ started_at
└─ ended_at
```

| 필드 | 소크라테스 학습 기능 | 파인만 학습 기능 |
| --- | --- | --- |
| `concepts` | PDF에서 생성한 개념 | 소크라테스 학습 파일에서 불러온 개념 |
| `questions` | PDF와 개념에서 생성한 질문 | 소크라테스 학습 파일에서 불러온 숨은 평가 기준 |
| `concept_answers` | 사용하지 않음 | 개념별 원본 자유 답변 |
| `answers` | 질문에 직접 답한 결과 | 개념 답변을 질문별로 평가한 결과 |
| `summary` | 질문 학습 요약 | 백지회상 평가 요약 |

## 7. AnswerEvaluation

두 학습 기능은 같은 평가 결과 모델을 사용한다.

```text
AnswerEvaluation
├─ matched_points
├─ missing_points
├─ misconceptions
├─ score
├─ status
├─ feedback_to_student
├─ socratic_follow_up
└─ next_action
```

소크라테스 학습 기능에서는 `next_action`이 재시도 또는 다음 질문 이동을 제어한다. 파인만 학습 기능에서는 모든 답변을 수집한 뒤 최종 평가하므로 실질적인 재시도를 진행하지 않는다.

## 8. SessionSummary

SessionSummary는 질문별 평가 결과를 개념 단위로 집계한다.

```json
{
  "strong_concepts": ["Redis 영속성"],
  "weak_concepts": ["캐시 무효화"],
  "frequently_missing_points": [
    "AOF 재작성의 목적"
  ],
  "recommended_review_questions": [
    "AOF 재작성이 필요한 이유를 설명해보세요."
  ],
  "overall_feedback": "기본 설명은 잘했지만 응용 관점의 복습이 필요합니다."
}
```

```text
StudentAnswer.question_id
→ Question.concept_id
→ Concept.title
→ 강한 개념/약한 개념 분류
```

## 9. 저장 관계

웹은 다음 PostgreSQL 테이블을 사용한다.

```text
learning_documents ← 파싱 문서 및 페이지
learning_materials ← 두 기능이 공유하는 Concept과 Question
web_study_sessions ← 답변, 평가, 진행 위치, 요약
```

CLI는 다음 파일을 사용한다.

```text
outputs/<문서 폴더>/
├─ concepts_<document_id>.json       ← 소크라테스 학습이 생성, 두 기능 공용
├─ questions_<document_id>.json      ← 소크라테스 학습이 생성, 두 기능 공용
├─ session_<timestamp>.json          ← 소크라테스 학습 결과
└─ concept_review_<timestamp>.json   ← 파인만 학습 결과
```

파인만 학습 리포트는 Concept와 Question 전체를 중복 저장하지 않고 원본 파일명을 참조한다.

```json
{
  "review_id": "concept_review_...",
  "document_id": "doc_dbb41790",
  "concepts_file": "concepts_doc_dbb41790.json",
  "questions_file": "questions_doc_dbb41790.json",
  "concept_answers": [],
  "evaluations": [],
  "summary": {}
}
```

## 10. 핵심 연결 키

| 연결 | 키 |
| --- | --- |
| PDF와 출력 파일 | `document_id` |
| Concept와 Question | `concept_id` |
| Concept와 파인만 학습의 자유 답변 | `concept_id` |
| Question과 평가 결과 | `question_id` |
| Question 내부 필수 요소 | `point_id` |

요약하면 소크라테스 학습 기능은 PDF에서 Concept와 Question을 생성한 뒤 질문별 학습을 진행한다. 파인만 학습 기능은 소크라테스 학습 기능이 만든 Concept 제목으로 자유 답변을 받은 뒤 같은 Concept에 연결된 두 Question의 RequiredPoint를 이용해 그 답변을 두 번 평가한다.

## 프론트엔드 API 문서

프론트엔드에서 사용하는 API와 소크라테스/파인만 학습 모드별 동작은 [frontend-api.md](./frontend-api.md)에 정리되어 있다.
