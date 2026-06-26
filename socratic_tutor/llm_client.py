from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


class LLMJSONParseError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, model: str, api_key: str, temperature: float = 0.2):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required.")
        self.model = model
        self.temperature = temperature
        base_url = os.getenv("OPENAI_BASE_URL")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        last_content = ""
        current_user_prompt = user_prompt

        for attempt in range(max_retries + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": f"{system_prompt}\nReturn valid JSON only."},
                    {"role": "user", "content": current_user_prompt},
                ],
            )
            last_content = response.choices[0].message.content or ""
            try:
                parsed = json.loads(last_content)
            except json.JSONDecodeError:
                if attempt >= max_retries:
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
