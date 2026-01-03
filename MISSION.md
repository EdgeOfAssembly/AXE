# AXE - Agent eXecution Engine

## Mission Statement

AXE is a lightweight, modular execution engine designed to orchestrate AI agent workflows with precision and reliability. Our goal is to provide developers with a robust framework for building, testing, and deploying agent-based systems.

## Core Principles

1. **Simplicity** - Clean interfaces that are easy to understand and extend
2. **Reliability** - Predictable behavior with comprehensive error handling
3. **Modularity** - Components that can be mixed and matched as needed
4. **Observability** - Full visibility into agent execution and state

## Workshop - Dynamic Analysis Tools

AXE includes advanced dynamic analysis capabilities through our "Workshop" module, featuring woodworking-themed tools for comprehensive code analysis:

- **Chisel**: Symbolic execution engine for precise vulnerability detection and path analysis
- **Saw**: Taint tracking system for identifying data flow vulnerabilities and injection attacks
- **Plane**: Source/sink enumeration for cataloging all entry and exit points in codebases
- **Hammer**: Live instrumentation framework for runtime monitoring and dynamic analysis

These tools enhance AXE's security auditing and reverse engineering capabilities, providing agents with powerful analysis instruments.

**Quality Assurance**: Comprehensive validation completed including [performance benchmarks](workshop_benchmarks.md), [security audit](workshop_security_audit.md), [dependency validation](workshop_dependency_validation.md), and [test suite results](workshop_test_results.md).

## Agent Communication Tokens

AXE uses special control tokens to coordinate multi-agent interactions. These tokens are defined in `axe.py` and should NEVER be written literally in files, as they trigger detection.

### Token Reference

To see the current token definitions, run:
```bash
grep "AGENT_TOKEN" axe.py | head -6
```

**Important**: Do not copy or paste these tokens into any documentation or files. While the token detection system now properly filters out file content and code blocks, it's still best practice to avoid literal tokens in documentation.

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
