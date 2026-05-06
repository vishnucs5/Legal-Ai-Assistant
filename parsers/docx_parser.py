from __future__ import annotations

from pathlib import Path


class DOCXParser:
    def parse(self, path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("Install python-docx to parse Word files.") from exc

        document = Document(path)
        return "\n\n".join(p.text.strip() for p in document.paragraphs if p.text.strip())

