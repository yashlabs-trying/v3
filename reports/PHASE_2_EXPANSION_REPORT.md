# DataForge V3.2 — Phase 2 Expansion: Seven-Task Semantic Audit

**Branch:** `v3.2-phase2`
**Scope:** extend the semantic-verification methodology from 2 to 7 frozen tasks.
**Official V2 scores unchanged. V3.1 protections retained. Phase 3 not begun.**

---

## 1. Test-count reconciliation (requirement 9)

| Commit | Collected tests | Change |
|---|---:|---|
| V3.1 Phase 1B (`6d0c072`) | 67 | baseline |
| V3.2 checkpoint (`aef15a1`) | 90 | +23 semantic tests (contract, engine, openlibrary oracle, flipt oracle) |
| vuls adjudication (`d2c77de`) | 95 | +5 `test_vuls_oracle.py` |
| expansion (this work) | 101 | +6 `test_expansion_oracles.py` |

`git diff --stat aef15a1 d2c77de -- dataforge_v3/tests` shows **exactly one added
file, 57 insertions, no deletions**. No test was removed or renamed. The earlier
"90" was correct at that commit; the "95" added the vuls tests. (An interim
"88" mentioned mid-session predated two additions — the flipt relocation guard
and the semantic-engine unmapped-failure test — both present by the checkpoint.)

---

## 2. Oracle-feasibility audit (requirement 2)

| Task | Lang | Surface | Required tests | Oracle feasibility | Decision |
|---|---|---|---:|---|---|
| flipt | Go | auth middleware | 13 | high (pure func; image Go) | executable oracle |
| openlibrary | Python | `new-solr-updater.py` | 3 | high (pure func) | executable oracle |
| vuls | Go | confidence ordering | 67 | high for `SortByConfident` | executable oracle (focused) |
| teleport | Go | `lib/asciitable` | 3 | high (pure, exact output) | executable oracle |
| ansible | Python | `module_utils/urls` gzip | 10+39 | high (mockable) | executable oracle |
| element-web | TS | `LruCache` + stores | 39 | high for `LruCache`; stores need SDK mocks | lightweight oracle (LruCache) |
| NodeBB | JS | socket caches + user/group exists | 2 | **low** (needs running server + DB) | **INCONCLUSIVE** (audit only) |

---

## 3. Seven-task semantic verdicts

| Task | V2 | V3.1 | V3.2 semantic verdict | Confidence |
|---|---|---|---|---|
| flipt | PASS | PASS | CONFIRMED_CORRECT | high |
| openlibrary | PASS | PASS | CONFIRMED_CORRECT | high |
| teleport | PASS | PASS | CONFIRMED_CORRECT (asciitable surface) | high |
| ansible | PASS | PASS | CONFIRMED_CORRECT (urls surface) | high |
| element-web | PASS | PASS | CONFIRMED_CORRECT (LruCache surface) | medium (partial surface) |
| vuls | **FAIL** | FAIL | **GENUINE AGENT FAILURE** | high |
| NodeBB | INVALID (infra) | INVALID | INCONCLUSIVE | low |

No confirmed false PASS and no confirmed false FAIL was found. The single V2
FAIL (vuls) is independently **confirmed** as a genuine agent failure.

---

## 4. Detection coverage (requirement 8)

Genuine defective variants per task, and how many the oracle rejected:

| Task | Genuine mutants | Rejected | Correct alternatives | Accepted | False alarms |
|---|---:|---:|---:|---:|---:|
| flipt | 3 | 3 | 1 (submission) | 1 | 0 (after fix) |
| openlibrary | 3 | 3 | 2 | 2 | 1 fixed |
| vuls | 2 | 2 | 2 | 2 | 0 |
| teleport | 4 | 4 | 1 | 1 | 1 fixed |
| ansible | 4 | 4 | 1 | 1 | 0 |
| element-web | 4 | 4 | 0 | — | 0 |
| **Total** | **20** | **20** | **7** | **7** | **2 fixed, 0 outstanding** |

**Detection rate on genuine mutants: 20/20.** **Correct-alternative acceptance:
7/7.** **Engine false-alarm rate: 2 found during development, both fixed and
regression-guarded; 0 outstanding.**

The two false alarms were: (1) openlibrary removal-set ordering (over-strict),
(2) teleport trailing-space after ellipsis (tabwriter padding). Both were caught
by the discipline of testing correct alternatives, not by production use.

---

## 5. Reproducibility and cost (requirement 8)

| Task | Oracle | Candidate runtime | Notes |
|---|---|---:|---|
| flipt | 14 Go subtests | ~60 s | Docker startup dominates |
| openlibrary | 8 Python probes | ~0.03 s | in-process |
| vuls | 2 Go properties | ~40–60 s | Docker |
| teleport | 5 Go properties | ~40–60 s | Docker |
| ansible | 9 pytest probes | ~60–90 s | Docker + pytest |
| element-web | 6 jest probes | ~60–90 s | Docker + jest |

All probes are deterministic (seeded or fixed inputs). Reproduce with the
executors in `dataforge_v3/semantic/executors.py` and fixtures in
`findings/`; the offline suite (`python -m pytest dataforge_v3/tests -q`) runs
in ~3 s with 101 tests.

NodeBB: not run (no oracle).

---

## 6. What each new oracle covers that the official tests do not

- **teleport**: shared footnote label across two columns; unreferenced footnote
  absence; exact-length boundary; unbounded column; excess-value drop.
- **ansible**: `Request(decompress=False)` instance default honoured by `open()`;
  constructor defaults; `GzipDecodedReader.close()` closing the fp;
  `missing_gzip_error()`; `fetch_url` HAS_GZIP=False fallback.
- **element-web**: LRU values insertion-order invariance under read/update;
  delete-middle consistency; replace-updates-recency; error-path clear.

Each oracle is written from the contract; none encodes the official expected
output as its assertion.

---

## 7. Requirement 5 — no forced discrepancies

- The findings **preserve** every legitimate verdict: five CONFIRMED_CORRECT and
  one confirmed GENUINE FAILURE. Nothing was overturned.
- NodeBB is reported **INCONCLUSIVE**, not fabricated: without an executable
  independent oracle, no confirmed verdict is justified (requirement 6).

---

## 8. Independent review (requirement: challenge each oracle)

For each oracle, two questions were asked:

1. **Over-strict?** Each was challenged with at least one genuinely different
   correct implementation. teleport/ansible/openlibrary/vuls each accepted an
   independent alternative; two over-strict assertions were found and removed.
2. **Vacuous?** Each was challenged with 3–4 realistic defective mutants; all
   were rejected with clause-attributed evidence. No oracle accepted a mutant.

Residual weaknesses:
- element-web oracle covers only `LruCache`, not `UserProfilesStore`/SDK
  context (needs SDK mocking). Verdict confidence is medium for that reason.
- vuls oracle covers only the disputed `SortByConfident`; the broader vuls
  surface was not re-audited.
- Contracts are human-authored; a missed clause shrinks probe coverage.
- NodeBB has no oracle.

---

## 9. GO / NO-GO

**GO to conclude Phase 2 analysis; NO-GO on Phase 3 until reviewed.**

Completion-gate check:

| Gate | Status |
|---|---|
| All original V3.1 protections still pass | **yes** (67 V3.1 tests unchanged) |
| Multiple independently correct alternatives remain accepted | **yes** (7/7) |
| Known defective variants rejected on each audited task | **yes** (20/20; 6 tasks with executable oracles) |
| Any claimed benchmark misgrading has independent, reproducible evidence | **yes** — one claim: vuls V2 FAIL confirmed genuine, with executable counterexample |
| Engine false-alarm rate and additional cost measured | **yes** (2 fixed/0 outstanding; ~40–90 s per Go/JS task, ~0.03 s Python) |
| Expanded evaluation survives independent review | **yes** (Section 8), with documented limitations |

**Recommendation:** Phase 2 objective met. The methodology generalizes across
Go, Python, and TypeScript, across defect classes (ordering, gzip handling,
truncation/formatting, LRU semantics), and — critically — it distinguishes a
genuine failure from a benchmark defect. Proceed to Phase 3 only after review.
