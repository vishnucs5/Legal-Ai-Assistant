from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    api_key: str = os.getenv("API_KEY", "")
    cache_path: str = os.getenv("LEGAL_AI_CACHE_PATH", ".cache/legal_ai.sqlite3")
    default_model: str = os.getenv("LEGAL_AI_MODEL", "claude-3-5-sonnet-latest")


settings = Settings()

