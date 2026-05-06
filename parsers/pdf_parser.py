from __future__ import annotations

import re
from pathlib import Path


class PDFParser:
    def parse(self, path: Path) -> str:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("Install pdfplumber to parse PDF files.") from exc

        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return self.cleanup("\n\n".join(pages))

    @staticmethod
    def cleanup(text: str) -> str:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

