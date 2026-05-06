from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    system: str
    user: str

    def render(self, **kwargs: object) -> str:
        return f"{self.system.strip()}\n\n{self.user.format(**kwargs).strip()}"

