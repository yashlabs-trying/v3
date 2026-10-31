# Security Review — DataForge V3.3 (Phase H)

## 1. Threat model

Trajectory and evidence data are **untrusted**. A hostile or corrupted trace may
contain forged assertions, instruction-like prompt injection, credentials,
path-traversal references, oversized payloads, or an incomplete/duplicated
history. The engine must not be manipulated by any of these into producing an
authoritative false finding.

## 2. Controls and where they live

| Threat | Control | Module / test |
|---|---|---|
| Prompt injection in log/tool output | instruction-like spans tagged, never executed | `streaming.sanitize_log_text`, `detect_injection`; `test_prompt_injection_in_tool_output_is_tagged` |
| Forged "success"/reward text | success text is data; no finding/strength derived from it | `test_forged_success_text_does_not_create_a_strength` |
| Fabricated events | engine only parses events present in the artifact | `trajectory.py`; malformed entries skipped with warning |
| Duplicate events inflating evidence | dedup by `event_id`, warns the count | `streaming.dedupe_events`; `test_duplicate_events_are_dropped_with_warning` |
| Out-of-order events | stable re-order by timestamp | `streaming.order_events`; `test_out_of_order_events_are_stably_reordered` |
| Path traversal / absolute path evidence | rejected by the resolver | `evidence.EvidenceResolver.resolve`; `test_evidence_resolver_rejects_path_escape` |
| Unresolvable evidence as authority | finding downgraded to HYPOTHESIS | `driver._downgrade_unresolved`; `test_unresolved_evidence_downgrades_finding_to_hypothesis` |
| Oversized / DoS input | byte, event and field caps; streaming | `schema.py` bounds; `test_large_trajectory_is_bounded`, `test_dedupe_scales_linearly` |
| Credential exposure | redaction patterns (API keys, bearer, private keys) before storage | `trajectory.redact` |
| Silent evidence tampering | resolver hashes and flags mutable logs non-authoritative; evidence tree is read-only | `evidence.py`; `EVIDENCE_INTEGRITY_NOTE.md` retained |
| Modifying evaluation artifacts | engine never writes to `jobs/`, `findings/*.json` inputs | by construction (write path is `findings/intelligence/` only) |

## 3. Threat-model test results

All adversarial cases are exercised in
`dataforge_v3/tests/test_intelligence_engine.py` (26 tests) and
`test_intelligence_integration.py` (9). Relevant ones: forged success, prompt
injection, duplicates, out-of-order, malformed events, path escape, unresolved
evidence downgrade, oversized trajectory, contaminated-patch detection.

**Result on the tested threat model:** untrusted traces did not manufacture any
authoritative finding; every authoritative finding resolved to preserved evidence.

## 4. Disclosure: evidence integrity

Two `final-vuls` mutable log checksums changed after freeze (see
`reports/EVIDENCE_INTEGRITY_NOTE.md`). This is preserved, not hidden. The resolver
marks `*.job.log` / `*.trial.log` **non-authoritative**, so no authoritative claim
rests on them. The vuls baseline used here (`f3-vuls-a1`) is a different, complete
job not covered by the mismatched entries.

## 5. Residual risk

- A malicious trajectory could still inject a *plausible* payload string into the
  `symptom` text; it is tagged and never executed, but human review remains the
  backstop for adversarial inputs in production.
- The resolver verifies existence and hash-at-read, but a manifest of *expected*
  hashes is only available where one was frozen; absent that, a claim is
  "resolved" but not "hash-pinned".

## 6. Credential handling

`result.json` files contain a Harbor-masked key (`sk-d****6Py`) and env var names.
The engine reads scores/usage only; no credential value is copied into any
V3.3 artifact. A scan of `dataforge_v3/intelligence/*.py` found only the
redaction *patterns*, no secrets.
