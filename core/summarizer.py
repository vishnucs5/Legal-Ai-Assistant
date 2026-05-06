from __future__ import annotations

import re

from models.clause import Clause
from models.report import CriticalDate, ExecutiveSummary, RiskSummary


class Summarizer:
    date_re = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})\b")

    def summarize(self, clauses: list[Clause], risk_summary: RiskSummary) -> ExecutiveSummary:
        highest = sorted(clauses, key=lambda c: c.risk_score, reverse=True)[:3]
        types = ", ".join(c.clause_type.value.replace("_", " ") for c in highest) or "no material clauses"
        paragraph = (
            f"This contract contains {len(clauses)} detected legal clauses. "
            f"Overall risk is {risk_summary.risk_level} ({risk_summary.overall_risk_score}/10), with the main negotiation focus on {types}."
        )
        obligations = [ob for clause in clauses for ob in clause.obligations][:8]
        dates = self._dates(clauses)
        priorities = [risk.plain_english_explanation for risk in risk_summary.risks[:5]]
        return ExecutiveSummary(
            one_paragraph=paragraph,
            key_obligations=obligations,
            critical_dates=dates,
            negotiation_priorities=priorities,
        )

    def _dates(self, clauses: list[Clause]) -> list[CriticalDate]:
        found: list[CriticalDate] = []
        for clause in clauses:
            for match in self.date_re.findall(clause.verbatim_text):
                found.append(CriticalDate(label=clause.heading or clause.clause_type.value, date=match))
                if len(found) >= 6:
                    return found
        return found

