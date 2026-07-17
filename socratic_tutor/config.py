from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field


DEFAULT_MODEL = "gpt-5-mini"
MAX_CONCEPTS = 5
QUESTIONS_PER_CONCEPT = 2


class AppConfig(BaseModel):
    pdf_path: Path | None = None
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    output_language: Literal["ko", "en"] = "ko"
    model: str = DEFAULT_MODEL
    output_dir: Path = Path("./outputs")
    cache_dir: Path = Path("./cache")
    skip_cache: bool = False
    api_key: str | None = None


def load_app_config(
    pdf: str | None = None,
    difficulty: str = "normal",
    output_language: str = "ko",
    model: str | None = None,
    output_dir: str = "./outputs",
    cache_dir: str = "./cache",
    skip_cache: bool = False,
) -> AppConfig:
    load_dotenv()
    resolved_model = model or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    return AppConfig(
        pdf_path=Path(pdf) if pdf else None,
        difficulty=difficulty,
        output_language=output_language,
        model=resolved_model,
        output_dir=Path(output_dir),
        cache_dir=Path(cache_dir),
        skip_cache=skip_cache,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
