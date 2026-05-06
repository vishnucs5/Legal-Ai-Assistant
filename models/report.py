from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from models.clause import Clause
from models.contract import ContractMetadata


class RiskItem(BaseModel):
    risk_id: str
    severity: str
    category: str
    affected_clause_ids: List[str] = Field(default_factory=list)
    plain_english_explanation: str
    recommended_action: str
    suggested_redline: Optional[str] = None


class RiskSummary(BaseModel):
    overall_risk_score: float = 0.0
    risk_level: str = "low"
    risks: List[RiskItem] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)
    one_sided_clauses: List[str] = Field(default_factory=list)


class CriticalDate(BaseModel):
    label: str
    date: str


class ExecutiveSummary(BaseModel):
    one_paragraph: str
    key_obligations: List[str] = Field(default_factory=list)
    critical_dates: List[CriticalDate] = Field(default_factory=list)
    negotiation_priorities: List[str] = Field(default_factory=list)


class ProcessingMeta(BaseModel):
    model: str = "heuristic"
    total_tokens_used: int = 0
    chunks_processed: int = 0
    cache_hits: int = 0
    processing_time_ms: int = 0


class AnalysisReport(BaseModel):
    contract_id: UUID = Field(default_factory=uuid4)
    metadata: ContractMetadata
    clauses: List[Clause] = Field(default_factory=list)
    risk_summary: RiskSummary
    executive_summary: ExecutiveSummary
    processing_meta: ProcessingMeta = Field(default_factory=ProcessingMeta)

