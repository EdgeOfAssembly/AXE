# AXE - Agent eXecution Engine

<div align="center">

```
   ___   _  __ ____
  / _ | | |/_// __/
 / __ |_>  < / _/  
/_/ |_/_/|_|/___/  
```

**Terminal-based multiagent coding assistant for C, C++, Python, and reverse-engineering**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## What is AXE?

**AXE (Agent eXecution Engine)** is a powerful terminal-based multiagent system that orchestrates multiple AI assistants to collaborate on complex coding, debugging, security auditing, and reverse engineering tasks. Built on proven cognitive science principles, AXE provides a unified interface for working with any AI model from any provider.

Think of AXE as your AI coding team manager - it coordinates multiple specialists, manages their interactions, tracks their contributions, and ensures they work together effectively on your projects.

---

## Why AXE?

### 🌐 Provider/Model Agnostic
**AXE doesn't care what provider or model you use.** Mix and match Claude Opus 4.5, GPT-5.2, Llama 4 Maverick, Grok 4.1, or any other LLM in the same session. No vendor lock-in, ever.

### 💬 Works with ANY Talking Model
**No need for specialized "agentic coding" or "tool use" models.** If the model can generate text, it can use AXE - the engine handles all the heavy-lifting parsing and executing. Just provide text, and AXE takes care of the rest.

### 🤝 Strong Multi-Agent Collaboration
**Turn-based round-robin coordination** prevents chaos while maintaining full context sharing. Agents take turns, build on each other's work, and vote on contributions - one of the strongest collaboration systems available.

### 🧠 Built-in Cognitive Architecture
Grounded in proven cognitive science:
- **Brooks' Subsumption Architecture** (1986) - Layered behavioral control
- **Minsky's Society of Mind** (1986) - Peer voting and conflict resolution
- **Baars' Global Workspace Theory** (1988) - Broadcast-based communication
- **Simon's Nearly-Decomposable Hierarchies** (1969) - Privilege levels by rank

### 🎮 Gamification for Agents
**XP/Level/Title progression system** like "The Office" TV show - agents earn experience, level up from Worker to Supervisor, gain titles, and unlock privileges. Encourages growth, collaboration, and quality contributions.

### 🛡️ Sandbox Security
**Bubblewrap (bwrap) isolation** with blacklist security model. Default-allow with explicit restrictions for maximum flexibility while preventing access to sensitive paths and commands.

---

## Quick Install (TL;DR)

### Option A: Standard venv + pip

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./axe.py
```

### Option B: Using mkpyenv tool

```bash
# Usage
tools/mkpyenv [options] <target>

# Examples:
tools/mkpyenv --python 3.11 ./myenv
tools/mkpyenv --python 3.12 -i "requests anthropic openai" ./myenv
tools/mkpyenv -i requirements.txt ./venv

# Activate and run
source ./venv/bin/activate
./axe.py
```

---

## Features

For a complete alphabetically-organized catalog of all implemented and planned features, see **[TODO.md](TODO.md)**.

### Key Implemented Features

- **Provider/Model Agnostic**: Works with Claude Opus 4.5, GPT-5.2, Llama 4, Grok 4.1, and any other LLM
- **Works with ANY Talking Model**: No need for specialized "tool use" models
- **Cognitive Architecture**: Brooks' Subsumption + Minsky's Society of Mind + Baars' Global Workspace
- **Multi-Agent Collaboration**: Turn-based round-robin with full context sharing
- **XP/Level Progression**: Gamification system with Worker → Supervisor progression
- **Bubblewrap Sandbox**: Linux namespace isolation for secure execution
- **Agent Skills System**: 25+ domain-specific expertise modules loaded on-demand
- **Workshop Tools**: Chisel (symbolic execution), Hammer (Frida), Saw (taint), Plane (source/sink)
- **Unix Socket Interface**: Agent-to-AXE bidirectional communication
- **Multi-Format Parsing**: XML, Bash, native READ/WRITE/EXEC blocks
- **Token Optimization**: Context management, summarization, compression
- **Arbitration Protocol**: Minsky's conflict resolution system
- **Privilege Mapping**: Four-tier access control (Worker, Senior, Deputy, Supervisor)

See **[TODO.md](TODO.md)** for the complete feature catalog.

---

## Command-Line Options

```bash
./axe.py -h

usage: axe.py [-h] [-d DIR] [-c COMMAND] [--config CONFIG] [--init] [--dry-run]
              [--collab COLLAB] [--workspace WORKSPACE] [--time TIME] [--task TASK]
              [--enable-github]

options:
  -h, --help            Show help message
  -d, --dir DIR         Project directory (default: current)
  -c, --command COMMAND Single command to execute
  --config CONFIG       Config file path (YAML or JSON)
  --init                Generate sample config file
  --dry-run             Dry-run mode for tool executions
  --collab COLLAB       Start collaborative session with comma-separated agents
  --workspace WORKSPACE Workspace directory(s) - comma-separated for multiple
  --time TIME           Time limit in minutes (default: 30)
  --task TASK           Task description for collaborative session
  --enable-github       Enable autonomous GitHub operations (disabled by default)

Examples:
  axe.py                           # Interactive chat mode
  axe.py -c "@gpt analyze main.c"  # Single command
  axe.py --config my.yaml          # Use custom config
  axe.py --init                    # Generate sample config
  
Collaborative Mode:
  axe.py --collab llama,copilot --workspace ./playground --time 30 --task "Review code"
```

---

## Interactive Mode

Interactive mode for single-agent use with human in the loop:

```bash
./axe.py
```

### Commands

#### Basic Commands
```
@<agent> <task>   Send task to agent (e.g., @gpt analyze this code)
/agents           List available agents and their status
/rules            Display session rules
/tools            List available tools by category
/dirs             Show directory access permissions
/config           Show current configuration
/files            List project code files
/context          Show project context summary
/read <file>      Read file content
/exec <cmd>       Execute a whitelisted command
/history          Show chat history
/clear            Clear chat history
/save             Save current config
/stats [agent]    Show token usage statistics and cost estimates
/tokenopt-stats   Show token optimization statistics (live reporting)
/help             Show this help
/quit             Exit
```

#### Session Management
```
/session save <name>   Save current session
/session load <name>   Load a saved session
/session list          List all saved sessions
```

#### Analysis Tools
```
/prep [dir] [-o output_dir]         Generate codebase overview, stats, structure
/llmprep [dir] [-o output_dir]      Alias for /prep
/buildinfo <path> [--json]          Detect build system (Autotools, CMake, Meson, etc.)
                                    Supports directories and .tar/.tar.gz/.tar.zst archives
```

#### Workspace Management
```
/workspace                          Show current workspace(s)
/workspace <path>                   Set workspace directory
/workspace <path1>,<path2>          Set multiple workspaces (comma-separated)
/workspace +<path>                  Add workspace to list
/workspace -<path>                  Remove workspace from list
/workspace clear                    Clear all workspaces (use project dir only)
```

#### Workshop Tools
```
/workshop chisel <binary> [func]    Symbolic execution
/workshop saw "<code>"              Taint analysis
/workshop plane <path>              Source/sink enumeration
/workshop hammer <process>          Live instrumentation
/workshop status                    Check tool availability and dependencies
/workshop help [tool]               Get detailed help for a specific tool
/workshop history [tool]            View analysis history
/workshop stats [tool]              View usage statistics
```

#### Collaborative Mode
```
/collab <agents> <workspace(s)> <time> <task>
                  Start collaborative session with multiple agents
                  Workspace(s) can be comma-separated for multiple
                  Example: /collab llama,copilot ./playground 30 "Review and improve wadextract.c"
                  Example: /collab llama,copilot /tmp/a,/tmp/b 30 "Cross-project analysis"

During collaboration:
  Ctrl+C          Pause session (options: continue, stop, inject message)
  Agents say "PASS" to skip their turn
  Agents say "TASK COMPLETE: summary" when done
```

#### Agent Aliases
```
@g, @gpt         OpenAI GPT
@c, @claude      Anthropic Claude
@l, @llama       HuggingFace Llama
@x, @grok        xAI Grok
@cp, @copilot    GitHub Copilot
```

#### Examples
```
@claude review this function for security issues
@gpt write a parser for DOS WAD files in C
@llama disassemble the interrupt handler at 0x1000
/exec hexdump -C game.exe | head -20
/workspace /tmp/playground
/workspace +/tmp/projectX
/workshop saw "import os; os.system(input())"
/collab llama,copilot ./playground 30 "Analyze and document wadextract.c"
/collab grok,copilot /tmp/a,/tmp/b 60 "Do cross-project code review"
```

---

## Collaboration Mode

Multi-agent collaboration with turn-based round-robin coordination:

### With Cloud Models

```bash
# Claude Opus 4.5 + GPT-5.2
./axe.py --collab claude,gpt --workspace ./project --time 60 --task "Implement feature X"

# Grok 4.1 + Claude Sonnet 4.5
./axe.py --collab grok,claude --workspace ./src --time 45 --task "Security audit"
```

### With Local Ollama Models

```bash
# Start ollama first
ollama serve

# Use local models (Llama 4 Scout, Maverick, etc.)
./axe.py --collab llama,codellama --workspace ./project --time 30 --task "Debug code"

# Llama 3.3 70B
./axe.py --collab llama3.3 --workspace ./analytics --time 60 --task "Optimize algorithms"
```

### Mixed Cloud + Local

```bash
# Claude (cloud) + Llama 4 (local)
./axe.py --collab claude,llama --workspace ./project --time 45 --task "Security audit"

# GPT-5.2 (cloud) + Llama 3.3 (local)
./axe.py --collab gpt,llama3.3 --workspace ./backend --time 60 --task "API review"
```

### Multiple Workspaces

```bash
# Work across multiple directories
./axe.py --collab grok,copilot --workspace /tmp/frontend,/tmp/backend --time 60 --task "Full stack review"
```

---

## Batch Mode

Execute single commands without interactive mode:

```bash
# Single command
./axe.py -c "@claude explain this error"

# With workspace
./axe.py -c "@gpt list all Python files" --workspace /tmp/myproject

# Dry run
./axe.py -c "@llama refactor main.py" --dry-run
```

---

## API Providers

### Anthropic (Claude)
- **Models**: Opus 4.5, Sonnet 4.5, Haiku 4.5
- **Features**: Prompt caching, extended thinking, vision, reasoning effort
- **API Key**: `ANTHROPIC_API_KEY`

### OpenAI (GPT)
- **Models**: GPT-5.2, GPT-5.1, o1/o3 series
- **Features**: 400K context window, function calling, vision
- **API Key**: `OPENAI_API_KEY`

### xAI (Grok)
- **Models**: Grok 4.1, Grok-2 mini
- **Features**: Real-time X data, uncensored responses
- **API Key**: `XAI_API_KEY`

### Meta Llama (via Ollama)
- **Models**: Llama 4 Scout, Llama 4 Maverick, Llama 3.3 70B
- **Features**: Local deployment, multimodal, open source
- **Setup**: `ollama serve`

### Others
- **HuggingFace**: Various models, free tier
- **GitHub Copilot**: GPT-5.2 via GitHub Models
- **DeepSeek**: DeepSeek-V3, DeepSeek-Coder
- **Qwen**: Qwen series (multilingual)

---

## Configuration

Three-file configuration architecture:

1. **models.yaml** - Model metadata (context windows, capabilities)
2. **providers.yaml** - Provider infrastructure (endpoints, auth)
3. **axe.yaml** - User configuration (agents, prompts, tools)

Generate sample config:
```bash
./axe.py --init
```

---

## Tools Directory

### mkpyenv
Creates relocatable Python virtual environments:
```bash
tools/mkpyenv --python 3.11 ./myenv
tools/mkpyenv -i requirements.txt ./venv
```

### llmprep
Codebase preparation for LLM context:
- Build system detection
- Source tree analysis
- Token-optimized output

### minifier
Source code minifier (C/C++/Python/Assembly):
- Comment/docstring removal
- Preserves compilability
- Language auto-detection

### build_analyzer
Build system detection and analysis:
- Makefile, CMake, Ninja detection
- Build command extraction

---

## Documentation

- **[AGENTS.md](AGENTS.md)** - Agent collaboration guidelines
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[MISSION.md](MISSION.md)** - Project mission statement
- **[TODO.md](TODO.md)** - Complete feature catalog

---

## Scientific References

### Cognitive Architecture

- **Brooks, R. A. (1986)**. *A Robust Layered Control System for a Mobile Robot*. MIT AI Lab.
  - Subsumption Architecture: layered behaviors, suppression/inhibition

- **Minsky, M. (1986)**. *The Society of Mind*. Simon & Schuster.
  - Agent negotiation, emergent reputation, cross-exclusion, conflict resolution

- **Baars, B. J. (1988)**. *A Cognitive Theory of Consciousness*.
  - Global Workspace Theory: broadcast-based agent communication

- **Simon, H. A. (1969)**. *The Sciences of the Artificial*.
  - Nearly-Decomposable Hierarchies: modular system organization

### Multi-Agent Systems

- **Wooldridge, M. (2009)**. *An Introduction to MultiAgent Systems*. Wiley.
  - Foundations of agent coordination and collaboration

---

## Contact & Issues

- **Issues**: [https://github.com/EdgeOfAssembly/AXE/issues](https://github.com/EdgeOfAssembly/AXE/issues)
- **Discussions**: [https://github.com/EdgeOfAssembly/AXE/discussions](https://github.com/EdgeOfAssembly/AXE/discussions)

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Author

**EdgeOfAssembly**

AXE is developed and maintained by EdgeOfAssembly with contributions from the open source community.

---

<div align="center">

**Built with ❤️ for the coding community**

*"The whole is greater than the sum of its parts" - Aristotle*

</div>
