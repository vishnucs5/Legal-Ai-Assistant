from __future__ import annotations

from core.risk_analyzer import RiskAnalyzer
from models.clause import Clause, ClauseType


def test_risk_analyzer_creates_high_risk_item():
    clause = Clause(
        clause_id="C001",
        clause_type=ClauseType.LIABILITY,
        verbatim_text="Liability is uncapped.",
        plain_english="Liability is uncapped.",
        risk_score=8.0,
        risk_flags=["uncapped exposure"],
    )

    summary = RiskAnalyzer().analyze([clause])

    assert summary.risk_level == "high"
    assert summary.risks[0].recommended_action == "escalate"

