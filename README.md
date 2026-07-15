# Socratic Lecture Tutor

강의 PDF를 Markdown으로 파싱하고, OpenAI-compatible API를 사용해 핵심 개념과 소크라테스식 질문을 생성하는 학습 도구입니다. CLI와 웹 UI를 모두 제공합니다. 사용자는 자유롭게 답변하고, 앱은 필수 포함 요소 기준으로 답변을 평가한 뒤 부족한 경우 힌트를 제공합니다. 세션 종료 후 요약을 출력하고 로컬 JSON 파일로 저장합니다.

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
OPENAI_MODEL=gpt-4.1
```

웹 UI로 실행하려면 프론트엔드를 빌드한 뒤 FastAPI 서버를 실행합니다.

```bash
cd frontend
npm install
npm run build
cd ..
.venv/bin/socratic-tutor-web
```

브라우저에서 `http://127.0.0.1:8000`을 열면 PDF 업로드, 개념 확인, 문답 세션, 학습 기록서를 한 화면에서 사용할 수 있습니다.

PDF를 넣고 학습 세션을 시작합니다.

```bash
.venv/bin/socratic-tutor start --pdf ./examples/sample.pdf
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

세션 중에는 답변을 입력하면 됩니다. 중간에 끝내고 싶으면 `/quit`을 입력하세요.

```text
답변 (/quit 종료, /skip 건너뛰기, /help 도움말):
```

한 질문당 최대 3번까지 답변할 수 있습니다. 1차 답변이 부족하면 소크라테스식 후속 질문으로 다시 생각하게 하고, 2차 답변이 부족하면 조금 더 직접적인 힌트를 제공합니다. 3차 답변도 부족하면 빠진 핵심을 알려준 뒤 다음 질문으로 넘어갑니다.

## Common Usage

가장 자주 쓰는 명령은 `start`입니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf
```

강의 주제가 파일명이나 내용만으로 애매하면 `--subject`를 추가합니다.

```bash
.venv/bin/socratic-tutor start --pdf ./lecture.pdf --subject "UI 설계"
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

처음에는 `--pdf`만 지정하면 됩니다. 나머지는 필요할 때만 추가하세요.

| 옵션 | 기본값 | 언제 쓰나 |
| --- | --- | --- |
| `--pdf <path>` | 필수 | 학습할 PDF 경로입니다. |
| `--subject <text>` | 없음 | PDF 주제가 애매하거나 특정 수업/시험 맥락으로 분석하고 싶을 때 사용합니다. |
| `--difficulty easy\|normal\|hard` | `normal` | 질문과 평가 기준의 난이도를 조절합니다. |
| `--output-language ko\|en` | `ko` | 질문, 피드백, 요약 출력 언어를 바꿉니다. |
| `--max-concepts <n>` | `7` | 추출할 핵심 개념 수를 조절합니다. 최대 10개입니다. |
| `--questions-per-concept <n>` | `3` | 개념마다 생성할 질문 수를 조절합니다. 최대 3개입니다. |
| `--model <name>` | `OPENAI_MODEL` 또는 `gpt-4.1` | 실행할 모델을 명령마다 바꾸고 싶을 때 사용합니다. |
| `--output-dir <path>` | `./outputs` | 결과 저장 위치를 바꿉니다. |
| `--cache-dir <path>` | `./cache` | 캐시 저장 위치를 바꿉니다. |
| `--skip-cache` | `False` | 기존 캐시를 무시하고 다시 생성합니다. |

옵션을 모두 명시한 예시는 아래와 같습니다.

```bash
.venv/bin/socratic-tutor start \
  --pdf ./lecture.pdf \
  --subject "Machine Learning" \
  --difficulty normal \
  --output-language ko \
  --max-concepts 7 \
  --questions-per-concept 3
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

질문별 답변 흐름:

| 시도 | 답변이 부족한 경우 |
| --- | --- |
| 1차 | 첫 번째 누락 필수 요소에 연결된 간접적인 `gentle` 힌트를 보여줍니다. |
| 2차 | 같은 누락 필수 요소에 연결된 더 구체적인 `direct` 힌트를 보여줍니다. |
| 3차 | 빠진 핵심을 공개하고 다음 질문으로 넘어갑니다. |

답변의 충족 여부와 점수는 `required_points`만으로 계산합니다. 1~2차에 답변이 부족하면 서버가 `missing_points`의 첫 번째 요소를 선택하고, 그 요소에 연결된 힌트를 사용합니다. 따라서 LLM이 임의로 다른 힌트를 선택하지 않습니다. 연결 힌트가 없는 기존 질문 데이터에만 LLM 후속 질문 또는 일반 폴백 질문을 사용합니다.

## MVP Concept Schema

MVP에서 학습 루프가 사용하는 Concept 필드는 `concept_id`, `title`, `summary`, `importance`, `source_pages`, `evidence_from_material`입니다.

`prerequisites`와 `common_misconceptions`는 향후 고도화 기능을 위한 optional metadata입니다. 기존 JSON 호환성을 위해 모델에는 남아 있지만, 현재 MVP에서는 질문 생성, 답변 평가, 진행 판단에 사용하지 않습니다.

## Question Schema

질문은 채점 기준인 `required_points`와 각 기준에 명시적으로 연결된 `point_hints`를 사용합니다.

```json
{
  "question_id": "q_001_001",
  "concept_id": "concept_001",
  "question_type": "explanation",
  "question": "훈련 성능과 테스트 성능의 차이를 어떻게 설명하겠는가?",
  "required_points": [
    "새로운 데이터에서 일반화 성능이 떨어진다",
    "모델 복잡도가 지나치게 높을 수 있다"
  ],
  "point_hints": [
    {
      "point_id": "rp_001",
      "required_point": "새로운 데이터에서 일반화 성능이 떨어진다",
      "gentle": "처음 보는 데이터에서는 어떤 결과가 나타날지 생각해보게.",
      "direct": "훈련 성능과 테스트 성능을 비교해보게."
    },
    {
      "point_id": "rp_002",
      "required_point": "모델 복잡도가 지나치게 높을 수 있다",
      "gentle": "모델이 너무 많은 규칙을 기억하면 어떻게 될까?",
      "direct": "모델 복잡도와 과적합의 관계를 생각해보게."
    }
  ],
  "source_pages": [4, 5]
}
```

`point_hints`는 `required_points`와 같은 순서로 정확히 한 개씩 존재해야 합니다. `point_id`는 질문 안에서 `rp_001`, `rp_002` 순서로 부여됩니다. `required_point` 문자열이 연결 대상과 다르거나 항목이 누락되면 새 질문 생성 결과를 저장하지 않습니다.

기존 질문 JSON의 `hints` 배열도 계속 읽을 수 있습니다. `hints`와 `required_points`의 길이가 같으면 같은 순서의 연결 힌트로 변환하며, 이때 기존 힌트 하나를 `gentle`과 `direct`에 모두 사용합니다.

## Output Files

앱은 `outputs/`에는 사람이 확인할 결과를, `cache/`에는 재실행을 빠르게 하기 위한 중간 산출물을 저장합니다.

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
    concepts_ko.json
    questions_ko_v3.json
```

세션 JSON에는 사용자의 답변, 시도 횟수, 평가 결과, 요약이 함께 저장됩니다.

`v3` 질문 캐시는 필수 요소별 단계 힌트를 포함합니다. 이전 `v2` 질문 캐시는 자동 재사용하지 않으며, 같은 PDF를 다시 학습할 때 새 스키마로 질문을 생성합니다.

## PDF Upload Limits

웹 업로드와 CLI 파서는 서버 자원과 LLM 비용을 보호하기 위해 다음 제한을 적용합니다.

- 웹 업로드 파일은 최대 25MB입니다. 서버는 파일을 1MB 단위로 저장하며 제한을 넘으면 즉시 중단하고 부분 파일을 삭제합니다.
- PDF는 최대 200페이지입니다. 페이지 수는 텍스트 추출 전에 검사합니다.
- 파일 확장자뿐 아니라 파일 시작 부분의 `%PDF-` 시그니처를 검사합니다.
- 손상되었거나 암호화된 PDF는 처리하지 않습니다.
- 추출할 수 있는 텍스트가 없는 스캔 이미지 PDF는 처리하지 않습니다.

프론트엔드는 파일 선택 시 25MB 제한을 먼저 검사하지만, 최종 검증은 백엔드에서 다시 수행합니다.

## Language Behavior

기본 학습 인터페이스 언어는 한국어입니다.

강의자료가 영어 PDF여도 앱은:

- 한국어로 질문을 생성하고
- 한국어 답변을 받을 수 있으며
- 영어 원문 개념과 한국어 답변을 의미 기준으로 비교하고
- 한국어 피드백, 힌트, 요약을 제공합니다.

영어 출력이 필요하면 `--output-language en` 옵션을 사용하세요.

## Environment

모델명 우선순위는 `--model`, `OPENAI_MODEL`, 기본값 `gpt-4.1` 순서입니다.

OpenAI-compatible gateway를 쓰는 경우 `.env`에 `OPENAI_BASE_URL`도 설정할 수 있습니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
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
