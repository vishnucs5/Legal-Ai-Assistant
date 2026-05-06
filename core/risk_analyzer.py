from __future__ import annotations

from models.clause import Clause
from models.report import RiskItem, RiskSummary


class RiskAnalyzer:
    def analyze(self, clauses: list[Clause], missing_clauses: list[str] | None = None) -> RiskSummary:
        risks: list[RiskItem] = []
        for idx, clause in enumerate(clauses, start=1):
            severity = self._severity(clause.risk_score)
            if severity == "info":
                continue
            risks.append(
                RiskItem(
                    risk_id=f"R{idx:03d}",
                    severity=severity,
                    category=self._category(clause.clause_type.value),
                    affected_clause_ids=[clause.clause_id],
                    plain_english_explanation=self._explain(clause),
                    recommended_action=self._action(severity),
                    suggested_redline=self._redline(clause),
                )
            )

        overall = round(sum(c.risk_score for c in clauses) / len(clauses), 1) if clauses else 0.0
        one_sided = [c.clause_id for c in clauses if c.party_bound.value in {"party_a", "party_b"} and c.risk_score >= 6]
        return RiskSummary(
            overall_risk_score=overall,
            risk_level=self._severity(overall),
            risks=risks,
            missing_clauses=missing_clauses or [],
            one_sided_clauses=one_sided,
        )

    @staticmethod
    def _severity(score: float) -> str:
        if score >= 8.5:
            return "critical"
        if score >= 6.0:
            return "high"
        if score >= 3.0:
            return "medium"
        if score > 0:
            return "low"
        return "info"

    @staticmethod
    def _category(clause_type: str) -> str:
        if clause_type in {"liability", "indemnification", "payment"}:
            return "financial"
        if clause_type in {"ip_ownership", "warranty"}:
            return "ip"
        if clause_type == "data_privacy":
            return "compliance"
        if clause_type in {"auto_renewal", "non_compete"}:
            return "relationship"
        return "operational"

    @staticmethod
    def _action(severity: str) -> str:
        return {"critical": "reject", "high": "escalate", "medium": "negotiate", "low": "monitor"}.get(severity, "accept")

    @staticmethod
    def _explain(clause: Clause) -> str:
        if clause.risk_flags:
            return f"The clause may create risk because it includes {', '.join(clause.risk_flags)}."
        return f"The {clause.clause_type.value.replace('_', ' ')} clause is moderately unfavorable and should be checked against business expectations."

    @staticmethod
    def _redline(clause: Clause) -> str | None:
        if clause.risk_score < 3:
            return None
        if clause.clause_type.value == "liability":
            return "Each party's aggregate liability will be capped at fees paid or payable in the twelve months before the claim, excluding confidentiality breaches and payment obligations."
        if clause.clause_type.value == "auto_renewal":
            return "Renewal requires written notice at least thirty days before the end of the then-current term."
        return "Revise the clause to make obligations mutual, commercially reasonable, and subject to clear notice and cure periods."

