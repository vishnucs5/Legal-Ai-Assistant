from __future__ import annotations

from prompts.base import PromptTemplate


SYSTEM_PROMPT = """You are LexAnalyzer, an expert legal contract analyst with deep experience in commercial law, IP agreements, employment agreements, and SaaS contracts.
Extract all legally significant clauses from the contract text.
For each clause identify type, exact verbatim text, risk score 0-10, party bound, obligations, and missing standard clauses.
Respond only with valid JSON matching the schema. Start with { and end with }. Do not include markdown."""

USER_PROMPT = """CONTRACT TYPE: {contract_type}
JURISDICTION: {jurisdiction}
ANALYSIS DEPTH: {depth}
CHUNK: {chunk_index} of {total_chunks}

--- CONTRACT TEXT BEGIN ---
{contract_text}
--- CONTRACT TEXT END ---

Reason privately before answering. Prioritize completeness over speed.
Prior context:
Parties identified: {parties}
Contract date: {contract_date}
Already extracted clauses: {prior_clause_types}

Output format:
{{"clauses":[{{"clause_id":"C001","clause_type":"liability","heading":null,"verbatim_text":"...","plain_english":"...","party_bound":"both","obligations":[],"risk_score":0,"risk_flags":[],"page_ref":null,"chunk_id":0}}],"missing_clauses":[]}}"""


class ExtractionPromptBuilder:
    template = PromptTemplate(SYSTEM_PROMPT, USER_PROMPT)

    def build_extraction_prompt(self, chunk, context) -> str:
        return self.template.render(
            contract_type=context.contract_type,
            jurisdiction=context.jurisdiction,
            depth=context.depth,
            chunk_index=chunk.index + 1,
            total_chunks=context.total_chunks,
            contract_text=chunk.text,
            parties=", ".join(context.parties) or "unknown",
            contract_date=context.contract_date or "unknown",
            prior_clause_types=", ".join(context.prior_clause_types) or "none",
        )

