from __future__ import annotations

import json
import os
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError, Timeout


LLM_CONNECT_TIMEOUT_SECONDS = 10.0
LLM_RESPONSE_TIMEOUT_SECONDS = 70.0
LLM_NETWORK_RETRIES = 1
LLM_JSON_REPAIR_RETRIES = 1


class LLMJSONParseError(RuntimeError):
    pass


class LLMConnectionError(RuntimeError):
    pass


class LLMRequestTimeoutError(RuntimeError):
    pass


class LLMRateLimitError(RuntimeError):
    pass


class LLMServiceError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, model: str, api_key: str, temperature: float = 0.2):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required.")
        self.model = model
        self.temperature = temperature
        base_url = os.getenv("OPENAI_BASE_URL")
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=Timeout(LLM_RESPONSE_TIMEOUT_SECONDS, connect=LLM_CONNECT_TIMEOUT_SECONDS),
            max_retries=LLM_NETWORK_RETRIES,
        )

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_repair_retries: int = LLM_JSON_REPAIR_RETRIES,
    ) -> dict[str, Any]:
        last_content = ""
        current_user_prompt = user_prompt

        for attempt in range(json_repair_retries + 1):
            try:
                request_params = dict(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": f"{system_prompt}\nReturn valid JSON only."},
                        {"role": "user", "content": current_user_prompt},
                    ],
                )
                if not self.model.startswith("gpt-5"):
                    request_params["temperature"] = self.temperature
                response = self.client.chat.completions.create(**request_params)
            except APITimeoutError as exc:
                raise LLMRequestTimeoutError("LLM 응답 시간이 초과되었습니다.") from exc
            except RateLimitError as exc:
                raise LLMRateLimitError("LLM API 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.") from exc
            except APIConnectionError as exc:
                raise LLMConnectionError("LLM API에 연결할 수 없습니다.") from exc
            except APIStatusError as exc:
                raise LLMServiceError(f"LLM API 요청에 실패했습니다. 상태 코드: {exc.status_code}") from exc
            last_content = response.choices[0].message.content or ""
            try:
                parsed = json.loads(last_content)
            except json.JSONDecodeError:
                if attempt >= json_repair_retries:
                    break
                current_user_prompt = (
                    "The previous response was not valid JSON. Repair it and return valid JSON only.\n\n"
                    f"Previous response:\n{last_content}\n\n"
                    f"Original task:\n{user_prompt}"
                )
                continue
            if not isinstance(parsed, dict):
                raise LLMJSONParseError("LLM JSON response must be an object.")
            return parsed

        raise LLMJSONParseError(f"Could not parse LLM response as JSON: {last_content[:500]}")
