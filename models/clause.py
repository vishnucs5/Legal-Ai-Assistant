from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ClauseType(str, Enum):
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    TERMINATION = "termination"
    PAYMENT = "payment"
    IP_OWNERSHIP = "ip_ownership"
    CONFIDENTIALITY = "confidentiality"
    DISPUTE_RESOLUTION = "dispute_resolution"
    WARRANTY = "warranty"
    GOVERNING_LAW = "governing_law"
    FORCE_MAJEURE = "force_majeure"
    NON_COMPETE = "non_compete"
    AUTO_RENEWAL = "auto_renewal"
    DATA_PRIVACY = "data_privacy"
    OTHER = "other"


class PartyBound(str, Enum):
    PARTY_A = "party_a"
    PARTY_B = "party_b"
    BOTH = "both"
    UNSPECIFIED = "unspecified"


class Clause(BaseModel):
    clause_id: str = Field(pattern=r"^C\d{3}$")
    clause_type: ClauseType
    heading: Optional[str] = None
    verbatim_text: str = Field(min_length=10)
    plain_english: str = Field(default="")
    party_bound: PartyBound = PartyBound.UNSPECIFIED
    obligations: List[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=10.0)
    risk_flags: List[str] = Field(default_factory=list)
    page_ref: Optional[int] = None
    chunk_id: int = 0

    @field_validator("risk_score")
    @classmethod
    def round_risk_score(cls, value: float) -> float:
        return round(value, 1)


class ClauseList(BaseModel):
    clauses: List[Clause] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)

