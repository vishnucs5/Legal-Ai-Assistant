from __future__ import annotations

import asyncio
import json
import re
from difflib import SequenceMatcher
from typing import List, Optional

from models.clause import Clause, ClauseList, ClauseType, PartyBound
from parsers.clause_detector import ClauseDetector


class ClauseExtractor:
    """Multi-chunk clause extraction with cache-backed LLM support and heuristic fallback."""

    def __init__(self, llm_client=None, prompt_builder=None, cache=None, config=None):
        self.llm = llm_client
        self.prompts = prompt_builder
        self.cache = cache
        self.config = config
        self.detector = ClauseDetector()

    async def extract(self, chunks: List[object], context: object) -> ClauseList:
        tasks = [self._extract_chunk(chunk, context) for chunk in chunks]
        raw_results = await asyncio.gather(*tasks)
        return self._fuse_results(raw_results, context)

    async def _extract_chunk(self, chunk: object, context: object) -> ClauseList:
        cache_key = self.cache.make_key(chunk.text, context) if self.cache else None
        if cache_key and (cached := self.cache.get(cache_key)):
            return ClauseList.model_validate_json(cached)

        if self.llm and self.prompts:
            prompt = self.prompts.build_extraction_prompt(chunk, context)
            raw = await self.llm.complete(prompt, response_format="json")
            validated = ClauseList.model_validate_json(raw)
        else:
            validated = self._heuristic_extract(chunk, context)

        if cache_key:
            self.cache.set(cache_key, validated.model_dump_json())
        return validated

    def _heuristic_extract(self, chunk: object, context: object) -> ClauseList:
        detected = self.detector.detect(chunk.text)
        clauses: list[Clause] = []
        for idx, item in enumerate(detected, start=1):
            risk_score, flags = self._score_clause(item.text, item.clause_type)
            clauses.append(
                Clause(
                    clause_id=f"C{idx:03d}",
                    clause_type=item.clause_type,
                    heading=item.heading,
                    verbatim_text=item.text,
                    plain_english=self._plain_english(item.clause_type, item.text),
                    party_bound=self._party_bound(item.text),
                    obligations=self._obligations(item.text),
                    risk_score=risk_score,
                    risk_flags=flags,
                    chunk_id=getattr(chunk, "index", 0),
                )
            )
        return ClauseList(
            clauses=clauses,
            missing_clauses=self.detector.missing_standard_clauses(detected, context.contract_type),
        )

    def _fuse_results(self, results: List[ClauseList], context: Optional[object] = None) -> ClauseList:
        fused: list[Clause] = []
        missing: set[str] = set()
        for result in results:
            missing.update(result.missing_clauses)
            for clause in result.clauses:
                if not any(self._similar(clause.verbatim_text, existing.verbatim_text) > 0.88 for existing in fused):
                    fused.append(clause)

        for idx, clause in enumerate(fused, start=1):
            clause.clause_id = f"C{idx:03d}"

        present = {clause.clause_type.value for clause in fused}
        return ClauseList(clauses=fused, missing_clauses=sorted(missing - present))

    @staticmethod
    def _similar(left: str, right: str) -> float:
        return SequenceMatcher(None, left[:1200], right[:1200]).ratio()

    @staticmethod
    def _score_clause(text: str, clause_type: ClauseType) -> tuple[float, list[str]]:
        lowered = text.lower()
        score = 2.0
        flags: list[str] = []
        rules = [
            (r"\buncapped\b|no limit|without limitation", 3.5, "uncapped exposure"),
            (r"\bsole discretion\b|for convenience", 1.5, "broad discretionary right"),
            (r"\bautomatic(?:ally)? renew|auto.?renew", 2.5, "automatic renewal"),
            (r"\bindemnif", 2.0, "indemnity obligation"),
            (r"\bliquidated damages|penalt", 2.5, "penalty or liquidated damages"),
            (r"\bnon-compete|noncompete", 2.5, "restrictive covenant"),
            (r"\bassigns? all right|work made for hire", 2.0, "broad IP assignment"),
            (r"\bgdpr|ccpa|personal data", 1.0, "regulated data obligations"),
        ]
        for pattern, bump, flag in rules:
            if re.search(pattern, lowered):
                score += bump
                flags.append(flag)
        if clause_type in {ClauseType.LIABILITY, ClauseType.INDEMNIFICATION, ClauseType.NON_COMPETE}:
            score += 1.0
        return min(10.0, score), flags

    @staticmethod
    def _plain_english(clause_type: ClauseType, text: str) -> str:
        first_sentence = re.split(r"(?<=[.!?])\s+", text.strip())[0]
        return f"This {clause_type.value.replace('_', ' ')} clause says: {first_sentence[:240]}"

    @staticmethod
    def _party_bound(text: str) -> PartyBound:
        lowered = text.lower()
        if "each party" in lowered or "both parties" in lowered or "either party" in lowered:
            return PartyBound.BOTH
        has_a = "party a" in lowered or "client" in lowered or "company" in lowered
        has_b = "party b" in lowered or "vendor" in lowered or "contractor " in lowered or "employee" in lowered
        if has_a and has_b:
            return PartyBound.BOTH
        if has_a:
            return PartyBound.PARTY_A
        if has_b:
            return PartyBound.PARTY_B
        return PartyBound.UNSPECIFIED

    @staticmethod
    def _obligations(text: str) -> list[str]:
        patterns = re.findall(r"([^.]{0,80}\b(?:shall|must|required to|agrees to)\b[^.]{0,180}\.)", text, re.IGNORECASE)
        return [item.strip() for item in patterns[:5]]
