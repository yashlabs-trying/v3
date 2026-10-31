# DataForge V3.3 — Architecture

**Layer:** Evaluation Intelligence (additive above V3.1 reliability and V3.2 semantic verification).
**Branch:** `v3.3-phase3` (base `122683ac614f6bcb233c7f9b2e6df31cc5e41154`, V3.2 Phase 2).
**Status:** implemented, tested, measured. No V2 reward, V3.1 classification or V3.2 verdict is modified.

---

## 1. Where V3.3 sits

```
                 raw agent execution (Harbor / mini-swe-agent artifacts)
                              │
        ┌─────────────────────┼──────────────────────────┐
        ▼                     ▼                          ▼
   V3.1 reliability      V3.2 semantic              V3.3 observable
   (valid? PASS/FAIL/    (correct? contract         trajectory
    INVALID)              clauses + oracles)         (events)
        │                     │                          │
        └──────────┬──────────┴──────────────┬───────────┘
                   ▼                          ▼
        V3.3 Failure Attribution      V3.3 Capability evidence
                   │                          │
                   └────────────┬─────────────┘
                                ▼
                    V3.3 Recommendations + Reporting
                                ▼
                 per-task diagnosis (JSON + Markdown)
                    + fleet capability profile
```

V3.3 consumes the two lower layers' *verdicts and evidence*. It never re-scores.

## 2. Module map (`dataforge_v3/intelligence/`)

| Module | Responsibility |
|---|---|
| `schema.py` | Evidence contract: `Event`, `EvidenceRef`, `Finding`, `DiagnosticClaim`, `CapabilityObservation`, `ExperimentRecommendation`, `Diagnosis`, enums, bounded-input limits. |
| `trajectory.py` | System A: parse `mini-swe-agent-1.1` (and generic) trajectories into bounded, redacted `Event`s. |
| `streaming.py` | System A robustness: dedup, stable re-order, streaming iteration, prompt-injection tagging. |
| `normalizer.py` | System A adapters: bind each task to its raw artifacts + V3.2 semantic evidence (`TaskEvidence`, `SemanticInput`). |
| `evidence.py` | Evidence resolution + hashing; rejects path escapes; flags non-authoritative mutable logs. |
| `attribution.py` | System B: generic failure attribution to V3.2 contract clauses. |
| `capabilities.py` | System C: capability observations with evidence counts (no ability scores). |
| `recommendations.py` | System D: measurable engineering experiments. |
| `experiments.py` | System D: experiment outcome tracking (never fabricates an improvement). |
| `reporting.py` | System E: JSON + Markdown, evidence-resolution audit, honest uncertainty. |
| `driver.py` | Orchestration: per-task `Diagnosis` + fleet profile. |
| `comparison.py` | Phase G: baseline comparison vs an independent answer key. |
| `performance.py` | Phase H: latency, memory, throughput, scaling. |

CLI: `python -m dataforge_v3.cli intelligence --root . --out-dir findings/intelligence`.

## 3. Knowledge states (core discipline)

Every statement is tagged by what the evidence can support:

- **OBSERVED** — directly present in a recorded artifact.
- **REPRODUCED** — re-executed and confirmed (e.g. an oracle counterexample).
- **SUPPORTED** — a causal claim grounded in observed + reproduced evidence.
- **HYPOTHESIS** — plausible but unverified.

The driver **downgrades any finding whose evidence does not resolve to HYPOTHESIS**, so an authoritative claim always carries resolvable evidence.

## 4. Numbers (this run)

- Cohort: 8 attempts (7 tasks + NodeBB recovery).
- Fleet analysis runtime: **0.09 s** (recorded evidence, offline).
- Tests: **136 passing** (101 pre-existing V3.1/V3.2 + 35 new V3.3).
- Verified failure findings: 1 (vuls clause `sort.equal_score_order`).
- Invented weaknesses on passing tasks: **0**. Unsupported accusations: **0**.
- Unresolved evidence references: **0**.

## 5. Extension to other frameworks

`normalizer.py` declares task→artifact mapping as data. A Terminal-Bench adapter only needs a new normalizer + a `COHORT`-style mapping and (optionally) V3.2-style clause evidence; the attribution/capability/recommendation layers are framework-agnostic.

## 6. Non-goals / limits

- The engine cannot read hidden model reasoning; only observable events and recorded messages are used.
- Contracts are human-authored (V3.2); a missed clause shrinks coverage.
- One task per failure class here: capability observations are counts, not ability scores.
