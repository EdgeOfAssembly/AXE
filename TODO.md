# AXE Feature Catalog

This document catalogs all implemented and planned features of the AXE (Agent eXecution Engine) system, organized alphabetically for easy reference.

## Implemented Features (Alphabetical)

### A

- **Agent Communication Tokens**: Special control keywords enable agents to coordinate: pass control, request breaks, report completion, signal emergencies, spawn new agents, vote on XP, flag conflicts, and arbitrate disputes. Token detection includes false-positive filtering to avoid triggering on file content or code blocks.

- **Agent Skills System**: Domain-specific expertise modules loaded from markdown files without prompt bloat. Features a central `manifest.json` registry with keyword-based activation, provider-specific filtering, and 25+ skills including build practices, reverse engineering, C++/C modernization, Python patterns, x86 assembly, and IDA Pro decompiler analysis.

- **Anthropic Claude Integration**: Full support for Claude's advanced features including prompt caching, Files API, extended thinking, token counting, vision capabilities (image analysis), and reasoning effort configuration (Claude 3.7+).

- **Arbitration Protocol**: Minsky's cross-exclusion conflict resolution system with automatic conflict detection, evidence-based arbitration, escalation to higher-level agents, structured binding resolution broadcasts, and comprehensive conflict tracking and history.

### B

- **Blacklist Security Model**: Default-allow approach with explicit blacklist for forbidden commands and paths. Includes shell operator support, heredoc parsing, and execution logging to `axe_exec.log`.

- **Break System**: Agent rest and sleep management with break request handling and recovery mechanisms for long-running collaboration sessions.

- **Bubblewrap Sandbox**: Process isolation via Linux namespaces using bubblewrap (bwrap). Features user namespace support detection with multiple fallback methods, prevents access to sensitive paths, and blocks restricted commands while maintaining filesystem transparency.

### C

- **Cognitive Architecture Integration**: Theory-grounded implementations of multiple cognitive science frameworks:
  - **Global Workspace Theory (Baars 1988)**: Broadcast mechanism for shared agent findings
  - **Society of Mind (Minsky 1986)**: Peer voting for reputation via XP system
  - **Subsumption Architecture (Brooks 1986)**: Layered hierarchical agent control
  - **Nearly-Decomposable Hierarchies (Simon 1969)**: Explicit privilege levels by agent rank

- **Configuration Architecture**: Three-file configuration system with validation and backward compatibility:
  - `models.yaml` - Static model metadata (loaded first)
  - `providers.yaml` - Provider infrastructure (loaded second)
  - `axe.yaml` - User configuration (loaded third)

- **Context Window Optimization**: Sliding window context management with intelligent message truncation, conversation summarization, duplicate content detection, and token budget enforcement.

### D

- **Database Persistence**: SQLite with WAL mode for thread-safety. Tracks agent state, XP and level persistence, supervisor logs, workshop analysis storage, broadcast history, and conflict/arbitration records.

- **Dynamic Agent Spawning**: On-demand agent creation based on workload with resource-based spawning decisions, spawn cooldown (prevents rapid creation), and maximum agent limits enforcement. Supervisors only.

### E

- **Emergency Mailbox**: GPG-encrypted agent-to-human communication for emergency escalation with secure message storage.

- **Environment Probe**: Auto-generates `.collab_env.md` at session start with system info (kernel, distro, toolchain), resource info (CPU, memory, disk), and tool availability detection (gcc, python, gdb, etc.). Zero agent token cost.

### G

- **GitHub Copilot Integration**: Autonomous GitHub operations with human review gates, SSH-based authentication, branch/commit management. Disabled by default (no-op when off).

- **Global Workspace Theory Implementation**: Broadcast mechanism enabling agents to share findings across the entire collaboration. Supports selective attention and integration without central control.

### L

- **LLM Preparation Tool (llmprep)**: Codebase context preparation tool with build system detection and LLM-friendly documentation generation. Reduces token usage via intelligent context extraction.

### M

- **Multi-Agent Collaboration System**: Parallel agent thinking with background processes, shared context between agents (conversation, workspace state, notes), and agent pass-control tokens for sequential collaboration. Turn-based round-robin coordination.

- **Multi-Format Tool Call Parsing**: Supports XML function calls (Anthropic/OpenAI standard), Bash XML tags, shell code blocks, AXE native blocks (READ/WRITE/EXEC), and mixed format support with deduplication.

- **Multi-Workspace Support**: Multiple workspace directories with comma-separated CLI input (`--workspace /tmp/a,/tmp/b`), interactive `/workspace` command for dynamic management, and proper sandbox binding for all paths.

### P

- **Peer XP Voting**: Minsky's Society of Mind voting mechanism with level-dependent vote limits (Workers ±10/-5, Supervisors ±25/-15). Prevents self-voting and spam while building agent reputation.

- **Privilege Mapping & Access Control**: Four-tier privilege system (Worker, Senior, Deputy, Supervisor) with level-based authority restrictions, command validation against agent level, and level milestones (Level 10: Senior, Level 20: Team Leader, Level 30: Deputy, Level 40+: Supervisor).

- **Prompt Compression**: Reduces prompt size while maintaining semantic meaning through context optimization strategies and support for multiple compression algorithms.

- **Provider/Model Agnostic Architecture**: Unified interface for 8+ AI providers (Anthropic, OpenAI, xAI, HuggingFace, GitHub Copilot, Ollama, DeepSeek, Qwen/Dashscope). Configuration-driven provider enabling/disabling with no vendor lock-in.

### R

- **READ/WRITE/EXEC Blocks**: Native AXE tool syntax - READ blocks for reading files, WRITE blocks for creating/modifying files, EXEC blocks for command execution. Includes path validation and security checks.

- **Resource Monitor**: Background resource tracking with disk usage monitoring, memory/CPU collection, periodic snapshots to file, and non-intrusive monitoring.

### S

- **Session Persistence**: Save/load/list conversation sessions with JSON-based storage, session metadata (tokens, duration, agents), and conversation history preservation.

- **Session Preprocessing**: Environment probing, source code minification, LLM context file generation (llmprep), all at zero agent token cost.

- **Session Rules & Constraints**: Configurable safety policies with tool restrictions, directory access controls, and blacklist management.

- **Shared Build Status**: Tracks multi-agent build tasks with status synchronization and build logging/reporting.

- **Source Code Minifier**: C/C++/Python/Assembly minification with comment/docstring removal (configurable), token reduction while preserving compilability, recursive directory processing, and language auto-detection.

- **Subsumption Architecture**: Brooks' layered behavioral control system - lower-level reactive behaviors can suppress/inhibit higher-level deliberative processes. Enables rapid response while maintaining strategic planning.

### T

- **Token Statistics & Tracking**: Token usage counting per message/session, cost estimation for all major providers, model pricing database (100+ models), and token limit tracking with warnings.

- **Tool Execution System**: Unified tool runner with blacklist-based command validation (default-allow), forbidden path checking, shell operator support (pipes, redirects, logical operators), heredoc parsing for inline content, auto-detection of shell vs direct execution, and comprehensive logging.

### U

- **Unix Socket Interface**: Bidirectional communication via Unix domain sockets for low-latency agent-to-AXE communication. Features ANSI color code preservation, PID file tracking for process discovery. Only enabled in interactive mode. Allows agents to interactively connect and control AXE's shell - use agents to command agents inside another program for coding, debugging, or improving AXE itself.

### W

- **Workshop Dynamic Analysis Framework**: Four specialized tools for runtime analysis:
  - **Chisel**: Symbolic execution via angr - program path analysis, constraint extraction, vulnerability identification, code path carving
  - **Hammer**: Live instrumentation via Frida - runtime hooking/monitoring, function call tracing, memory inspection, dynamic behavior analysis
  - **Saw**: Taint analysis - data flow tracking, taint propagation analysis, source/sink identification
  - **Plane**: Source/sink enumeration - identifies data entry/exit points, maps data flow paths

- **Works with ANY Talking Model**: No requirement for "agentic coding" or "tool use" designed models. As long as the model can produce text, it can use AXE's special agent keywords. AXE handles all the heavy-lifting parsing and executing - the model just needs to talk.

### X

- **XP/Level Progression System**: Gamification system with hybrid linear/exponential progression curve. XP awarded for workshop tool usage, collaboration, bug fixes, and peer voting. Level-based rank titles progress from Worker → Senior Worker → Team Leader → Deputy Supervisor → Supervisor. Full agent persistence across sessions.

---

## Planned Features (Alphabetical)

### A

- **Advanced Caching Strategies**: Extended prompt caching for frequently used contexts, intelligent cache invalidation, and cross-session cache persistence.

- **Agent Personality Customization**: Configurable agent personalities with persistent behavioral traits, learning from past interactions, and team dynamics modeling.

- **Automated Test Generation**: AI-driven unit test creation based on code analysis, integration test scaffolding, and coverage optimization.

### B

- **Backup and Recovery**: Automatic session backup with configurable intervals, disaster recovery mechanisms, and session replay capabilities.

- **Batch Processing Mode**: Queue multiple tasks for sequential or parallel execution, scheduled task execution, and batch result aggregation.

### C

- **Code Migration Assistant**: Automated language translation (C to Rust, Python 2 to 3), framework migration support, and API modernization.

- **Continuous Learning**: Agent memory of successful patterns, project-specific knowledge accumulation, and adaptive strategy refinement.

### D

- **Distributed Execution**: Multi-node agent collaboration via network sockets, load balancing across compute resources, and fault-tolerant distributed workflows.

- **Docker Integration**: Containerized execution environments, reproducible build sandboxes, and multi-platform testing support.

### E

- **Enhanced Visualization**: Real-time agent activity dashboards, token usage graphs, and collaboration flow diagrams.

### G

- **Git Integration Enhancement**: Automatic commit generation with meaningful messages, branch strategy recommendations, and merge conflict resolution assistance.

### I

- **Intelligent Code Search**: Semantic code search across large codebases, cross-repository pattern detection, and API usage discovery.

- **Interactive Debugging**: Integrated debugger with agent-driven breakpoint placement, variable inspection, and root cause analysis.

### M

- **Memory Management**: Long-term agent memory across sessions, project knowledge graphs, and context-aware memory retrieval.

- **Metrics Dashboard**: Real-time performance metrics, agent efficiency scoring, and collaboration quality analysis.

### N

- **Natural Language Queries**: Direct NLP-to-command translation, conversational code modification, and intent-based task execution.

### P

- **Plugin Architecture**: Third-party plugin support, custom tool integration API, and community plugin marketplace.

- **Project Templates**: Scaffolding for common project types, best-practice project structures, and framework-specific templates.

### R

- **Refactoring Automation**: Large-scale automated refactoring with safety checks, API deprecation handling, and code modernization workflows.

- **Remote Collaboration**: Multi-user collaboration sessions, shared workspace synchronization, and role-based access control.

### S

- **Security Auditing**: Automated vulnerability scanning, security best practice enforcement, and compliance checking.

- **Smart Conflict Resolution**: AI-driven merge conflict resolution, semantic conflict detection, and automated conflict testing.

### T

- **Task Scheduling**: Time-based task execution, dependency-aware task ordering, and priority-based scheduling.

- **Testing Integration**: Automated test execution with result analysis, regression detection, and test failure diagnosis.

### V

- **Version Control Intelligence**: Smart commit organization, automated changelog generation, and release note drafting.

### W

- **Web Interface**: Browser-based AXE interface, remote access support, and mobile-friendly UI.

- **Whistleblower Mechanism**: Privacy-enhanced agent-to-human communication - GPG-encrypted reports/files in local mailbox accessible only to worker agents and human users (not supervisors). For secure escalation outside supervisor oversight.

---

## Key Differentiators

### 🌐 Provider/Model Agnostic
AXE doesn't care what provider or model you use. Mix and match Claude, GPT, Llama, Grok, or any other LLM in the same session.

### 💬 Works with ANY Talking Model
No need for specialized "agentic coding" or "tool use" models. If the model can generate text, it can use AXE - the engine handles all parsing and execution.

### 🛡️ Sandbox Security
Bubblewrap (bwrap) isolation with a blacklist security model. Default-allow with explicit restrictions for maximum flexibility and safety.

### 🧠 Cognitive Architecture
Built on proven cognitive science: Brooks' Subsumption Architecture + Minsky's Society of Mind + Baars' Global Workspace Theory.

### 🔄 Turn-based Round-Robin Multi-Agent
One of the strongest collaboration systems - agents take turns with full context sharing, preventing chaos while maintaining coordination.

### 🎮 XP/Level/Title Progression
Gamification like "The Office" TV show - agents earn experience, level up, gain titles, and unlock privileges. Encourages growth and collaboration.

### 👔 @boss Supervisor
Always at least one supervisor agent to maintain oversight, resolve conflicts, and coordinate team efforts.

### 💾 Token Saving System
Efficient context management with sliding windows, conversation summarization, and intelligent truncation to minimize costs.

### 🔌 Unix Socket Interface
Agents can interactively connect to and control AXE's shell - use agents to command agents inside another program for coding, debugging, or improving AXE itself.

---

## Contributing

Features marked as "Planned" are open for community contributions. Please submit PRs with:
- Clear feature description and use case
- Test coverage for new functionality
- Documentation updates
- Examples demonstrating the feature

---

## References

### Cognitive Architecture Papers

- **Brooks, R. A. (1986)**. *A Robust Layered Control System for a Mobile Robot*. MIT AI Lab.
- **Minsky, M. (1986)**. *The Society of Mind*. Simon & Schuster.
- **Baars, B. J. (1988)**. *A Cognitive Theory of Consciousness*.
- **Simon, H. A. (1969)**. *The Sciences of the Artificial*.

### Multi-Agent Systems

- **Wooldridge, M. (2009)**. *An Introduction to MultiAgent Systems*. Wiley.
