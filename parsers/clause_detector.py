from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from models.clause import ClauseType


@dataclass(frozen=True)
class DetectedClause:
    heading: Optional[str]
    text: str
    clause_type: ClauseType


TYPE_PATTERNS = {
    ClauseType.LIABILITY: r"\b(liability|limitation of liability|damages)\b",
    ClauseType.INDEMNIFICATION: r"\b(indemnif|hold harmless|defend)\b",
    ClauseType.TERMINATION: r"\b(termination|terminate|survival)\b",
    ClauseType.PAYMENT: r"\b(payment|fees?|invoice|taxes|late fee)\b",
    ClauseType.IP_OWNERSHIP: r"\b(intellectual property|ip ownership|work product|assignment)\b",
    ClauseType.CONFIDENTIALITY: r"\b(confidential|non-disclosure|nondisclosure)\b",
    ClauseType.DISPUTE_RESOLUTION: r"\b(dispute|arbitration|venue|jurisdiction)\b",
    ClauseType.WARRANTY: r"\b(warrant|representation|as is)\b",
    ClauseType.GOVERNING_LAW: r"\b(governing law|laws of)\b",
    ClauseType.FORCE_MAJEURE: r"\b(force majeure|act of god|unavoidable)\b",
    ClauseType.NON_COMPETE: r"\b(non-compete|noncompete|restrictive covenant)\b",
    ClauseType.AUTO_RENEWAL: r"\b(auto.?renew|automatic renewal|renewal term)\b",
    ClauseType.DATA_PRIVACY: r"\b(data privacy|personal data|gdpr|ccpa|data protection)\b",
}


class ClauseDetector:
    heading_re = re.compile(
        r"(?m)^\s*(?:\d+(?:\.\d+)*[.)]?\s+)?([A-Z][A-Za-z0-9 /&,\-]{2,80})\s*$"
    )

    def detect(self, text: str) -> List[DetectedClause]:
        sections = self._split_by_headings(text)
        if not sections:
            sections = [(None, text.strip())]

        detected = [
            DetectedClause(heading=heading, text=body.strip(), clause_type=self.classify(f"{heading or ''}\n{body}"))
            for heading, body in sections
            if len(body.strip()) >= 10
        ]
        return [item for item in detected if item.clause_type != ClauseType.OTHER] or detected

    def classify(self, text: str) -> ClauseType:
        for clause_type, pattern in TYPE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return clause_type
        return ClauseType.OTHER

    def missing_standard_clauses(self, clauses: Iterable[DetectedClause], contract_type: str) -> List[str]:
        present = {clause.clause_type for clause in clauses}
        expected = {
            "nda": {ClauseType.CONFIDENTIALITY, ClauseType.GOVERNING_LAW, ClauseType.TERMINATION, ClauseType.DISPUTE_RESOLUTION},
            "saas": {ClauseType.PAYMENT, ClauseType.LIABILITY, ClauseType.DATA_PRIVACY, ClauseType.TERMINATION, ClauseType.WARRANTY},
            "sow": {ClauseType.PAYMENT, ClauseType.IP_OWNERSHIP, ClauseType.TERMINATION, ClauseType.WARRANTY},
            "employment": {ClauseType.CONFIDENTIALITY, ClauseType.NON_COMPETE, ClauseType.TERMINATION, ClauseType.IP_OWNERSHIP},
            "msa": {ClauseType.LIABILITY, ClauseType.INDEMNIFICATION, ClauseType.PAYMENT, ClauseType.GOVERNING_LAW},
            "lease": {ClauseType.PAYMENT, ClauseType.TERMINATION, ClauseType.GOVERNING_LAW},
            "vendor": {ClauseType.PAYMENT, ClauseType.LIABILITY, ClauseType.INDEMNIFICATION, ClauseType.DATA_PRIVACY},
        }.get(contract_type, {ClauseType.LIABILITY, ClauseType.TERMINATION, ClauseType.GOVERNING_LAW})
        return sorted(clause.value for clause in expected - present)

    def _split_by_headings(self, text: str) -> List[tuple[Optional[str], str]]:
        matches = list(self.heading_re.finditer(text))
        sections: List[tuple[Optional[str], str]] = []
        for idx, match in enumerate(matches):
            heading = match.group(1).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if body:
                sections.append((heading, body))
        return sections

