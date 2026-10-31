# Environment Reliability — DataForge V3.1 Phase 1A

## Host (audit machine)
- Windows 11 + WSL2 Ubuntu 26.04; 8 logical cores; 7.6 GB RAM; Docker 29.1.3 (overlayfs).
- Harbor 0.25.0 (uv tool). Local Docker backend (README's Modal unavailable — no Modal creds).
- Network to PyPI: 12–23 s per HTTPS request (severely degraded, persistent during the audit).

## Environment failures observed and how they were handled

| # | Failure | Evidence | Handling (harness only) |
|---|---|---|---|
| E1 | CRLF working tree from Windows checkout → `#!/bin/bash\r` scripts unrunnable | `file tests/test.sh` = "with CRLF"; `bash: /tests/test.sh: cannot execute` | LF mirror of same commit |
| E2 | Agent setup `uv tool install` times out (default 360 s) | `AgentSetupTimeoutError`; `Failed to download ... UV_HTTP_TIMEOUT` | pre-baked agent images; `--agent-setup-timeout-multiplier 6`; UV/PIP timeouts 1800 |
| E3 | mini-swe-agent 2.4.6 setup wizard aborts on non-TTY | `To get started... Aborted.` | `MSWEA_CONFIGURED=true` |
| E4 | mini-swe-agent 2.4.6 cost-calc crash | `RuntimeError: This model isn't mapped yet` | `MSWEA_COST_TRACKING=ignore_errors` |
| E5 | litellm import needs `mcp` | `ModuleNotFoundError: No module named 'mcp'` | `uv tool install ... --with mcp` (overlay) |
| E6 | Egress sidecar stalls first model call ~892 s | sidecar log `duration:891823869964`; transcript frozen at 8.3 KB | `stream:false`, `timeout:120`, `num_retries:3` |
| E7 | ansible image ships no curl | `/bin/sh: curl: not found` during build | install curl via apt in derived image |
| E8 | Harbor reports 0 tokens/cost for DeepInfra | `agent_result` zeros on success | cost estimated from trajectories |

## Does the environment cause incorrect verdicts?
- In the nodebb original, **yes** (E6 produced a 0.0 for a never-run agent). This is why the
  verdict is classified INFRASTRUCTURE FAILURE and not AGENT FAILURE.
- For the other 6 tasks, the mitigations held and the verifier graded genuine evidence.

## Reproducibility
- Controls reproduced: oracle 1.0 / no-op 0.0 on all 7; flipt oracle 1.0 ×3.
- Regrade reproduced every original verdict (0/7 disagreements).
