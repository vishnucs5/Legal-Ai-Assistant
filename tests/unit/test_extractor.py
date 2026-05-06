from __future__ import annotations

import asyncio
from pathlib import Path

from core.extractor import ClauseExtractor
from parsers.text_chunker import TextChunk
from pipeline.stages import AnalysisConfig, PipelineContext


def test_extractor_detects_and_scores_risky_clauses():
    asyncio.run(_run_extractor())


async def _run_extractor():
    text = "Limitation of Liability\nVendor's liability is uncapped for all claims under this Agreement."
    ctx = PipelineContext(input_file=Path("x.txt"), config=AnalysisConfig(contract_type="saas"), raw_text=text)
    chunks = [TextChunk(text=text, index=0, start_token=0, end_token=20)]

    result = await ClauseExtractor().extract(chunks, ctx)

    assert result.clauses
    assert result.clauses[0].clause_type.value == "liability"
    assert result.clauses[0].risk_score >= 6

