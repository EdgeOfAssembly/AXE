# AXE - Agent eXecution Engine

<div align="center">

```
   ___   _  __ ____
  / _ | | |/_// __/
 / __ |_>  < / _/  
/_/ |_/_/|_|/___/  
```

**Terminal-based multiagent coding assistant for C, C++, Python, and reverse-engineering**

</div>

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Providers](#api-providers)
- [Usage Examples](#usage-examples)
- [Chat Commands Reference](#chat-commands-reference)
- [Agent Reference](#agent-reference)
- [Tool Whitelist](#tool-whitelist)
- [Advanced Usage](#advanced-usage)
- [Multi-Agent Collaboration](#multi-agent-collaboration)
- [Workshop - Dynamic Analysis Tools](#workshop---dynamic-analysis-tools)
- [Troubleshooting](#troubleshooting)

---

## Overview

AXE (Agent eXecution Engine) is a powerful terminal-based multiagent system designed for:

- **Coding Tasks**: C, C++, Python development with multiple AI assistants
- **Reverse Engineering**: Analysis of DOS-era binaries, WAD files, executables
- **Code Review**: Security auditing and code quality analysis
- **Multi-Provider Support**: Use Claude, GPT, Llama, Grok, and GitHub Copilot in one interface

### Why AXE?

1. **Unified Interface**: Talk to multiple AI models through one terminal interface
2. **Tool Integration**: Execute whitelisted commands (hexdump, objdump, gdb, etc.)
3. **Context-Aware**: Automatically provides project context to agents
4. **Safe Execution**: Command whitelist and directory access control
5. **Flexible Config**: YAML/JSON configuration for easy customization

---

## Features

### Note on Whistleblower Feature

The "whistleblower" mechanism – which allows worker agents to send GPG-encrypted reports or files to a local mailbox directory accessible only by other worker agents and the human user (not supervisor agents) – is currently an unfinished stub. It's planned for enhanced privacy and secure agent-to-human communication in multi-agent setups, but not yet implemented or functional yet.

### Multi-Provider AI Support

| Provider | Models | Status |
|----------|--------|--------|
| **Anthropic** | Claude 3.5 Sonnet, Claude Opus | ✓ Supported |
| **OpenAI** | GPT-4o, GPT-4 Turbo | ✓ Supported |
| **HuggingFace** | Llama 3.1 70B, Llama 4 Maverick | ✓ Supported (Free Tier) |
| **xAI** | Grok 4, Grok Code | ✓ Supported |
| **GitHub** | GPT-4o via GitHub Models | ✓ Supported (Free with Copilot) |

### Integrated Tools

- **Disassembly**: ndisasm, objdump, hexdump, readelf, nm, strings
- **Debugging**: gdb, lldb, strace, ltrace, valgrind
- **Building**: make, cmake, gcc, g++, clang, nasm
- **Analysis**: cppcheck, clang-format, clang-tidy, pylint, mypy
- **Emulation**: dosbox-x, xvfb-run

---

## Quick Start

```bash
# 1. Navigate to multiagent directory
cd multiagent

# 2. Install dependencies
pip install openai anthropic huggingface_hub pyyaml gitpython

# 3. Set up at least one API key
export HUGGINGFACE_API_KEY="your_key_here"  # Free tier available

# 4. Run interactive mode
python axe.py

# 5. Talk to an agent!
# axe> @llama explain what a WAD file format is
```

---

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Git (optional, for git features)

### Install Dependencies

```bash
# Core dependencies
pip install openai anthropic huggingface_hub pyyaml gitpython

# Optional: readline for better terminal experience
pip install readline  # Linux/macOS
pip install pyreadline3  # Windows
```

### Clone and Setup

```bash
git clone https://github.com/EdgeOfAssembly/RetroCodeMess.git
cd RetroCodeMess/multiagent
chmod +x axe.py
```

---

## Configuration

### API Keys Setup

Set environment variables for the providers you want to use:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or shell config

# Anthropic (Claude)
export ANTHROPIC_API_KEY='sk-ant-...'

# OpenAI (GPT)
export OPENAI_API_KEY='sk-proj-...'

# HuggingFace (Llama) - Free tier available!
export HUGGINGFACE_API_KEY='hf_...'

# xAI (Grok)
export XAI_API_KEY='xai-...'

# GitHub Models (uses GitHub PAT)
export GITHUB_TOKEN='github_pat_...'
```

### Configuration File (axe.yaml)

Generate a sample configuration:

```bash
python axe.py --init
```

This creates `axe.yaml` with default settings. Edit to customize:

```yaml
version: "1.0"
project_dir: "."

providers:
  anthropic:
    enabled: true
    env_key: ANTHROPIC_API_KEY
    models:
      - claude-3-5-sonnet-20241022
      - claude-3-opus-20240229

  openai:
    enabled: true
    env_key: OPENAI_API_KEY
    models:
      - gpt-4o
      - gpt-4-turbo

  huggingface:
    enabled: true
    env_key: HUGGINGFACE_API_KEY
    models:
      - meta-llama/Llama-3.1-70B-Instruct
      - meta-llama/Llama-4-Maverick-17B-128E-Instruct

  xai:
    enabled: true
    env_key: XAI_API_KEY
    base_url: https://api.x.ai/v1
    models:
      - grok-4-1-fast
      - grok-code-fast

  github:
    enabled: true
    env_key: GITHUB_TOKEN
    base_url: https://models.github.ai/inference
    models:
      - openai/gpt-4o
      - claude-opus-4-5

agents:
  gpt:
    alias: [g, openai]
    provider: openai
    model: gpt-4o
    role: General-purpose coder and architect

  claude:
    alias: [c, anthropic]
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    role: Code reviewer and security auditor

  llama:
    alias: [l, hf]
    provider: huggingface
    model: meta-llama/Llama-3.1-70B-Instruct
    role: Open-source hacker and assembly expert

  grok:
    alias: [x, xai]
    provider: xai
    model: grok-code-fast
    role: Creative problem solver

  copilot:
    alias: [cp, gh]
    provider: github
    model: openai/gpt-4o
    role: GitHub-integrated assistant
```

---

## API Providers

### HuggingFace (Llama) - Free Tier Available!

HuggingFace offers free inference for many models including Llama.

**Latest Models:**
| Model | Context | Best For |
|-------|---------|----------|
| `meta-llama/Llama-4-Maverick-17B-128E-Instruct` | 128K | General, Coding, Vision |
| `meta-llama/Llama-3.1-405B-Instruct` | 128K | Complex reasoning |
| `meta-llama/Llama-3.1-70B-Instruct` | 128K | Balanced performance |

**Setup:**
```bash
# 1. Create HuggingFace account at huggingface.co
# 2. Generate API token in settings
# 3. Request access to Llama models (usually auto-approved)
export HUGGINGFACE_API_KEY="hf_..."
```

### GitHub Models - Free with Copilot

If you have GitHub Copilot subscription, you can access models for free.

**Available Models:**
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `claude-opus-4-5`
- `gpt-5.1`

**Setup:**
```bash
# 1. Create a GitHub Personal Access Token
# 2. Grant 'models:read' permission
export GITHUB_TOKEN="github_pat_..."
```

### xAI (Grok)

**Latest Models:**
| Model | Context | Input | Capabilities |
|-------|---------|-------|--------------|
| `grok-4-1-fast` | 2M tokens | text | Function calling |
| `grok-code-fast` | 256K | text | Specialized for coding |
| `grok-2-vision` | 32K | image/text | Image understanding |
| `grok-2-image` | - | text | Image generation |

### Anthropic (Claude)

**Top Models:**
- `claude-opus-4-5` - Latest and most capable
- `claude-3-5-sonnet-20241022` - Best balance
- `claude-3-opus-20240229` - Deep reasoning

### OpenAI (GPT)

**Top Models:**
- `gpt-5.2-2025-12-11` - Latest
- `gpt-4o` - Multimodal, fast
- `gpt-4-turbo` - Long documents

---

## Usage Examples

### Interactive Mode

```bash
# Start AXE
python axe.py

# You'll see:
#    ___   _  __ ____
#   / _ | | |/_// __/
#  / __ |_>  < / _/  
# /_/ |_/_/|_|/___/  
# Agent eXecution Engine v1.0
# Type /help for commands, @agent to address agents
#
# axe>
```

### Basic Agent Conversations

```bash
# Ask Claude to review code
axe> @claude review main.c for security issues

# Ask GPT to write a function
axe> @gpt write a C function to parse WAD file headers

# Ask Llama about assembly
axe> @llama explain x86 calling conventions for DOS programs

# Ask Grok for creative solutions
axe> @grok brainstorm ways to optimize this game loop

# Use aliases for speed
axe> @c review this    # @c = @claude
axe> @g write code     # @g = @gpt
axe> @l disasm help    # @l = @llama
```

### Single Command Mode

```bash
# Quick one-liner queries
python axe.py -c "@llama what is the DOS interrupt 21h?"

# Code review
python axe.py -c "@claude analyze security of wadextract.c"

# Get coding help
python axe.py -c "@gpt write a Makefile for this project"
```

### Working with Files

```bash
# List code files in project
axe> /files

# Read a specific file
axe> /read wadextract.c

# Get project context
axe> /context

# Then ask agent about the code
axe> @claude review the wadextract.c file I just read
```

### Executing Tools

```bash
# Hexdump a binary
axe> /exec hexdump -C game.exe | head -20

# Disassemble
axe> /exec objdump -d program

# Run analysis
axe> /exec cppcheck --enable=all src/

# Compile code
axe> /exec gcc -o test main.c -lm
```

### Real-World Example: Reverse Engineering a WAD File

```bash
# Start AXE in the wadextract directory
cd doom/wadextract
python ../../multiagent/axe.py

# Step 1: Get overview
axe> /files
axe> /context

# Step 2: Ask Llama about WAD format
axe> @llama explain the DOOM WAD file format structure

# Step 3: Examine binary
axe> /exec hexdump -C DOOM.WAD | head -50

# Step 4: Ask Claude to review extractor code
axe> /read wadextract.c
axe> @claude review this WAD extractor for bugs and improvements

# Step 5: Ask GPT to optimize
axe> @gpt suggest optimizations for the lump parsing code
```

### Example: Multi-Agent Code Analysis

```bash
# Have different agents analyze the same code
axe> /read main.c

# Security review from Claude
axe> @claude analyze main.c for buffer overflows and security issues

# Architecture review from GPT
axe> @gpt review the overall structure and suggest improvements

# Low-level analysis from Llama
axe> @llama check for DOS compatibility issues in this code
```

---

## Chat Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `@<agent> <task>` | Send task to agent | `@gpt write hello world` |
| `/agents` | List available agents | `/agents` |
| `/tools` | List available tools | `/tools` |
| `/dirs` | Show directory permissions | `/dirs` |
| `/config` | Show current configuration | `/config` |
| `/files` | List project code files | `/files` |
| `/context` | Show project context | `/context` |
| `/read <file>` | Read file content | `/read main.c` |
| `/exec <cmd>` | Execute whitelisted command | `/exec make build` |
| `/history` | Show chat history | `/history` |
| `/clear` | Clear chat history | `/clear` |
| `/save` | Save current config | `/save` |
| `/help` | Show help | `/help` |
| `/quit` | Exit | `/quit` |

---

## Agent Reference

### Available Agents

| Agent | Aliases | Provider | Role |
|-------|---------|----------|------|
| `gpt` | `g`, `openai` | OpenAI | General-purpose coder and architect |
| `claude` | `c`, `anthropic` | Anthropic | Code reviewer and security auditor |
| `llama` | `l`, `hf` | HuggingFace | Open-source hacker and assembly expert |
| `grok` | `x`, `xai` | xAI | Creative problem solver |
| `copilot` | `cp`, `gh` | GitHub | GitHub-integrated assistant |

### When to Use Each Agent

| Task | Recommended Agent |
|------|-------------------|
| Code review & security | `@claude` |
| Writing new code | `@gpt` |
| Assembly & DOS | `@llama` |
| Brainstorming | `@grok` |
| GitHub workflows | `@copilot` |
| Budget-conscious work | `@llama` (free tier) |

---

## Tool Whitelist

### Disassembly & Analysis
```
ndisasm, objdump, hexdump, readelf, nm, strings
```

### Debugging
```
gdb, lldb, strace, ltrace, valgrind
```

### Building
```
make, cmake, gcc, g++, clang, clang++, ld, ar, nasm, as
```

### Python
```
python, python3, pip, pytest, pylint, mypy, black, flake8
```

### Version Control
```
git, diff, patch
```

### Download
```
curl, wget, wget2
```

### Emulation
```
dosbox-x, dosbox, xvfb-run
```

### Analysis
```
cppcheck, clang-format, clang-tidy
```

---

## Advanced Usage

### Custom Project Directory

```bash
# Work on a specific project
python axe.py --dir /path/to/project

# With custom config
python axe.py --dir /path/to/project --config my-axe.yaml
```

### Auto-Approve Mode (Non-Interactive)

```bash
# Auto-approve all tool executions
python axe.py --auto-approve

# Dry-run mode (show what would be executed)
python axe.py --dry-run
```

### Batch Processing

```bash
# Run multiple commands
python axe.py -c "@llama analyze the code" && \
python axe.py -c "@claude security review" && \
python axe.py -c "@gpt suggest improvements"
```

### Custom System Prompts

Edit `axe.yaml` to customize agent behavior:

```yaml
agents:
  custom_agent:
    alias: [my]
    provider: openai
    model: gpt-4o
    role: My custom assistant
    system_prompt: |
      You are a specialized assistant for my specific use case.
      Always format code in a specific way.
      Focus on X, Y, Z aspects.
```

---

## Multi-Agent Collaboration

### Autonomous Collaborative Sessions (NEW!)

Start a fully autonomous session where multiple agents work together on a task without manual intervention:

```bash
# Command-line mode
python axe.py --collab llama,copilot --workspace ./playground --time 30 --task "Review and improve wadextract.c"

# Interactive mode
axe> /collab llama,copilot ./playground 30 "Analyze the WAD parser and suggest improvements"
```

**Features:**
- **Turn-based coordination**: Agents take turns automatically, no manual copy-pasting needed
- **Shared workspace**: All agents can read/write to the same directory
- **Time limits**: Sessions automatically end after the specified time
- **Auto-backup**: Files are backed up before modification
- **Conversation history**: All agents see the full conversation context
- **Human intervention**: Press Ctrl+C to pause and inject messages

**During collaborative session:**
- Agents see each other's responses and build on them
- Agents can say "PASS" to skip their turn
- Agents can say "TASK COMPLETE: summary" to end the session
- Session log is saved to `.collab_log.md` in the workspace

**Example collaborative workflow:**
```
┌─────────────────────────────────────────────────────────────┐
│ BOSS: "Review wadextract.c and add error handling"         │
├─────────────────────────────────────────────────────────────┤
│ LLAMA: "I'll analyze the code structure first..."          │
│        *provides analysis*                                  │
├─────────────────────────────────────────────────────────────┤
│ COPILOT: "@llama good analysis! I'll add error handling..."│
│          *shows code improvements*                          │
├─────────────────────────────────────────────────────────────┤
│ LLAMA: "@copilot looks good, but let me check edge cases..."│
│        *reviews copilot's code*                             │
├─────────────────────────────────────────────────────────────┤
│ COPILOT: "TASK COMPLETE: Added null checks and bounds..."  │
└─────────────────────────────────────────────────────────────┘
```

### Round-Robin Analysis

Ask multiple agents to analyze the same problem:

```bash
axe> /read complex_function.c
axe> @claude what security issues do you see?
axe> @gpt how would you refactor this?
axe> @llama any assembly-level optimizations possible?
```

### Chain of Thought

Use one agent's output as input for another:

```bash
axe> @gpt write a function to parse WAD headers
# Copy the output...
axe> @claude review this function: [paste GPT's code]
axe> @llama optimize this for DOS: [paste Claude's reviewed code]
```

### Collaborative Problem Solving

For complex projects, assign different aspects to different agents:

```bash
# Architecture planning
axe> @gpt design the module structure for a WAD parser library

# Security review
axe> @claude review the proposed API for security considerations

# Implementation details
axe> @llama help with the low-level binary parsing

# Creative optimization
axe> @grok suggest unconventional approaches to improve performance
```

---

## Workshop - Dynamic Analysis Tools

AXE includes **Workshop**, a comprehensive suite of reverse-engineering and security analysis tools designed for advanced code analysis and vulnerability detection.

### Overview

The Workshop framework provides four powerful analysis tools, each named after woodworking implements:

| Tool | Purpose | Command | Dependencies |
|------|---------|---------|--------------|
| **Chisel** | Symbolic execution for binary analysis | `/workshop chisel <binary> [func]` | angr |
| **Saw** | Taint analysis for Python code | `/workshop saw "<code>"` | (built-in) |
| **Plane** | Source/sink enumeration | `/workshop plane <path>` | (built-in) |
| **Hammer** | Live process instrumentation | `/workshop hammer <process>` | frida-python, psutil |

### Installation

Install Workshop dependencies:

```bash
# Install all dependencies
pip install angr frida-python psutil

# Or install individually
pip install angr           # For Chisel symbolic execution
pip install frida-python   # For Hammer instrumentation
pip install psutil         # For Hammer process monitoring
```

### Quick Examples

#### Chisel - Symbolic Execution
Analyze binary execution paths and find vulnerabilities:

```bash
axe> /workshop chisel ./vulnerable.exe main
# Outputs: paths explored, constraints found, potential vulnerabilities
```

**Use Chisel when:**
- Analyzing compiled binaries for security issues
- Finding buffer overflows and memory corruption bugs
- Exploring execution paths in compiled code
- Analyzing obfuscated or packed executables

#### Saw - Taint Analysis
Track data flow to identify injection vulnerabilities:

```bash
axe> /workshop saw "import os; os.system(input())"
# Outputs: taint sources, sinks, flows, and vulnerability classifications
```

**Use Saw when:**
- Auditing Python code for injection vulnerabilities
- Tracking user input through application flow
- Finding SQL injection, XSS, command injection risks
- Validating input sanitization

#### Plane - Source/Sink Enumeration
Catalog all data entry and exit points in a codebase:

```bash
axe> /workshop plane .
# Outputs: all sources (input, file reads, network) and sinks (exec, eval, db queries)
```

**Use Plane when:**
- Performing comprehensive security audits
- Mapping attack surface of applications
- Planning focused security reviews
- Documenting data flow architecture

#### Hammer - Live Instrumentation
Monitor and instrument running processes in real-time:

```bash
axe> /workshop hammer python.exe
# Starts live monitoring session (Ctrl+C to stop)
```

**Use Hammer when:**
- Debugging runtime behavior
- Analyzing malware or suspicious processes
- Monitoring function calls and API usage
- Dynamic analysis of running applications

### Management Commands

#### View Analysis History

```bash
# View all analyses
axe> /workshop history

# View specific tool history
axe> /workshop history chisel
axe> /workshop history saw
```

#### View Usage Statistics

```bash
# View overall statistics
axe> /workshop stats

# View specific tool stats
axe> /workshop stats hammer
```

### Configuration

Workshop tools can be configured in `axe.yaml`:

```yaml
workshop:
  enabled: true
  
  chisel:
    max_paths: 1000          # Maximum paths to explore
    timeout: 30              # Analysis timeout in seconds
    memory_limit: 1024       # Memory limit in MB
  
  saw:
    max_depth: 10            # Maximum taint propagation depth
    confidence_threshold: 0.7 # Minimum confidence for reporting
  
  plane:
    exclude_patterns:        # Patterns to exclude from enumeration
      - __pycache__
      - .git
      - venv
    max_files: 1000          # Maximum files to analyze
  
  hammer:
    monitoring_interval: 0.1 # Polling interval for monitoring
    max_sessions: 5          # Maximum concurrent sessions
```

### Integration with Agents

Agents can leverage Workshop tools for enhanced analysis:

```bash
# Ask Claude to use Workshop for security audit
axe> @claude use /workshop saw to analyze this code for injection vulnerabilities

# Ask GPT to analyze a binary
axe> @gpt analyze this binary with /workshop chisel and explain the findings

# Collaborative security review
axe> /collab claude,llama ./project 60 "Use workshop tools to perform comprehensive security audit"
```

### Database Integration

All Workshop analyses are automatically:
- Saved to the AXE database with full results
- Tracked with performance metrics (duration, success/failure)
- Linked to the XP system for agent progression
- Available for historical review and statistics

### XP Rewards

Workshop tool usage awards XP to agents:

| Tool | Base XP | Bonuses |
|------|---------|---------|
| **Chisel** | 25 XP | +10 per vulnerability, +20 for path exploration |
| **Saw** | 20 XP | +15 per taint flow, +25 per vulnerability |
| **Plane** | 15 XP | +1 per 5 sources/sinks enumerated |
| **Hammer** | 30 XP | +20 for successful instrumentation |

### Real-World Example: Security Audit Workflow

```bash
# Start AXE in your project
cd ~/my-project
axe

# Step 1: Enumerate attack surface
axe> /workshop plane .

# Step 2: Analyze suspicious code
axe> /workshop saw "$(cat suspicious_function.py)"

# Step 3: Review with agents
axe> @claude I found taint flows with Saw. Can you review the results and suggest fixes?

# Step 4: Verify fixes
axe> /workshop saw "$(cat fixed_function.py)"

# Step 5: Check statistics
axe> /workshop stats
```

### Documentation

For detailed documentation, see:
- **[workshop_quick_reference.md](workshop_quick_reference.md)** - Complete usage guide
- **[workshop_benchmarks.md](workshop_benchmarks.md)** - Performance metrics
- **[workshop_security_audit.md](workshop_security_audit.md)** - Security validation
- **[workshop_test_results.md](workshop_test_results.md)** - Test coverage details

### Help

Get help anytime with:

```bash
axe> /workshop help
axe> /workshop          # Same as /workshop help
```

---

## Troubleshooting

### Common Issues

**"Provider not available"**
```bash
# Check if API key is set
echo $HUGGINGFACE_API_KEY

# Make sure the library is installed
pip install huggingface_hub
```

**"Model not found"**
```bash
# Verify exact model name in config
# HuggingFace models need full path: meta-llama/Llama-3.1-70B-Instruct
```

**"Rate limited"**
```bash
# Wait a moment and try again
# Or switch to a different provider
axe> @llama instead of @gpt
```

**"Command not in whitelist"**
```bash
# Check available tools
axe> /tools

# Add tools to axe.yaml if needed
```

### Testing API Connections

```bash
# Test HuggingFace
curl -X POST https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-70B-Instruct \
  -H "Authorization: Bearer $HUGGINGFACE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello, how are you?"}'

# Test GitHub Models
curl -X POST "https://models.github.ai/inference/chat/completions" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-4o", "messages": [{"role": "user", "content": "Hi"}]}'
```

---

## Project Structure

```
AXE/
├── axe.py              # Main program
├── axe.yaml            # Default configuration
├── API_PROVIDERS.md    # Detailed API documentation
├── README.md           # This file
└── llm_prep/           # LLM context preparation files
    ├── codebase_overview.md
    ├── llm_system_prompt.md
    └── project_guidance.md
```

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License

Copyright (c) 2025 EdgeOfAssembly

This project is dual-licensed:

### Open Source License (Default)

This software is licensed under the **GNU General Public License v3.0 (GPLv3)**.

See the [LICENSE](LICENSE) file for the full license text.

### Commercial License

For commercial use or if you need a license other than GPLv3, please contact the author:

**EdgeOfAssembly**  
Email: haxbox2000@gmail.com


## Author

---

**EdgeOfAssemblly** - haxbox2000@gmail.com

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    AXE Quick Reference                          │
├─────────────────────────────────────────────────────────────────┤
│ AGENTS (use @ prefix)                                           │
│   @gpt, @g     - OpenAI GPT-4o                                 │
│   @claude, @c  - Anthropic Claude                              │
│   @llama, @l   - HuggingFace Llama (FREE!)                     │
│   @grok, @x    - xAI Grok                                      │
│   @copilot, @cp - GitHub Models                                │
├─────────────────────────────────────────────────────────────────┤
│ COMMANDS (use / prefix)                                         │
│   /agents  - List agents        /tools   - List tools          │
│   /files   - List code files    /context - Project summary     │
│   /read X  - Read file X        /exec X  - Run command X       │
│   /history - Chat history       /clear   - Clear history       │
│   /workshop - Analysis tools    /help    - Show help           │
│   /quit    - Exit                                               │
├─────────────────────────────────────────────────────────────────┤
│ WORKSHOP TOOLS (Dynamic Analysis)                               │
│   /workshop chisel <binary>     - Symbolic execution           │
│   /workshop saw "<code>"        - Taint analysis               │
│   /workshop plane <path>        - Source/sink enumeration      │
│   /workshop hammer <process>    - Live instrumentation         │
│   /workshop history             - View analysis history        │
├─────────────────────────────────────────────────────────────────┤
│ COLLABORATIVE MODE (NEW!)                                       │
│   /collab agents workspace time "task"                         │
│   Example: /collab llama,copilot ./playground 30 "Review code" │
│   Ctrl+C during session: pause/inject/stop                     │
├─────────────────────────────────────────────────────────────────┤
│ EXAMPLES                                                        │
│   @llama explain WAD file format                               │
│   @claude review main.c for security issues                    │
│   @gpt write a function to parse binary headers                │
│   /exec hexdump -C game.exe | head -20                         │
│   /read wadextract.c                                           │
└─────────────────────────────────────────────────────────────────┘
```
