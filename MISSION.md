# AXE Self-Improvement Mission Briefing

> **FOR AI AGENTS WORKING ON AXE**
> 
> This document is your mission briefing for improving AXE (Agent eXecution Engine).
> Read it carefully before starting any work. It contains critical context, architecture
> knowledge, and improvement opportunities.

---

## 🎯 What is AXE?

AXE is a **terminal-based multiagent coding assistant** that orchestrates multiple AI models
(Claude, GPT, Llama, Grok, DeepSeek, Qwen) to collaboratively solve programming tasks.

**Core Purpose:**
- Enable humans to work with multiple AI agents through a unified terminal interface
- Support collaborative sessions where agents work together autonomously
- Specialize in C, C++, Python development and reverse engineering
- Provide safe, sandboxed tool execution (compilers, debuggers, disassemblers)

---

## 📁 Architecture Overview

```
AXE/
├── axe.py              # Main entry point (3000+ lines) - Core engine
├── axe.yaml            # Configuration: providers, agents, tools, directories
│
├── core/               # Core multiprocessing utilities
│   └── multiprocess.py
│
├── database/           # SQLite persistence layer
│   ├── agent_db.py     # AgentDatabase class - state, XP, sleep, breaks
│   └── schema.py       # Database schema definitions
│
├── models/             # Model metadata and capabilities
│   └── metadata.py     # Context windows, input/output modes per model
│
├── progression/        # Agent leveling system
│   ├── levels.py       # Level thresholds and titles
│   └── xp_system.py    # XP calculation formulas
│
├── safety/             # Safety constraints
│   └── rules.py        # SESSION_RULES displayed to agents
│
├── utils/              # Utility modules
│   ├── formatting.py   # Colors, terminal output helpers
│   ├── xml_tool_parser.py  # XML function call parsing
│   └── token_tracker.py    # Token usage tracking
│
└── llm_prep/           # Context files for LLM sessions
    ├── codebase_overview.md
    ├── project_guidance.md
    └── tags             # ctags index for symbol navigation
```

---

## 🔑 Key Classes in axe.py

| Class | Purpose |
|-------|---------|
| `Config` | YAML/JSON configuration management |
| `AgentManager` | API client initialization, agent resolution, API calls |
| `ToolRunner` | Safe command execution with whitelist/blacklist |
| `ResponseProcessor` | Parse agent responses, execute READ/EXEC/WRITE blocks |
| `ProjectContext` | Gather project files, git status, context for agents |
| `SharedWorkspace` | Shared filesystem for multi-agent collaboration |
| `CollaborativeSession` | Main orchestration loop for agent collaboration |
| `ChatSession` | Interactive single-user chat mode |
| `SleepManager` | Mandatory rest system for agents (Phase 6) |
| `BreakSystem` | Coffee/play break requests and approval (Phase 9) |
| `DynamicSpawner` | On-demand agent spawning (Phase 10) |
| `EmergencyMailbox` | Encrypted whistleblower channel (Phase 8) |

---

## 🔧 Agent Communication Tokens

Agents use unique tokens to communicate state changes. **These are critical** - false
detection of these tokens caused major bugs (see PR #9).

```python
AGENT_TOKEN_PASS = "[[AGENT_PASS_TURN]]"
AGENT_TOKEN_TASK_COMPLETE = "[[AGENT_TASK_COMPLETE:"  # Ends with ]]
AGENT_TOKEN_BREAK_REQUEST = "[[AGENT_BREAK_REQUEST:"  # Ends with ]]
AGENT_TOKEN_EMERGENCY = "[[AGENT_EMERGENCY:"         # Ends with ]]
AGENT_TOKEN_SPAWN = "[[AGENT_SPAWN:"                 # Ends with ]]
AGENT_TOKEN_STATUS = "[[AGENT_STATUS]]"
```

**⚠️ IMPORTANT:** Never use these tokens in documentation, file content, or examples
without escaping them, or AXE may terminate sessions prematurely!

---

## 📋 Recent Changes (PR #9)

The most recent PR fixed critical bugs:

1. **False TASK COMPLETE detection** - AXE would terminate sessions when agents read files
   containing "TASK COMPLETE" in their content. Fixed with `is_genuine_task_completion()`.

2. **Unique token system** - Replaced plain-text commands with unique tokens like
   `[[AGENT_PASS_TURN]]` to prevent false positives from file content.

3. **Database file removed from git** - `axe_agents.db` should never be committed.

---

## 🚀 Improvement Opportunities

### High Priority

1. **Plugin System**
   - Allow third-party tools and agents without modifying core
   - Design a `plugins/` directory with auto-discovery
   - Interface: `class AXEPlugin` with `on_load()`, `on_message()`, `on_shutdown()`

2. **Better Error Recovery**
   - API rate limits should trigger automatic cooldown + retry
   - Network failures should not crash sessions
   - Malformed agent responses should be gracefully handled

3. **Token Usage Dashboard**
   - Track tokens per agent per session
   - Estimate costs across providers
   - Warn when approaching context limits

4. **Streaming Responses**
   - Currently responses are returned all-at-once
   - Implement streaming for better UX during long responses
   - Show typing indicator or partial output

### Medium Priority

5. **Agent Memory System**
   - Persist key facts/decisions across sessions
   - Implement vector store for semantic search of past context
   - Allow agents to "remember" previous collaborations

6. **Task Decomposition**
   - Automatically break large tasks into subtasks
   - Track subtask completion and dependencies
   - Parallel execution where possible

7. **Code Execution Sandbox**
   - Docker/container-based execution for untrusted code
   - Resource limits (CPU, memory, time)
   - Network isolation options

8. **Web UI Option**
   - Alternative to terminal interface
   - Real-time collaboration visualization
   - Better file/diff viewing

### Low Priority (Nice to Have)

9. **Voice Interface**
   - Speech-to-text input
   - Text-to-speech for agent responses

10. **Git Integration Enhancements**
    - Auto-create branches for tasks
    - PR creation from collaborative sessions
    - Diff preview before commits

11. **Test Coverage**
    - Current tests cover key functions but not all edge cases
    - Add integration tests for full collaborative sessions
    - Mock API calls for reliable testing

---

## 🛡️ Safety Considerations

When improving AXE, always consider:

1. **Path Traversal** - Never allow file operations outside project directory
   - `_resolve_project_path()` and `_is_path_safe()` are critical
   - **Known limitation:** Symlink-based escapes not fully hardened (see comments in code)

2. **Command Injection** - All commands go through `ToolRunner.is_tool_allowed()`
   - Whitelist is in `axe.yaml` under `tools:`
   - `shlex.split()` used to prevent shell injection

3. **API Key Security** - Keys from environment variables only, never in config files

4. **Agent Boundaries** - Agents should not be able to:
   - Access forbidden directories
   - Execute non-whitelisted commands
   - Spawn unlimited agents (MAX_TOTAL_AGENTS = 10)
   - Work without rest (MAX_WORK_HOURS = 6)

---

## 🧪 Testing Your Changes

```bash
# Run all tests
pytest test_*.py -v

# Test specific functionality
pytest test_task_completion_detection.py -v  # Token detection
pytest test_write_blocks.py -v                # File operations
pytest test_xml_tool_parser.py -v             # XML function calls

# Manual testing
python axe.py --init                          # Generate config
python axe.py -c "@llama hello"               # Single command
python axe.py --collab llama,copilot --workspace ./test --time 5 --task "Test task"
```

---

## 📝 Code Style Guidelines

1. **Python Style**
   - Follow PEP 8
   - Type hints for all public functions
   - Docstrings for classes and non-trivial functions

2. **Comments**
   - Explain *why*, not *what*
   - Mark security-sensitive code with `# SECURITY:`
   - Mark TODOs with `# TODO:` and owner if known

3. **Error Handling**
   - Never fail silently - at least log to stderr
   - Graceful degradation over crashes
   - Specific exceptions over generic `except Exception`

4. **Commit Messages**
   - Format: `type: short description`
   - Types: `fix`, `feat`, `refactor`, `docs`, `test`, `chore`
   - Example: `fix: prevent false TASK COMPLETE detection from file content`

---

## 🤝 Collaboration Protocol

When working with other agents on AXE improvements:

1. **Claim Your Work**
   - Announce what you're working on at start of turn
   - Example: "I'll focus on implementing the plugin system"

2. **Share Progress**
   - Update shared notes with findings
   - Leave TODO comments for things you didn't finish

3. **Review Each Other**
   - If you see code from another agent, review it
   - Suggest improvements respectfully

4. **Ask Questions**
   - Use: "Hey @teammate, what do you think about X?"
   - Don't assume - clarify with @boss or human

5. **Declare Completion Properly**
   - Only use `[[AGENT_TASK_COMPLETE: summary ]]` when truly done
   - Include summary of what was accomplished
   - List any remaining work

---

## 🚫 What NOT to Do

1. **Never commit:**
   - `axe_agents.db` or any `.db` files
   - API keys or secrets
   - Large binary files

2. **Never assume:**
   - File paths are safe without checking
   - Commands are allowed without whitelist check
   - Agent responses are well-formed

3. **Never break:**
   - Backward compatibility without deprecation warnings
   - Existing tests
   - The collaborative session loop

---

## 📚 Key Files to Understand

Before making changes, read these files carefully:

1. `axe.py` lines 1-300 - Imports, constants, token definitions
2. `axe.py` lines 1230-1450 - `ResponseProcessor` class (READ/EXEC/WRITE)
3. `axe.py` lines 1680-1870 - Token detection functions
4. `axe.py` lines 1875-2650 - `CollaborativeSession` class
5. `safety/rules.py` - Session rules shown to agents
6. `database/agent_db.py` - Persistence layer

---

## ✅ Definition of Done

A task is complete when:

1. ✅ Code works and passes all existing tests
2. ✅ New tests added for new functionality
3. ✅ No regressions in existing features
4. ✅ Documentation updated if needed
5. ✅ Code follows style guidelines
6. ✅ Security implications considered
7. ✅ Ready for PR review

---

## 🆘 Getting Help

- **Code questions:** Ask @boss or refer to inline comments
- **Architecture decisions:** Discuss with team before implementing
- **Security concerns:** Flag immediately with `[[AGENT_EMERGENCY: description ]]`
- **Human intervention:** Use emergency mailbox for critical issues

---

*Last updated: 2026-01-02*
*Version: 1.0*
*Maintainer: EdgeOfAssembly*
