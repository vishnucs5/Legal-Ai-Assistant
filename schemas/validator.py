from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.clause import ClauseList
from models.report import AnalysisReport


def validate_clause_json(payload: str | dict[str, Any]) -> ClauseList:
    if isinstance(payload, str):
        return ClauseList.model_validate_json(payload)
    return ClauseList.model_validate(payload)


def validate_report_json(payload: str | dict[str, Any]) -> AnalysisReport:
    if isinstance(payload, str):
        return AnalysisReport.model_validate_json(payload)
    return AnalysisReport.model_validate(payload)


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

