# AXE Live Feature Test Results

*Last updated: 2026-03-12*

This document captures the results of every AXE feature test run against three
small Ollama models in a CPU-only sandbox environment.

## Test Environment

| Component | Version / Notes |
|-----------|----------------|
| Ollama | 0.17.7 |
| Python | 3.12 |
| Host | Ubuntu (GitHub-hosted runner, CPU-only, no GPU) |
| Supervisor model | `qwen2.5-coder:1.5b` (~986 MB) |
| Worker A model | `qwen2.5:1.5b` (~986 MB) |
| Worker B model | `tinyllama:latest` (~637 MB) |

---

## How to re-run

```bash
# Full setup + validation (installs Ollama and pulls models if needed)
bash tests/run_feature_validation.sh

# Skip Ollama install (assume already done)
bash tests/run_feature_validation.sh --skip-setup

# Structural tests only (no Ollama needed)
bash tests/run_feature_validation.sh --skip-live

# Individual test files
python3 tests/test_end_to_end.py           # Structural / unit suite
python3 tests/test_live_feature_matrix.py  # Live Ollama feature suite
```

---

## Section 1 – Batch Mode (`-c "@agent task"`)

| Test | Result | Notes |
|------|--------|-------|
| `qwen25coder` responds to simple prompt | ✅ PASS | Model responds with content |
| `tinyllama` responds to simple prompt | ✅ PASS | Ultra-fast on CPU |
| `--dry-run` flag accepted | ✅ PASS | No crash, exits cleanly |
| `--workspace a,b` (two dirs) | ✅ PASS | Both dirs passed to agent |

**Key finding**: Batch mode works reliably with all three models. The `--workspace`
comma-separator allows true multi-repo analysis in a single invocation.

---

## Section 2 – Collaborative Session (`--collab`)

| Test | Result | Notes |
|------|--------|-------|
| `qwen25coder + tinyllama` collab task | ✅ PASS | Both agents take turns |
| Workspace files accessible to agents | ✅ PASS | READ blocks work |

**Key finding**: The `--collab` mode orchestrates multiple agents on shared workspace
files. With CPU-only models, each turn takes ~30–60 s. A `--time 1` (1-minute) session
is enough for 2–3 turns per agent.

---

## Section 3 – Session Save / Load

| Test | Result | Notes |
|------|--------|-------|
| `save_session()` writes JSON file | ✅ PASS | |
| `load_session()` restores data | ✅ PASS | |
| `list_sessions()` returns all | ✅ PASS | |
| save→load round-trip (all fields) | ✅ PASS | conversation, agents, workspace |
| load of non-existent name → None | ✅ PASS | |
| `/session save + load` interactive | ✅ PASS | |

**Key finding**: Session persistence works end-to-end. Sessions are stored as JSON in
`.axe_sessions/`. The `/session save <name>` and `/session load <name>` slash commands
are functional.

**SRI relevance**: The session system is the foundation for Self-Recursive Improvement
(SRI). An agent can save its state, improve AXE's source, and reload the session after
restart to continue from where it left off.

---

## Section 4 – Token Optimization / Savings

| Test | Result | Notes |
|------|--------|-------|
| `TokenStats` input/output tracking | ✅ PASS | Per-agent stats correct |
| Per-agent stats accumulated | ✅ PASS | |
| `Minifier` compresses Python source | ✅ PASS | 63 → 21 bytes (67% reduction) |
| `PromptCompressor` importable | ✅ PASS | |
| Token stats populated after live call | ✅ PASS | input + output tracked |

**Key finding**: Token savings are real. The minifier reduces source code by ~60–70%
before sending to models. The `PromptCompressor` handles conversation history
compression. `/stats` and `/tokenopt-stats` show live usage.

---

## Section 5 – Multiple Workspace Directories

| Test | Result | Notes |
|------|--------|-------|
| `--workspace a,b` comma-split (source) | ✅ PASS | `axe.py` splits correctly |
| `SharedWorkspace` creates note file | ✅ PASS | `.collab_shared.md` created |
| `ToolRunner` accepts multiple paths | ✅ PASS | `workspace_paths` list set |
| Live batch with two workspaces | ✅ PASS | Agent accesses both dirs |
| `/workspace +path` in interactive mode | ✅ PASS | Path added at runtime |

**Key finding**: Multi-workspace support works both at CLI level (`--workspace`) and
at runtime (`/workspace +path`). This is essential for cross-project analysis tasks.

---

## Section 6 – Unix Socket Interface

| Test | Result | Notes |
|------|--------|-------|
| `SOCKET_PATH` construction correct | ✅ PASS | `/run/user/<uid>/axe.sock` |
| `axe_socket_client.py` importable | ✅ PASS | |
| Socket server starts in interactive mode | ✅ PASS | File appears within 15 s |
| `/help` via socket returns text | ✅ PASS | Full command listing returned |

**Key finding**: AXE's bi-directional Unix socket interface works correctly. External
processes (other agents, scripts, CI jobs) can send slash commands and receive
formatted output via the socket. The socket polls between `input()` calls; feeding
blank lines keeps the REPL loop spinning for socket tests.

---

## Section 7 – Interactive Slash Commands

| Test | Result | Notes |
|------|--------|-------|
| `/help` mentions `/agents` | ✅ PASS | |
| `/agents` lists agents | ✅ PASS | |
| `/tools` shows tool config | ✅ PASS | |
| `/workspace` shows paths | ✅ PASS | |
| `/stats` shows token usage | ✅ PASS | |
| `/config` shows configuration | ✅ PASS | |
| `/collab` syntax in `/help` | ✅ PASS | |
| `/session list` works | ✅ PASS | |

**Key finding**: All core slash commands work in interactive mode. `/collab` syntax
is documented. The REPL handles EOF cleanly.

---

## Section 8 – `/collab` Inside Interactive Mode

| Test | Result | Notes |
|------|--------|-------|
| `/collab` launches session | ✅ PASS | Agents respond in-session |

**Key finding**: `/collab` works as a slash command inside an existing interactive
session — no need to restart AXE to start a collaboration.

---

## Section 9 – AXE Self-Analysis (workspace = AXE source)

| Test | Result | Notes |
|------|--------|-------|
| Supervisor reads `session_manager.py` | ✅ PASS | Real improvement suggestion |
| Worker reviews C source | ✅ PASS | Identifies unused headers |
| Three-agent collab on AXE source | ✅ PASS | Agents discuss SRI improvements |

**Sample supervisor suggestion**:
> *"Consider adding error handling when saving session data to ensure data integrity
> and provide a meaningful message in case of a failure."*

**Sample worker suggestion** (on `hello_world.c`):
> *"The `#include <string.h>` and `#include <stdlib.h>` headers are not used in the
> provided code, so they can be removed."*

---

## Section 10 – SRI Groundwork Discussion

| Test | Result | Notes |
|------|--------|-------|
| Supervisor discusses SRI feasibility | ✅ PASS | Substantive response |
| `SRI_FUTURE_WORK.md` covers key topics | ✅ PASS | autosave, restart, session |
| `AXE_IMPROVEMENT_SUGGESTIONS.md` complete | ✅ PASS | supervisor, token, session |

**Live SRI discussion** (model: `qwen2.5-coder:1.5b`):

> *"Despite significant advancements in programming and machine learning, there remains
> a significant technical gap preventing full Self-Recursive Improvement (SRI) in AXE.
> To address this gap, the '/restart --load \<session\>' primitive is proposed. Specifically,
> this primitive should save and restore the session after each restart, ensuring
> consistency and reliability. Autosave-on-exit, while helpful, is not sufficient for
> making SRI loops reliable, as it does not prevent the state machines that make up AXE
> from getting out of sync over time."*

See [`docs/SRI_AGENT_DISCUSSION.md`](SRI_AGENT_DISCUSSION.md) for the full discussion.

---

## Section 11 – XP / Level / Title Progression

| Test | Result | Notes |
|------|--------|-------|
| `vote_xp()` records a vote | ✅ PASS | |
| `calculate_xp_for_level` returns int | ✅ PASS | Level 40 → 3181 XP |

---

## Section 12 – Workshop Tools

| Test | Result | Notes |
|------|--------|-------|
| chisel, hammer, saw, plane importable | ✅ PASS | |
| `/workshop status` in interactive mode | ✅ PASS | |

---

## Overall Results

```
Total: 45 | Passed: 45 | Skipped: 0 | Failed: 0
```

All 45 live feature tests pass against three real Ollama models on CPU.

---

## Known Limitations

1. **CPU-only execution**: Models run ~10–30× slower than GPU. Collab sessions use
   1-minute time limits (`--time 1`) to keep CI fast.

2. **No autosave-on-exit**: AXE does not yet automatically save sessions on exit.
   This is the primary gap identified for SRI support. See `SRI_FUTURE_WORK.md`.

3. **Socket polling**: AXE's socket server is polled between REPL `input()` calls.
   In automated tests, blank lines must be fed to stdin to keep the loop spinning.

4. **No `/restart --load`**: A `/restart --load <session>` primitive does not yet
   exist. This is the second-most critical gap for SRI. See `SRI_FUTURE_WORK.md`.

---

## Future Work

See [`docs/SRI_FUTURE_WORK.md`](SRI_FUTURE_WORK.md) for the full SRI roadmap.
See [`docs/AXE_IMPROVEMENT_SUGGESTIONS.md`](AXE_IMPROVEMENT_SUGGESTIONS.md) for
agent-generated improvement suggestions.
