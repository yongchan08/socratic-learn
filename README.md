# Socratic Lecture Tutor

강의 PDF를 Markdown으로 파싱하고, OpenAI-compatible API를 사용해 핵심 개념과 소크라테스식 질문을 생성하는 학습 도구입니다. 기존 질문별 학습 세션과 별도로, 개념별 자유 답변을 모두 수집한 뒤 필수 요소 충족 여부를 일괄 평가하는 리포트 기능도 제공합니다.

## Quick Start

처음 사용하는 경우 아래 순서만 따라가면 됩니다.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

`.env`에 API 키를 넣습니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/socratic_tutor
```

웹 학습 세션을 새로고침이나 서버 재시작 후에도 이어가려면 PostgreSQL 데이터베이스를 만들고
`DATABASE_URL`을 설정합니다. 웹 서버 시작 시 `web_study_sessions` 테이블이 자동 생성됩니다.
`DATABASE_URL`을 생략하면 웹 세션은 기존처럼 서버 메모리에만 보관됩니다.

웹 UI로 실행하려면 프론트엔드를 빌드한 뒤 FastAPI 서버를 실행합니다.

```bash
cd frontend
npm install
npm run build
cd ..
.venv/bin/socratic-tutor-web
```

브라우저에서 `http://127.0.0.1:8000`을 열면 PDF 업로드, 개념 확인, 문답 세션, 학습 기록서를 한 화면에서 사용할 수 있습니다.

배포된 프론트엔드는 첫 화면 진입 시 백엔드의 `/api/health`를 비동기로 호출합니다. 이 호출은 무료 Render 인스턴스의 콜드스타트를 없애지는 않지만, 사용자가 PDF를 선택하는 동안 서버 시작을 미리 유도해 분석 버튼 이후의 대기 시간을 줄입니다. health 요청 실패는 화면 사용을 막지 않습니다.

PDF를 넣고 학습 세션을 시작합니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf
```

실행하면 앱이 PDF를 분석한 뒤 핵심 개념을 보여줍니다. 개념 목록이 괜찮으면 `Y`를 입력해 학습을 시작하세요.

```text
PDF 분석 완료.

추출된 핵심 개념:
1. Training Error and Test Error
2. Overfitting
3. Underfitting

이 개념들로 학습을 시작할까요? [Y/n]
```

기본 `start` 세션에서는 표시된 질문에 답합니다. 중간에 끝내고 싶으면 `/quit`을 입력하세요.

```text
답변 (/quit 종료, /skip 건너뛰기, /help 도움말):
```

답변이 부족하면 최대 3번까지 소크라테스식 후속 질문과 힌트를 제공합니다.

## Common Usage

가장 자주 쓰는 명령은 `start`입니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf
```

질문 난이도를 조절하고 싶으면 `--difficulty`를 사용합니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf --difficulty easy
.venv/bin/socratic-tutor start --pdf ./lecture.pdf --difficulty normal
.venv/bin/socratic-tutor start --pdf ./lecture.pdf --difficulty hard
```

영어 질문과 피드백이 필요하면 `--output-language en`을 사용합니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf --output-language en
```

PDF 파싱 결과만 확인하고 싶으면 `parse`를 실행합니다.

```bash
.venv/bin/socratic-tutor parse --pdf ./lecture.pdf
```

이전 세션 요약을 다시 보고 싶으면 저장된 세션 JSON을 지정합니다.

```bash
.venv/bin/socratic-tutor inspect --session ./outputs/lecture_doc_12345678/session_20260626_143012.json
```

## Commands

| 명령 | 용도 |
| --- | --- |
| `socratic-tutor start --pdf <path>` | PDF 분석, 개념 추출, 질문 생성, 대화형 학습, 요약 저장까지 실행합니다. |
| `socratic-tutor parse --pdf <path>` | PDF를 Markdown/JSON으로 변환해 `outputs/`에 저장합니다. |
| `socratic-tutor inspect --session <path>` | 저장된 세션 JSON을 읽어 요약을 출력합니다. |
| `socratic-tutor-web` | React 웹 UI와 API 서버를 실행합니다. |

패키지 스크립트 대신 모듈로도 실행할 수 있습니다.

```bash
.venv/bin/python -m socratic_tutor start --pdf ./lecture.pdf
```

## Start Options

처음에는 `--pdf`만 지정하면 됩니다. 나머지는 필요할 때만 추가하세요. 핵심 개념은 LLM이 강의 내용의 중요도에 따라 최대 5개까지 자동으로 선정하며, 개념마다 질문 2개를 생성합니다.

| 옵션 | 기본값 | 언제 쓰나 |
| --- | --- | --- |
| `--pdf <path>` | 필수 | 학습할 PDF 경로입니다. |
| `--difficulty easy\|normal\|hard` | `normal` | 질문과 평가 기준의 난이도를 조절합니다. |
| `--output-language ko\|en` | `ko` | 질문, 피드백, 요약 출력 언어를 바꿉니다. |
| `--model <name>` | `OPENAI_MODEL` 또는 `gpt-5-mini` | 실행할 모델을 명령마다 바꾸고 싶을 때 사용합니다. |
| `--output-dir <path>` | `./outputs` | 결과 저장 위치를 바꿉니다. |
| `--cache-dir <path>` | `./cache` | 캐시 저장 위치를 바꿉니다. |
| `--skip-cache` | `False` | 기존 캐시를 무시하고 다시 생성합니다. |

옵션을 모두 명시한 예시는 아래와 같습니다.

```bash
.venv/bin/socratic-tutor start \
  --pdf ./lecture.pdf \
  --difficulty normal \
  --output-language ko
```

## Session Controls

학습 세션 중 답변 입력란에서 아래 명령을 사용할 수 있습니다.

| 명령 | 동작 |
| --- | --- |
| `/skip` | 현재 질문을 건너뜁니다. |
| `/quit` | 현재까지 답변으로 세션을 종료하고 요약을 저장합니다. |
| `/exit` | `/quit`과 같습니다. |
| `/done` | `/quit`과 같습니다. |
| `/help` | 사용 가능한 명령을 출력합니다. |

답변의 충족 여부와 점수는 `required_points`만으로 계산합니다. `required_points` 개수는 고정되어 있지 않으며 질문 생성 LLM이 질문 내용에 필요한 만큼 생성합니다.

## Concept Review

기존 `start` 학습 흐름을 바꾸지 않고 개념별 일괄 평가를 실행하려면 별도 명령을 사용합니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf
.venv/bin/socratic-tutor concept-review --pdf ./lecture.pdf
```

먼저 `start`가 생성한 `concepts_{document_id}.json`과 `questions_{document_id}.json`이 있어야 합니다. `concept-review`는 개념과 질문을 새로 만들지 않고 이 두 파일을 직접 읽습니다. 백지회상을 위해 개념 제목만 순서대로 제시하고, `summary`, 생성된 질문, `required_points`, 힌트는 답변 전에 보여주지 않습니다. 답변 수집 중에는 LLM을 호출하지 않으며, 순회가 끝난 뒤 각 답변을 해당 개념의 `explanation` 질문과 `comparison`/`application` 질문의 `required_points`에 각각 대조합니다.

`concept_review_{timestamp}.json`에는 개념·질문 전체를 중복 저장하지 않습니다. 대신 원본 개념·질문 파일명, 사용자의 개념별 답변, 질문별 평가 결과와 요약을 저장합니다.

## MVP Concept Schema

MVP에서 학습 루프가 사용하는 Concept 필드는 `concept_id`, `title`, `summary`, `importance`, `source_pages`, `evidence_from_material`입니다.

## Question Schema

질문은 채점 기준과 두 단계 힌트를 하나로 묶은 `required_points` 객체 배열을 사용합니다.

```json
{
  "question_id": "q_001_001",
  "concept_id": "concept_001",
  "question_type": "explanation",
  "question": "훈련 성능과 테스트 성능의 차이를 어떻게 설명하겠는가?",
  "required_points": [
    {
      "point_id": "rp_001",
      "text": "새로운 데이터에서 일반화 성능이 떨어진다",
      "gentle_hint": "처음 보는 데이터에서는 어떤 결과가 나타날지 생각해보게.",
      "direct_hint": "훈련 성능과 테스트 성능을 비교해보게."
    },
    {
      "point_id": "rp_002",
      "text": "모델 복잡도가 지나치게 높을 수 있다",
      "gentle_hint": "모델이 너무 많은 규칙을 기억하면 어떻게 될까?",
      "direct_hint": "모델 복잡도와 과적합의 관계를 생각해보게."
    }
  ],
  "source_pages": [4, 5]
}
```

각 항목은 채점 문장인 `text`와 첫 번째·두 번째 재시도에 사용할 `gentle_hint`, `direct_hint`를 함께 가집니다. `point_id`는 질문 안에서 `rp_001`, `rp_002` 순서로 부여됩니다. 별도의 힌트 배열이 없으므로 문자열 중복이나 배열 간 순서 불일치가 발생하지 않습니다.

## Output Files

CLI는 `outputs/`에는 사람이 확인할 결과를, `cache/`에는 재실행을 빠르게 하기 위한 중간 산출물을 저장합니다. `DATABASE_URL`이 설정된 웹 서버는 이 폴더 대신 PostgreSQL을 사용합니다.

```text
outputs/
  {pdf_title}_{document_id}/
    {pdf_title}_parsed.md
    parsed_{document_id}.md
    parsed_{document_id}.json
    concepts_{document_id}.json
    questions_{document_id}.json
    session_{timestamp}.json

cache/
  {pdf_title}_{pdf_sha256_prefix}/
    parsed.json
    concepts_auto_5_{language}.json
    questions_{language}_v6_unified_points_q2.json

uploads/
  {random_id}/
    {original_filename}.pdf  # 웹 분석 중에만 존재하며 완료/실패 후 삭제
```

세션 JSON에는 난이도, 출력 언어, 최대 5개의 개념, 개념당 2개의 평가 질문, 개념별 자유 답변(`concept_answers`), 질문별 필수 요소 평가(`answers`)와 요약이 저장됩니다. 각 개념의 첫 질문은 개념 자체를 확인하는 `explanation`, 두 번째 질문은 `comparison` 또는 `application`입니다. 제거된 `subject`, `max_concepts`, `questions_per_concept` 입력 필드는 저장하지 않습니다.

웹 저장 테이블은 다음과 같습니다.

- `learning_documents`: PDF 해시와 파싱된 문서·페이지 JSONB
- `learning_materials`: PDF 해시·난이도·언어별 Concept 및 Question JSONB
- `web_study_sessions`: 현재 인덱스, 답변, 평가, 요약을 포함한 웹 세션 JSONB
- `learning_courses`: 3단계 로드맵, 단계별 세션 연결과 완료 상태 JSONB

웹에서 업로드한 원본 PDF는 PostgreSQL에 저장하지 않으며 처리 후 삭제합니다. 같은 PDF가 다시 업로드되면 파일 해시로 `learning_documents`를 조회하고, 같은 난이도·언어의 Concept과 Question이 있으면 `learning_materials`에서 재사용합니다. 따라서 DB를 사용하는 웹 실행에서는 별도의 로컬 `cache/`가 필요하지 않습니다. `outputs/`와 `cache/`는 CLI 및 `DATABASE_URL` 미설정 호환 모드에서만 사용합니다.

웹 학습은 3단계 로드맵으로 구성됩니다. 각 단계에 서로 다른 PDF를 등록하고 소크라테스 질문 학습을 완료하면 다음 단계가 열린다. 세 단계를 모두 완료하면 각 단계 세션의 Concept과 Question ID에 `stage_1_`, `stage_2_`, `stage_3_` 접두사를 붙여 하나의 최종 개념 리포트 세션으로 합칩니다. 이 네임스페이스는 서로 다른 PDF가 동일한 `concept_001`, `q_001_001` ID를 생성해도 평가 연결이 충돌하지 않게 합니다.

`v6_unified_points_q2` 질문 캐시는 개념당 설명 질문 1개와 비교·응용 질문 1개를 포함합니다. 각 필수 요소는 채점 문장과 두 단계 힌트를 하나의 객체로 저장합니다. 이전 질문 캐시는 자동 재사용하지 않으며, 같은 PDF를 다시 학습할 때 새 정책으로 질문을 생성합니다.

## PDF Upload Limits

웹 업로드와 CLI 파서는 서버 자원과 LLM 비용을 보호하기 위해 다음 제한을 적용합니다.

- 웹 업로드 파일은 최대 25MB입니다. 서버는 파일을 1MB 단위로 저장하며 제한을 넘으면 즉시 중단하고 부분 파일을 삭제합니다.
- PDF는 최대 200페이지입니다. 페이지 수는 텍스트 추출 전에 검사합니다.
- 파일 확장자뿐 아니라 파일 시작 부분의 `%PDF-` 시그니처를 검사합니다.
- 손상되었거나 암호화된 PDF는 처리하지 않습니다.
- 추출할 수 있는 텍스트가 없는 스캔 이미지 PDF는 처리하지 않습니다.

프론트엔드는 파일 선택 시 25MB 제한을 먼저 검사하지만, 최종 검증은 백엔드에서 다시 수행합니다.
웹 서버에 임시 저장된 원본 PDF는 세션 생성의 성공 또는 실패 여부와 관계없이 처리가 끝나는 즉시 삭제합니다.

세션 생성 SSE 연결은 처리 단계 사이에 새 진행 이벤트가 없더라도 15초마다 heartbeat comment를 전송합니다. heartbeat는 장시간 PDF 파싱이나 LLM 응답 대기 중 프록시가 연결을 유휴 상태로 종료하는 위험을 줄이며, 작업 자체의 실행 제한 시간 역할은 하지 않습니다.

LLM API 연결에는 10초 연결 타임아웃과 70초 응답 타임아웃을 적용합니다. 개념별 질문을 병렬 생성하는 전체 단계는 최대 120초까지 실행하며, 제한을 넘으면 아직 시작하지 않은 작업을 취소하고 세션 생성을 실패 처리합니다.

일시적인 네트워크 오류, 요청 제한, 서버 오류는 OpenAI SDK가 최대 1회 재시도합니다. API 응답이 유효한 JSON이 아니면 별도의 JSON 복구 요청을 1회만 수행합니다. 최종 실패는 연결, 응답 시간 초과, 요청 제한, API 상태 오류로 구분하며, 질문 생성 중 실패하면 해당 개념 제목과 ID를 오류에 포함하고 불완전한 질문 캐시는 저장하지 않습니다.

## Language Behavior

기본 학습 인터페이스 언어는 한국어입니다.

강의자료가 영어 PDF여도 앱은:

- 한국어로 질문을 생성하고
- 한국어 답변을 받을 수 있으며
- 영어 원문 개념과 한국어 답변을 의미 기준으로 비교하고
- 한국어 피드백, 힌트, 요약을 제공합니다.

영어 출력이 필요하면 `--output-language en` 옵션을 사용하세요.

## Environment

모델명 우선순위는 `--model`, `OPENAI_MODEL`, 기본값 `gpt-5-mini` 순서입니다.

OpenAI-compatible gateway를 쓰는 경우 `.env`에 `OPENAI_BASE_URL`도 설정할 수 있습니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
OPENAI_BASE_URL=https://your-gateway.example.com/v1
```

## Troubleshooting

`OPENAI_API_KEY가 설정되어 있지 않습니다.`

`.env` 파일을 만들고 `OPENAI_API_KEY`를 추가하세요.

`PDF 파싱에 실패했습니다.`

PDF가 손상되었거나 텍스트 추출이 어려운 스캔 문서일 수 있습니다.

`LLM 응답을 JSON으로 파싱하지 못했습니다.`

다시 실행하거나 `--model`로 다른 모델을 지정하세요.

## Limitations

- 로그인, 결제, 데이터베이스는 없습니다.
- OCR 고도화나 이미지 기반 슬라이드 이해는 지원하지 않습니다.
- 스캔 PDF, 이미지 중심 슬라이드, 복잡한 수식/도표는 품질이 낮을 수 있습니다.
- PDF 업로드는 25MB 및 200페이지로 제한됩니다.
- 긴 PDF는 `MAX_MARKDOWN_CHARS = 80_000` 기준으로 시작, 중간, 끝 부분만 사용합니다.
- 모든 LLM 호출은 PDF에서 추출된 텍스트를 외부 API로 전송합니다.

## Security and Privacy

- PDF 파일 자체는 로컬 파일로 처리됩니다.
- PDF에서 추출된 텍스트는 LLM API로 전송됩니다.
- 민감한 강의자료나 개인정보가 포함된 문서는 주의해서 사용하세요.
- 세션 결과와 캐시는 로컬 `outputs/`, `cache/` 디렉터리에 저장됩니다.

## Development

테스트 실행:

```bash
.venv/bin/pytest
```
