from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContractType(str, Enum):
    NDA = "nda"
    SOW = "sow"
    EMPLOYMENT = "employment"
    SAAS = "saas"
    MSA = "msa"
    LEASE = "lease"
    IP_ASSIGNMENT = "ip_assignment"
    VENDOR = "vendor"
    UNKNOWN = "unknown"


class DetectedParty(BaseModel):
    name: str
    role: str = "unspecified"


class ContractMetadata(BaseModel):
    filename: str
    contract_type: ContractType = ContractType.UNKNOWN
    detected_parties: List[DetectedParty] = Field(default_factory=list)
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    governing_law: str = ""
    token_count: int = 0
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class Contract(BaseModel):
    contract_id: UUID = Field(default_factory=uuid4)
    metadata: ContractMetadata
    raw_text: str = ""

