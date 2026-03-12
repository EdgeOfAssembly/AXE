# SRI (Self-Recursive Improvement) — Future Work

*Discussion document produced during AXE test-environment setup (PR: setup-fast-reproducible-test-env).*

---

## What Is SRI in the AXE Context?

Self-Recursive Improvement (SRI) means that AXE's Ollama agents can:

1. Read and reason about AXE's own source code.
2. Propose concrete, testable improvements.
3. Write changes to AXE source files.
4. Re-launch AXE with the updated code and a restored prior session.
5. Verify that the improvement works, then iterate.

Full SRI would create a closed feedback loop: agents improve the tool they run
inside, and that tool then runs the improved agents.

---

## What Exists Today

### Session Saving and Loading — `/session` commands

AXE implements a `/session` command set in interactive mode:

```
/session save <name>   Save current session to disk
/session load <name>   Load a previously saved session
/session list          List all saved sessions
```

**What is saved:**  The session database records agent state (XP, level, alias,
memory, diffs, error count), plus a Markdown log of the collaboration
(`.collab_log.md` written to the workspace directory).

**What is NOT saved (as of this writing):**  The full in-memory message history
passed to each LLM — only the on-disk `.collab_log.md` exists.  When a session
is loaded, agents start a fresh context window; they read the log to catch up,
but do not have token-by-token replay of the prior conversation.

### Session History and Selection

* AXE stores sessions by name (`/session save my-session`).
* `/session list` shows all saved sessions in the database.
* A user **can** choose which session to load by name.
* There is **no automatic session saving** — the user or an agent must explicitly
  call `/session save <name>`.  If AXE crashes or is killed, the in-memory
  state is lost.

### Can an Agent Trigger a Session Save?

Yes — any agent can emit a `/session save` EXEC block and AXE's tool-runner
will execute it, provided it is not blacklisted.  This is the foundation needed
for SRI: an agent can save state, then ask the supervisor to restart AXE.

### Restarting AXE With Updated Code

AXE does not yet have a built-in "restart with updated code" primitive.  An
agent can write files to disk (WRITE block), but it cannot instruct AXE to
`exec` a new process that replaces the current one.  A human operator (or a
CI script) must restart AXE after agents have written code changes.

---

## What Is Missing for Full SRI

| Capability | Status | Notes |
|---|---|---|
| Session save / load | ✅ Implemented | `/session save <name>` / `/session load <name>` |
| Session list / choose | ✅ Implemented | `/session list` |
| Automatic session save (checkpoint) | ❌ Missing | No periodic or on-exit autosave |
| Full conversation-history replay | ❌ Partial | Only log file; no token-level replay |
| Agent-initiated restart of AXE | ❌ Missing | No `restart` primitive |
| Versioned session history (git-like) | ❌ Missing | Sessions overwrite by name |
| Agent self-patching AXE source | 🟡 Partial | Agents can WRITE files; restart is manual |
| Sandboxed test of patched AXE | ❌ Missing | No built-in sandbox for re-running AXE |
| Regression test runner hook | 🟡 Partial | `tests/test_end_to_end.py` exists; no auto-invoke |

---

## Feasibility Assessment

**Short-term feasibility (1–3 PRs):** Medium.

The building blocks are there:
* Agents can read AXE source via `/read` or EXEC blocks.
* Agents can propose and write diffs.
* Session save/load works.
* The test suite (`tests/test_end_to_end.py`) can validate changes.

What blocks full automation is the lack of:
1. **Autosave on exit / crash** — adds safety; agents do not lose state.
2. **AXE restart primitive** — lets an agent say "restart with this session."
3. **Versioned session snapshots** — lets agents roll back a bad patch.

**Long-term feasibility:** High, once the above three primitives exist.

---

## Proposed Additions for SRI

### 1. Automatic Session Checkpoint

Add a flag `--autosave-interval N` (minutes).  On each checkpoint:

```python
self.db.save_session(name=f"autosave-{datetime.now().isoformat()}")
```

Also save on clean exit (SIGTERM handler).

### 2. Versioned Session Store

Replace flat-name sessions with a git-style store:

```
.axe/sessions/
  <timestamp>-<name>/
    state.json        # agent XP, level, aliases
    history.jsonl     # full message log (token-level)
    meta.yaml         # AXE version, models, workspace
```

`/session list` would show all snapshots; `/session load` accepts a timestamp
prefix or a name tag.

### 3. `restart` Slash Command / Primitive

```
/restart [--load <session>]
```

AXE would:
1. Save current session to a timestamped checkpoint.
2. `exec` a fresh `axe.py` process with `--collab ... --load <session>`.
3. The old process exits cleanly.

This is the key primitive that closes the SRI loop.

### 4. Agent-Driven SRI Workflow (Proposed)

```
Supervisor: "Read axe.py and propose one improvement."
Agent A:    "I'll improve token optimization in _compress_history."
            [writes diff to /tmp/patch.diff]
Supervisor: "Apply it, save session, restart AXE, run tests."
            [EXEC: git apply /tmp/patch.diff]
            [/session save pre-restart]
            [/restart --load pre-restart]
            # new AXE process loads session, runs tests
            [EXEC: python3 tests/test_end_to_end.py]
Supervisor: "Tests passed. Tag this session as stable."
            [/session save stable-v2]
```

---

## The "Office" Vision and SRI

AXE is designed as an "office" environment: a supervisor agent manages a team,
assigns tasks, rewards performance, and ensures well-being.  SRI fits naturally:

* The supervisor can delegate "improve AXE" as a long-running project.
* Agents earn XP for accepted patches (already in the XP system).
* Agents can specialize: one focuses on token optimization, another on security,
  another on RE workflow improvements.
* Session persistence lets the team pick up exactly where they left off.

The missing autosave and restart primitives are the only hard blockers.  Once
those exist, SRI is achievable with minimal additional scaffolding.

---

## Recommended Next Steps

1. **PR: autosave-on-exit** — Save a checkpoint whenever AXE exits cleanly.
2. **PR: versioned session store** — Replace flat-name sessions with timestamped
   snapshots and a `--load-latest` flag.
3. **PR: `/restart` primitive** — Let agents trigger a controlled AXE restart.
4. **PR: agent-initiated test run** — Hook `tests/test_end_to_end.py` so an agent
   can invoke it and get a pass/fail result back as a tool output.
5. **PR: SRI demo** — Wire the above into a demo where agents improve
   `core/token_manager.py` and validate the change end-to-end.

---

*This document is a starting point.  It should be updated as SRI capabilities
are implemented.*
