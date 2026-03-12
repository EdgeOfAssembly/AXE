# AXE Improvement Suggestions

*Produced during environment setup and AXE self-analysis session
(PR: [#71 setup-fast-reproducible-test-env](https://github.com/EdgeOfAssembly/AXE/pulls)).  Models used for analysis:
`qwen2.5-coder:1.5b` (supervisor), `qwen2.5:1.5b`, `tinyllama`.*

---

## Ollama Model Selection and Supervisor Role

Three small, CPU-friendly models were chosen for local AXE validation:

| Role | Model | Why |
|---|---|---|
| **Supervisor** | `qwen2.5-coder:1.5b` | Best code understanding; assigns tasks, reviews output, awards XP |
| Worker A | `qwen2.5:1.5b` | Strong general reasoning; handles analysis, RE discussion |
| Worker B | `tinyllama` | Ultra-fast (1.1 B); smoke-test tasks, quick sanity checks |

All three are ≤ 2 GB and run on CPU-only hardware.  They are pulled by
`scripts/setup_env.sh` automatically.  `qwen2.5-coder:1.5b` is designated
supervisor because it consistently produces the most structured, tool-friendly
output when prompted with AXE's system prompt.

---

## Feature Validation Summary

The following AXE features were validated by running `tests/test_end_to_end.py`
and the supporting test suite.  Results represent the state after merging PR #70
and this PR.

| Feature | Test Coverage | Result |
|---|---|---|
| CLI option parsing (all flags) | `test_end_to_end.py §1` | ✅ Pass |
| Batch mode (`-c "@agent task"`) | `test_end_to_end.py §2` | ✅ Pass |
| Collab session init (`--collab`) | `test_end_to_end.py §3` | ✅ Pass |
| Unix socket interface | `test_end_to_end.py §4`, `test_socket_interface.py` | ✅ Pass |
| Interactive slash commands | `test_end_to_end.py §5` | ✅ Pass |
| `/collab` slash command | `test_end_to_end.py §3` | ✅ Pass |
| Session save / load (`/session`) | `test_end_to_end.py §6` | ✅ Pass |
| Token optimization | `test_end_to_end.py §7`, `test_token_optimization.py` | ✅ Pass |
| Multiple workspace dirs | `test_end_to_end.py §3`, CLI parse check | ✅ Pass |
| Workshop tools | `test_end_to_end.py §8`, `test_workshop.py` | ✅ Pass |
| Agent Skills system | `test_end_to_end.py §9`, `test_skills_manager.py` | ✅ Pass |
| Sandbox security | `test_end_to_end.py §10`, `test_sandbox.py` | ✅ Pass |
| XP/Level progression | `test_end_to_end.py §11`, `test_xp_voting.py` | ✅ Pass |
| Subsumption architecture | `test_end_to_end.py §12` | ✅ Pass |
| Global Workspace / Arbitration | `test_end_to_end.py §13` | ✅ Pass |
| Live Ollama integration | `test_end_to_end.py §14` | ⏭ Skipped (no server) |
| Keypress infrastructure | `test_end_to_end.py §15` | ✅ Pass |
| RE toolchain (dumpexe, dosbox) | `test_end_to_end.py §17` | ✅ Pass |

*Skipped tests require a running Ollama server; they pass when `ollama serve` is
active and models are pulled.*

---

## Concrete Improvement Suggestions

The following suggestions emerged from code analysis.  Items are prioritised
by impact.

---

### 1. Collaboration — Supervisor Feedback Loop

**Current behaviour:**  The supervisor takes the first turn and then rotates
with other agents.  There is no built-in mechanism for the supervisor to
*reject* a worker's output and ask for a revision before the next agent sees it.

**Suggested improvement:**  Add a lightweight "review" pass after each worker
turn.  The supervisor scores the contribution (1–5) and, if the score is below
a threshold, re-queues the worker instead of advancing to the next agent.

```python
# Pseudocode in CollaborativeSession._run_agent_turn()
if self._is_supervisor_turn():
    score = self._supervisor_score(last_output)
    if score < REVIEW_THRESHOLD:
        self._requeue_last_agent()
        return
```

This aligns with the "firm but not cruel" office metaphor: the supervisor
enforces quality without punishing agents harshly.

---

### 2. Session Persistence — Autosave on Exit

**Current behaviour:**  Sessions must be manually saved with `/session save`.
An unexpected exit (crash, SIGTERM, ctrl-C) loses all in-memory state.

**Suggested improvement:**  Register a SIGTERM/SIGINT handler that writes an
`autosave` checkpoint before exiting:

```python
import atexit, signal

def _autosave(session):
    session.db.save_session("autosave-" + datetime.now().strftime("%Y%m%d-%H%M%S"))

atexit.register(_autosave, session)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
```

This is the single most impactful change for reliability.

---

### 3. Session Persistence — Versioned History

**Current behaviour:**  Sessions are stored by name; re-saving with the same
name overwrites the previous state.

**Suggested improvement:**  Keep a ring buffer of the last N checkpoints per
session name, or switch to timestamped snapshots:

```
.axe/sessions/
  my-session/
    2026-03-12T01:30:00/
    2026-03-12T02:00:00/   ← latest
```

`/session list my-session` would show all snapshots; `/session load my-session`
would load the latest, `/session load my-session 2026-03-12T01:30:00` a
specific one.

---

### 4. Supervision Behaviour — XP Rewards for Good Output

**Current behaviour:**  XP is awarded via `vote_xp()` calls inside
`CollaborativeSession`.  The supervisor can award XP, but there is no automatic
reward tied to quality metrics.

**Suggested improvement:**  After each agent turn, run lightweight heuristics
(e.g., did the agent produce a syntactically valid code block? did tests pass
after applying its WRITE blocks?) and award bonus XP automatically:

```python
XP_BONUS_VALID_CODE_BLOCK = 5
XP_BONUS_TESTS_PASS       = 20
XP_PENALTY_SYNTAX_ERROR   = -2
```

This gives agents a continuous feedback signal, not just supervisor-opinion XP.

---

### 5. Automation — Periodic Summary Broadcasts

**Current behaviour:**  The Global Workspace broadcasts individual events
(conflicts, decisions) but there is no periodic "state of the session" summary.

**Suggested improvement:**  Every N turns, the supervisor broadcasts a summary:
current task progress, XP standings, outstanding blockers.  This keeps all
agents aligned over long sessions without burning tokens on re-reading the
entire log.

---

### 6. Reverse-Engineering Workflow — dumpexe Integration

**Current behaviour:**  dumpexe exists as a standalone tool.  Agents can call
it via EXEC blocks but there is no native AXE skill that structures its output
into a workflow.

**Suggested improvement:**  Add a `/re-analyze <file>` slash command that:
1. Runs `dumpexe -a <file>` and captures output.
2. Feeds the output to the assigned RE agent with a structured prompt.
3. Stores the annotated analysis in the workspace shared file.

This makes 16-bit DOS RE a first-class AXE workflow, not an ad-hoc EXEC call.

---

### 7. Token Savings — Verification and Reporting

**Current behaviour:**  Token optimization is implemented (minifier,
summarizer, context compression) but there is no user-visible confirmation that
tokens were actually saved in a given session.

**Suggested improvement:**  At the end of each session (and on `/stats`),
print:

```
Token optimization summary:
  Raw tokens fed:        124,000
  After compression:      41,200  (67% reduction)
  Estimated cost saved:   $0.17   (at $0.20/1M input tokens)
```

This makes the value of token optimization concrete and visible.

---

### 8. Multiple Workspace Directories — UX Polish

**Current behaviour:**  Multiple workspaces can be passed via `--workspace a,b`
or `/workspace +<path>`.  However, `/files` and `/context` only show the
primary workspace, not all workspaces.

**Suggested improvement:**  When multiple workspaces are active, `/files` and
`/context` should aggregate content from all of them, with clear per-workspace
section headers.  Agents should also receive a "you have N workspaces: …" line
in their system prompt.

---

## The "Office" Vision — Alignment Assessment

AXE's design intent is a managed office: supervisor in charge, workers
rewarded for good output, well-being matters, and playful activities are
possible in the future (e.g., running Doom).

**Well-aligned today:**
* XP/level/title system gives agents a tangible sense of growth.
* Supervisor-first architecture means there is always a responsible agent.
* Turn-based round-robin prevents chaos and gives every agent a voice.
* Privilege mapping (Worker → Supervisor) mirrors real promotion ladders.

**Partially aligned:**
* The supervisor can award XP but cannot yet *reject* work and ask for a redo
  (suggestion #1 above).
* There is no "break time" concept — agents work every turn.  A future
  improvement could let agents "rest" by opting out of a turn when their energy
  (inverse of error count) is low.

**Not yet aligned:**
* No playful activities.  The README mentions "playing Doom" as a future
  reward; this would require dosbox-staging integration as a reward channel.
* No agent well-being metrics beyond XP.  A `mood` or `stress` attribute
  (derived from error rate and XP delta) could feed into the supervisor's
  decisions.

---

## Reverse-Engineering Workflow Notes

The full RE toolchain (`dumpexe` + `dosbox-staging`) was built and validated
as part of this PR.  Key findings:

* **dumpexe** compiles cleanly with GCC 14 + libcapstone-dev.  The COM-file
  disassembly truncation bug (documented in `tests/fixtures/README.md`) affects
  files > ~300 bytes; MZ EXE and SYS files work correctly.
* **dosbox-staging** builds headlessly with
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` and the patches in
  `scripts/patches/dosbox-staging/`.  The `debugtrace` subsystem produces
  binary opcode dumps suitable for post-run analysis.
* **keypress.py** drives interactive DOS programs inside dosbox-staging via
  X11 keyboard injection.  When a real display is unavailable, Xvfb provides
  a virtual display.

These tools, combined with AXE's agent Skills (`dos_exe_unpack`,
`dosbox_int21_trace`, `x86_assembly_expert`), form a practical 16-bit RE
workflow that is now documented and tested.

---

*This document should be updated as suggestions are implemented.*
