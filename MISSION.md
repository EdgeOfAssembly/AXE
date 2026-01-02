# AXE - Agent eXecution Engine

## Mission Statement

AXE is a lightweight, modular execution engine designed to orchestrate AI agent workflows with precision and reliability. Our goal is to provide developers with a robust framework for building, testing, and deploying agent-based systems.

## Core Principles

1. **Simplicity** - Clean interfaces that are easy to understand and extend
2. **Reliability** - Predictable behavior with comprehensive error handling
3. **Modularity** - Components that can be mixed and matched as needed
4. **Observability** - Full visibility into agent execution and state

## Agent Communication Tokens

AXE uses special control tokens to coordinate multi-agent interactions. These tokens are defined in `axe.py` and should NEVER be written literally in files, as they trigger detection.

### Token Reference

To see the current token definitions, run:
```bash
grep "AGENT_TOKEN" axe.py | head -6
```

**Important**: Do not copy or paste these tokens into any documentation or files. The token detection system will trigger on them even in quoted text or file content.

### Token Purpose

The tokens enable agents to:
- **Pass control** to the next agent in sequence
- **Request breaks** when needing rest
- **Report task completion** with a summary
- **Signal emergencies** that need immediate attention  
- **Spawn new agents** (supervisor only)
- **Check status** of the collaboration

### Usage Guidelines

- Tokens are automatically detected in agent responses
- Only use tokens when you genuinely intend to trigger that action
- Reading files that contain token definitions will NOT trigger false positives (the engine strips file content)
- Tokens work whether in old format or new format

## Architecture Overview

```
┌─────────────────────────────────────────┐
│            AXE Orchestrator             │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Agent 1 │ │ Agent 2 │ │ Agent N │   │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│           Token Parser Layer            │
├─────────────────────────────────────────┤
│           State Management              │
└─────────────────────────────────────────┘
```

## Getting Started

See [QUICKSTART.md](./QUICKSTART.md) for installation and setup instructions.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before submitting pull requests.

## License

MIT License - See [LICENSE](./LICENSE) for details.
