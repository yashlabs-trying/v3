"""A. Specification Contract Auditor (V3.2).

Turns a task's prose instruction plus its official grading contract into a
reviewable list of `ContractClause`s, then audits the relationship between them:

  * clauses that no official required test exercises  -> false-PASS surface
  * official assertions that no clause authorizes     -> possible false-FAIL surface
  * clauses whose wording is not decidable            -> SPECIFICATION_AMBIGUOUS

The contract itself is *data*, declared per task and independently reviewable
(see `dataforge_v3/semantic/tasks/`). This module only performs the audit; it
does not invent requirements, because an LLM-drafted clause is a hypothesis, not
ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dataforge_v3.semantic.model import ClauseKind, ContractClause


@dataclass
class ContractAudit:
    total_clauses: int
    uncovered_clauses: list[str] = field(default_factory=list)
    ambiguous_clauses: list[str] = field(default_factory=list)
    unsupported_restrictions: list[str] = field(default_factory=list)
    evidence_strength: dict[str, str] = field(default_factory=dict)

    @property
    def uncovered_fraction(self) -> float:
        if not self.total_clauses:
            return 0.0
        return len(self.uncovered_clauses) / self.total_clauses

    def to_dict(self) -> dict:
        return {
            "total_clauses": self.total_clauses,
            "uncovered_clauses": self.uncovered_clauses,
            "ambiguous_clauses": self.ambiguous_clauses,
            "unsupported_restrictions": self.unsupported_restrictions,
            "uncovered_fraction": round(self.uncovered_fraction, 4),
            "evidence_strength": self.evidence_strength,
        }


def _is_ambiguous(clause: ContractClause) -> bool:
    """Heuristic for prose that cannot be decided by an executable probe.

    Kept deliberately conservative and reviewable: only flags clauses the
    contract author explicitly marked with an AMBIGUOUS source tag, or clauses
    with no source at all.
    """
    return clause.source.strip().upper() == "AMBIGUOUS" or not clause.source.strip()


def audit_contract(
    clauses: list[ContractClause],
    required_tests: set[str],
) -> ContractAudit:
    """Audit a declared contract against the official required test set.

    `required_tests` are the exact names from `fail_to_pass | pass_to_pass`.
    A clause is "covered" when at least one of its `tested_by_original` names is
    in the required set. Anything else is an uncovered (false-PASS) surface.
    """
    uncovered: list[str] = []
    ambiguous: list[str] = []
    strengths: dict[str, str] = {}

    for c in clauses:
        if _is_ambiguous(c):
            ambiguous.append(c.id)
        covering = [t for t in c.tested_by_original if t in required_tests]
        if covering:
            strengths[c.id] = f"official-tests:{len(covering)}"
        else:
            uncovered.append(c.id)
            strengths[c.id] = "uncovered"

    return ContractAudit(
        total_clauses=len(clauses),
        uncovered_clauses=uncovered,
        ambiguous_clauses=ambiguous,
        unsupported_restrictions=[],
        evidence_strength=strengths,
    )


def flag_unsupported_restrictions(
    asserted_behaviors: list[str],
    clauses: list[ContractClause],
) -> list[str]:
    """Report official assertions that no clause authorizes.

    `asserted_behaviors` are free-text descriptions of what the official tests
    demand (e.g. an exact error string, an implementation detail). Each is judged
    by whether any clause statement mentions its normalized key terms. This is a
    review aid, not a decision: results are hypotheses for a human to confirm.
    """
    unsupported: list[str] = []
    clause_text = " ".join(c.statement.lower() for c in clauses)
    for behavior in asserted_behaviors:
        terms = [t for t in _key_terms(behavior) if len(t) > 3]
        if not terms:
            continue
        if not any(t in clause_text for t in terms):
            unsupported.append(behavior)
    return unsupported


def _key_terms(text: str) -> list[str]:
    import re

    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower())
