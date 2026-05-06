from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from core.extractor import ClauseExtractor
from core.risk_analyzer import RiskAnalyzer
from core.summarizer import Summarizer
from models.contract import ContractMetadata, ContractType
from models.report import AnalysisReport, ProcessingMeta
from parsers.docx_parser import DOCXParser
from parsers.html_parser import html_to_text
from parsers.pdf_parser import PDFParser
from parsers.text_chunker import TextChunk, TextChunker
from prompts.extraction import ExtractionPromptBuilder
from utils.token_counter import count_tokens


@dataclass
class AnalysisConfig:
    contract_type: str = "unknown"
    jurisdiction: str = ""
    depth: str = "standard"
    output: str = "json"
    cache_path: str = ".cache/legal_ai.sqlite3"


@dataclass
class PipelineContext:
    input_file: Path
    config: AnalysisConfig
    started_at: float = field(default_factory=time.perf_counter)
    raw_text: str = ""
    chunks: list[TextChunk] = field(default_factory=list)
    clauses: list[Any] = field(default_factory=list)
    missing_clauses: list[str] = field(default_factory=list)
    risk_summary: Any = None
    executive_summary: Any = None
    result: Optional[AnalysisReport] = None
    should_abort: bool = False

    @property
    def contract_type(self) -> str:
        return self.config.contract_type

    @property
    def jurisdiction(self) -> str:
        return self.config.jurisdiction

    @property
    def depth(self) -> str:
        return self.config.depth

    @property
    def total_chunks(self) -> int:
        return len(self.chunks) or 1

    @property
    def parties(self) -> list[str]:
        return []

    @property
    def contract_date(self) -> str:
        return ""

    @property
    def prior_clause_types(self) -> list[str]:
        return [c.clause_type.value for c in self.clauses]


class ParseStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        suffix = ctx.input_file.suffix.lower()
        if suffix == ".pdf":
            ctx.raw_text = PDFParser().parse(ctx.input_file)
        elif suffix == ".docx":
            ctx.raw_text = DOCXParser().parse(ctx.input_file)
        elif suffix in {".html", ".htm"}:
            ctx.raw_text = html_to_text(ctx.input_file.read_text(encoding="utf-8"))
        else:
            ctx.raw_text = ctx.input_file.read_text(encoding="utf-8")
        return ctx


class ChunkStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        max_tokens = {"quick": 2400, "standard": 1800, "deep": 1200}.get(ctx.config.depth, 1800)
        ctx.chunks = TextChunker(max_tokens=max_tokens).chunk(ctx.raw_text)
        return ctx


class DetectStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        return ctx


class ExtractStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        extractor = ClauseExtractor(
            llm_client=self.deps.get("llm_client"),
            prompt_builder=ExtractionPromptBuilder(),
            cache=self.deps.get("cache"),
            config=ctx.config,
        )
        result = await extractor.extract(ctx.chunks, ctx)
        ctx.clauses = result.clauses
        ctx.missing_clauses = result.missing_clauses
        return ctx


class ValidateStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        return ctx


class RiskStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.risk_summary = RiskAnalyzer().analyze(ctx.clauses, ctx.missing_clauses)
        return ctx


class SummarizeStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.executive_summary = Summarizer().summarize(ctx.clauses, ctx.risk_summary)
        return ctx


class FormatStage:
    def __init__(self, deps: dict[str, Any]):
        self.deps = deps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        metadata = ContractMetadata(
            filename=ctx.input_file.name,
            contract_type=self._contract_type(ctx.config.contract_type),
            governing_law=ctx.config.jurisdiction,
            token_count=count_tokens(ctx.raw_text),
        )
        elapsed = int((time.perf_counter() - ctx.started_at) * 1000)
        cache = self.deps.get("cache")
        ctx.result = AnalysisReport(
            metadata=metadata,
            clauses=ctx.clauses,
            risk_summary=ctx.risk_summary,
            executive_summary=ctx.executive_summary,
            processing_meta=ProcessingMeta(
                chunks_processed=len(ctx.chunks),
                cache_hits=getattr(cache, "hits", 0),
                processing_time_ms=elapsed,
            ),
        )
        return ctx

    @staticmethod
    def _contract_type(value: str) -> ContractType:
        try:
            return ContractType(value)
        except ValueError:
            return ContractType.UNKNOWN

