from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TextChunk:
    text: str
    index: int
    start_token: int
    end_token: int


class TextChunker:
    def __init__(self, max_tokens: int = 1800, overlap_tokens: int = 120):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return max(1, len(text.split()))

    def chunk(self, text: str) -> List[TextChunk]:
        words = text.split()
        if not words:
            return []
        if len(words) <= self.max_tokens:
            return [TextChunk(text.strip(), 0, 0, len(words))]

        chunks: List[TextChunk] = []
        step = max(1, self.max_tokens - self.overlap_tokens)
        start = 0
        while start < len(words):
            end = min(len(words), start + self.max_tokens)
            chunk_text = " ".join(words[start:end])
            chunks.append(TextChunk(chunk_text, len(chunks), start, end))
            if end >= len(words):
                break
            start += step
        return chunks
