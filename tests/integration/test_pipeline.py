from __future__ import annotations

import asyncio
from pathlib import Path

from pipeline.pipeline import LegalAnalysisPipeline
from pipeline.stages import AnalysisConfig


def test_pipeline_runs_sample_contract():
    report = asyncio.run(
        LegalAnalysisPipeline().run(
            Path("tests/fixtures/sample_contracts/sample_nda.txt"),
            AnalysisConfig(contract_type="nda", jurisdiction="New York"),
        )
    )

    assert report.clauses
    assert report.risk_summary.overall_risk_score > 0
    assert report.executive_summary.one_paragraph

