# SRI Agent Discussion — Live Session Output

*This document is regenerated automatically by `tests/test_live_feature_matrix.py` §10
when run with `AXE_WRITE_LIVE_DOCS=1` and Ollama available.
The content below was produced by `qwen2.5-coder:1.5b` acting as supervisor.*

---

## Question posed to supervisor

> AXE is a multi-agent coding framework.
> Consider Self-Recursive Improvement (SRI): agents improve AXE's own code,
> save their session, restart AXE, and continue improving.
>
> 1. The single biggest technical gap blocking full SRI in AXE today?
> 2. What would a minimal "/restart --load \<session\>" need to do?
> 3. Is autosave-on-exit enough to make SRI loops reliable?

## Supervisor response (qwen2.5-coder:1.5b)

1. **The single biggest technical gap** blocking full SRI in AXE today is the lack of a
   robust way to save and load session data effectively. This includes ensuring that all
   necessary settings, modifications, and dependencies are persisted across sessions, as
   code that changes frequently requires being recreated.

2. **What a minimal "/restart --load \<session\>" needs to do:**
   - **Save the current session** — all changes to code, config files, and settings
     tailored to the specific experiment running.
   - **Reload the session** — restart execution of the code, apply changes, and ensure
     all relevant dependencies are properly set up. This is crucial for maintaining the
     consistency and reliability of SRI loops.

3. **Is autosave-on-exit enough to make SRI loops reliable?**
   Autosave alone is **not sufficient**. Autosave provides immediate feedback during a
   run but does not address session management (saving state after each session) or
   recovery mechanisms (loading a session with `/restart` so an experiment can continue
   from where it left off). A robust automated session-versioning system would eliminate
   manual save/load steps, reducing the risk of error and improving efficiency.

---

## Analysis Summary

| Question | Key Insight |
|----------|-------------|
| Biggest gap | No `/restart --load <session>` primitive; session state not fully persisted |
| What `/restart` needs | Save full state → kill process → reload session on start |
| Autosave sufficient? | No — state machines can drift; explicit sync checkpoints needed |

---

## Implications for AXE Roadmap

1. **Session autosave-on-exit** (`/session autosave enable`) — lowest hanging fruit;
   ensures no work is lost if an agent exits.

2. **`/restart --load <session>`** — launches a new AXE process, loads the named
   session, and resumes the conversation. This is the critical primitive for SRI loops.

3. **Session history browser** — let agents (and humans) choose which prior session to
   resume; enables branching improvement paths.

4. **Incremental code-diff checkpointing** — save a diff of what was changed between
   sessions so agents can understand their own change history.

---

*For the full SRI roadmap, see [SRI_FUTURE_WORK.md](SRI_FUTURE_WORK.md).*
*To regenerate this file from a live session: `AXE_WRITE_LIVE_DOCS=1 python3 tests/test_live_feature_matrix.py`*
