from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from core.comparator import ContractComparator
from pipeline.pipeline import LegalAnalysisPipeline
from pipeline.stages import AnalysisConfig

router = APIRouter()


@router.post("/compare")
async def compare(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    contract_type: str = Form("unknown"),
    jurisdiction: str = Form(""),
) -> dict:
    config = AnalysisConfig(contract_type=contract_type, jurisdiction=jurisdiction)
    pipeline = LegalAnalysisPipeline()
    old_report = await pipeline.run(await _save(old_file), config)
    new_report = await pipeline.run(await _save(new_file), config)
    return ContractComparator().compare(old_report.clauses, new_report.clauses)


async def _save(file: UploadFile) -> Path:
    suffix = Path(file.filename or "contract.txt").suffix or ".txt"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.write(await file.read())
    handle.close()
    return Path(handle.name)

