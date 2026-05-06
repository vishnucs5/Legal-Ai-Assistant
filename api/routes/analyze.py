from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from pipeline.pipeline import LegalAnalysisPipeline
from pipeline.stages import AnalysisConfig

router = APIRouter()


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    contract_type: str = Form("unknown"),
    depth: str = Form("standard"),
    jurisdiction: str = Form(""),
) -> dict:
    path = await _save_upload(file)
    report = await LegalAnalysisPipeline().run(path, AnalysisConfig(contract_type=contract_type, depth=depth, jurisdiction=jurisdiction))
    return report.model_dump(mode="json")


@router.post("/analyze/stream")
async def analyze_stream(
    file: UploadFile = File(...),
    contract_type: str = Form("unknown"),
    depth: str = Form("standard"),
    jurisdiction: str = Form(""),
) -> StreamingResponse:
    path = await _save_upload(file)
    pipeline = LegalAnalysisPipeline()
    config = AnalysisConfig(contract_type=contract_type, depth=depth, jurisdiction=jurisdiction)
    return StreamingResponse(pipeline.stream(path, config), media_type="text/event-stream")


async def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "contract.txt").suffix or ".txt"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.write(await file.read())
    handle.close()
    return Path(handle.name)

