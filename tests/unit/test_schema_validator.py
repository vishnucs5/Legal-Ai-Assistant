from __future__ import annotations

from schemas.validator import validate_clause_json


def test_clause_schema_validator_accepts_valid_payload():
    payload = {
        "clauses": [
            {
                "clause_id": "C001",
                "clause_type": "payment",
                "verbatim_text": "Client shall pay all undisputed invoices within thirty days.",
                "plain_english": "Client pays invoices within thirty days.",
                "party_bound": "party_a",
                "obligations": ["Client shall pay all undisputed invoices within thirty days."],
                "risk_score": 2,
                "risk_flags": [],
                "chunk_id": 0,
            }
        ],
        "missing_clauses": [],
    }

    assert validate_clause_json(payload).clauses[0].clause_id == "C001"

