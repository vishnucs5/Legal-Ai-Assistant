from __future__ import annotations

from difflib import unified_diff

from models.clause import Clause


class ContractComparator:
    def compare(self, old_clauses: list[Clause], new_clauses: list[Clause]) -> dict:
        old_by_type = {c.clause_type.value: c for c in old_clauses}
        new_by_type = {c.clause_type.value: c for c in new_clauses}
        old_types = set(old_by_type)
        new_types = set(new_by_type)

        changed = []
        for clause_type in sorted(old_types & new_types):
            old_text = old_by_type[clause_type].verbatim_text.splitlines()
            new_text = new_by_type[clause_type].verbatim_text.splitlines()
            if old_text != new_text:
                changed.append(
                    {
                        "clause_type": clause_type,
                        "diff": "\n".join(unified_diff(old_text, new_text, fromfile="old", tofile="new", lineterm="")),
                        "risk_delta": round(new_by_type[clause_type].risk_score - old_by_type[clause_type].risk_score, 1),
                    }
                )

        return {
            "added_clause_types": sorted(new_types - old_types),
            "deleted_clause_types": sorted(old_types - new_types),
            "changed_clauses": changed,
            "new_risk_vectors": [item for item in changed if item["risk_delta"] > 0],
        }

