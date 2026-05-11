from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _default_cache_path() -> str:
    if os.getenv("LEGAL_AI_CACHE_PATH"):
        return os.getenv("LEGAL_AI_CACHE_PATH", "")
    if os.getenv("VERCEL"):
        return str(Path(tempfile.gettempdir()) / "legal_ai.sqlite3")
    return ".cache/legal_ai.sqlite3"


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    api_key: str = os.getenv("API_KEY", "")
    cache_path: str = _default_cache_path()
    default_model: str = os.getenv("LEGAL_AI_MODEL", "claude-3-5-sonnet-latest")


settings = Settings()
