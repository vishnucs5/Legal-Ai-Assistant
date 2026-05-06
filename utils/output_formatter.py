from __future__ import annotations

import json

from models.report import AnalysisReport


class OutputFormatter:
    def format(self, report: AnalysisReport, output: str = "json") -> str:
        if output == "markdown":
            return self.markdown(report)
        if output == "html":
            return self.html(report)
        return json.dumps(report.model_dump(mode="json"), indent=2, default=str)

    def markdown(self, report: AnalysisReport) -> str:
        lines = [
            f"# Contract Analysis: {report.metadata.filename}",
            "",
            report.executive_summary.one_paragraph,
            "",
            "## Risks",
        ]
        for risk in report.risk_summary.risks:
            lines.append(f"- **{risk.severity.upper()}** ({risk.category}): {risk.plain_english_explanation}")
        lines.extend(["", "## Clauses"])
        for clause in report.clauses:
            lines.append(f"- `{clause.clause_id}` **{clause.clause_type.value}** risk {clause.risk_score}/10")
        return "\n".join(lines)

    def html(self, report: AnalysisReport) -> str:
        risks = "".join(f"<li><strong>{r.severity}</strong>: {r.plain_english_explanation}</li>" for r in report.risk_summary.risks)
        clauses = "".join(f"<li>{c.clause_id}: {c.clause_type.value} ({c.risk_score}/10)</li>" for c in report.clauses)
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Contract Analysis</title>"
            "<style>body{font-family:Arial,sans-serif;max-width:920px;margin:40px auto;line-height:1.5}</style></head><body>"
            f"<h1>{report.metadata.filename}</h1><p>{report.executive_summary.one_paragraph}</p>"
            f"<h2>Risks</h2><ul>{risks}</ul><h2>Clauses</h2><ul>{clauses}</ul></body></html>"
        )

