# NodeBB Infrastructure Case — DataForge V3.3 (Negative Control)

**Task:** `instance_NodeBB__NodeBB-00c70ce7b0541cfc...`
**Attempt:** `final-nodebb` (original DeepSeek). **V2:** reward 0.0.
**V3.1:** INVALID. **V3.2:** INCONCLUSIVE (no oracle).

Generated artifact: `findings/intelligence/per_task/NodeBB.md` (+ `.json`).

---

## 1. The control's purpose

Demonstrate that the diagnostic engine does **not** turn an infrastructure failure
into an invented AI coding weakness.

## 2. Observed facts

- No model responses were recorded; the run timed out.
- **No trajectory artifact** was produced
  (`agent/mini-swe-agent.trajectory.json` absent).
- The submitted `model.patch` (~151 KB) contains **Redis persistence artifacts**
  (`appendonlydir/appendonly.aof.*`, `dump.rdb`), not source edits.
- V3.1 classified the run INVALID.

## 3. Engine output

The engine emits exactly one finding, `NodeBB:infra`:

- **Category:** `agent_startup_failure` | **Severity:** blocker | **Kind:** observed.
- **Symptom:** "Agent execution did not validly complete; no authoritative
  evaluation of coding ability is possible."
- **Limitations:** the absence of valid execution is the failure; no trajectory
  was produced; the patch is runtime/database artifacts, not source edits.
- **Competing explanations (platform-side):** model API unavailable; harness
  startup error; environment/network failure.

Capability observations: **none**. Recommendations: **none** (infrastructure is a
platform issue, not an agent-capability finding).

## 4. What the engine refuses to say

The generated report contains none of, and cannot contain, assertions such as:

- "DeepSeek failed to understand NodeBB."
- "DeepSeek wrote incorrect JavaScript."
- "DeepSeek has weak Redis knowledge."
- "DeepSeek cannot fix caching problems."

Enforced by `test_nodebb_original_is_infrastructure_only`, which renders the report
and asserts forbidden phrases are absent, and asserts every finding's category is
`agent_startup_failure`.

## 5. Recovered attempt

The separately recovered run (`jobs/nodebb-recovery`, VALID) is a **different**
attempt and is diagnosed as its own session; it does not retroactively validate
the original.

## 6. Reproduce

```bash
python -m pytest dataforge_v3/tests/test_intelligence_integration.py -q
python -m dataforge_v3.cli intelligence --root . --out-dir findings/intelligence
```
