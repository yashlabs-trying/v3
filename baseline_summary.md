# Baseline Summary — DataForge V3.1 Phase 1A

## Result
| Task | Repo/Lang | Oracle | No-op | DS original | Regrade | Class |
|---|---|---|---|---|---|---|
| nodebb | NodeBB/JS | 1.0 | 0.0 | 0.0 (invalid) | 0.0 (null replay) | INFRASTRUCTURE FAILURE |
| flipt | flipt/Go | 1.0 | 0.0 | 1.0 | 1.0 | NO ISSUE OBSERVED |
| vuls | vuls/Go | 1.0 | 0.0 | 0.0 | 0.0 | AGENT FAILURE (66/67) |
| openlibrary | openlibrary/Py | 1.0 | 0.0 | 1.0 | 1.0 | NO ISSUE OBSERVED |
| teleport | teleport/Go | 1.0 | 0.0 | 1.0 | 1.0 | NO ISSUE OBSERVED |
| ansible | ansible/Py | 1.0 | 0.0 | 1.0 | 1.0 | NO ISSUE OBSERVED |
| elementweb | element-web/TS | 1.0 | 0.0 | 1.0 | 1.0 | NO ISSUE OBSERVED |
| nodebb-recovery (rerun) | NodeBB/JS | 1.0 | 0.0 | 1.0 | 1.0 | recovery only |

## Metrics
- Selected tasks: 7; executed: 6 valid + 1 infrastructure failure.
- Valid DeepSeek patches: 6. Official V2: 5 pass / 1 fail (valid), plus nodebb invalid.
- Oracle pass rate 7/7; no-op rejection rate 7/7.
- Parser discrepancies: 0. Runner/grader disagreements: 0. Regrade disagreements: 0.
- Missing required tests: only the genuinely-failing `TestSortByConfident` (vuls).
- Contradictory results: 0. Confirmed false PASS: 0. Suspected false FAIL: 1 (nodebb, infra).
- Recovery rerun: 1.0 (not counted).
- Estimated model cost: ~$1.48.
- Repeat-control stability: flipt oracle 1.0 ×3.

## Most important issues to fix in V3.1 (do not implement yet)
1. Scope `model.patch` to source paths (exclude untracked runtime state).
2. Make `patch_replay` fail loudly when nothing applies.
3. Assert the agent actually ran; else classify ENVIRONMENT_FAILURE.
4. Pin the coding agent + deps; assert imports/tools.
5. Harden the model connection (non-streaming / short timeout / retries) around the egress sidecar.
