from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def ensure_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def compute_file_hash(path: str | Path) -> str:
    hasher = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_json(data: Any, path: str | Path) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    if isinstance(data, BaseModel):
        payload = data.model_dump(mode="json")
    elif isinstance(data, list):
        payload = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in data
        ]
    else:
        payload = data
    with target.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return target


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def save_text(text: str, path: str | Path) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(text, encoding="utf-8")
    return target


def cache_folder_name(file_hash: str, source_path: str | Path | None = None, title: str | None = None) -> str:
    raw_title = title or (Path(source_path).stem if source_path else "document")
    safe_title = "".join(
        char if char.isalnum() or char in {"-", "_"} else "-"
        for char in raw_title.strip()
    ).strip("-")
    safe_title = safe_title or "document"
    return f"{safe_title}_{file_hash[:12]}"


def cache_path(
    cache_dir: str | Path,
    file_hash: str,
    name: str,
    source_path: str | Path | None = None,
    title: str | None = None,
) -> Path:
    return Path(cache_dir) / cache_folder_name(file_hash, source_path=source_path, title=title) / name


def legacy_cache_path(cache_dir: str | Path, file_hash: str, name: str) -> Path:
    return Path(cache_dir) / file_hash / name
