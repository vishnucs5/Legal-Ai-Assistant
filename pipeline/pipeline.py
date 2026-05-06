from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from pipeline.cache import SQLiteLLMCache
from pipeline.stages import (
    AnalysisConfig,
    ChunkStage,
    DetectStage,
    ExtractStage,
    FormatStage,
    ParseStage,
    PipelineContext,
    RiskStage,
    SummarizeStage,
    ValidateStage,
)
from config.settings import settings


class LegalAnalysisPipeline:
    STAGES = [ParseStage, ChunkStage, DetectStage, ExtractStage, ValidateStage, RiskStage, SummarizeStage, FormatStage]

    def __init__(self, deps: dict | None = None):
        self.deps = deps or {}
        self.deps.setdefault("cache", SQLiteLLMCache(settings.cache_path))
        if "llm_client" not in self.deps and settings.anthropic_api_key:
            from core.llm import AnthropicClient

            self.deps["llm_client"] = AnthropicClient()

    async def run(self, input_file: Path, config: AnalysisConfig) -> object:
        ctx = PipelineContext(input_file=input_file, config=config)
        async with self._telemetry(ctx):
            for stage_cls in self.STAGES:
                ctx = await stage_cls(self.deps).run(ctx)
                if ctx.should_abort:
                    break
        return ctx.result

    async def stream(self, input_file: Path, config: AnalysisConfig) -> AsyncIterator[str]:
        ctx = PipelineContext(input_file=input_file, config=config)
        for stage_cls in self.STAGES:
            ctx = await stage_cls(self.deps).run(ctx)
            payload = {"stage": stage_cls.__name__, "complete": True}
            if stage_cls is ExtractStage:
                payload["clauses"] = [c.model_dump(mode="json") for c in ctx.clauses]
            if stage_cls is FormatStage and ctx.result:
                payload["result"] = ctx.result.model_dump(mode="json")
            yield f"data: {json.dumps(payload, default=str)}\n\n"

    @asynccontextmanager
    async def _telemetry(self, ctx: PipelineContext):
        yield
