from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional


class SQLiteLLMCache:
    CACHE_VERSION = "2026-05-04.2"

    def __init__(self, path: Path | str = ".cache/legal_ai.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()
        self.hits = 0

    def _init(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS llm_cache (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def make_key(self, text: str, context: object) -> str:
        payload = json.dumps(
            {
                "cache_version": self.CACHE_VERSION,
                "text": text,
                "contract_type": getattr(context, "contract_type", ""),
                "jurisdiction": getattr(context, "jurisdiction", ""),
                "depth": getattr(context, "depth", ""),
            },
            sort_keys=True,
        )
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[str]:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT payload FROM llm_cache WHERE cache_key = ?", (cache_key,)).fetchone()
        if row:
            self.hits += 1
            return row[0]
        return None

    def set(self, cache_key: str, payload: object) -> None:
        value = payload if isinstance(payload, str) else json.dumps(payload, default=str)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache (cache_key, payload) VALUES (?, ?)",
                (cache_key, value),
            )
