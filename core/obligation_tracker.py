from __future__ import annotations

from collections import defaultdict

from models.clause import Clause


class ObligationTracker:
    def map_by_party(self, clauses: list[Clause]) -> dict[str, list[dict[str, str]]]:
        obligations: dict[str, list[dict[str, str]]] = defaultdict(list)
        for clause in clauses:
            for obligation in clause.obligations:
                obligations[clause.party_bound.value].append(
                    {"clause_id": clause.clause_id, "clause_type": clause.clause_type.value, "obligation": obligation}
                )
        return dict(obligations)

