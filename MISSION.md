# AXE - Agent eXecution Engine

## Mission Statement

AXE is a lightweight, modular execution engine designed to orchestrate AI agent workflows with precision and reliability. Our goal is to provide developers with a robust framework for building, testing, and deploying agent-based systems.

## Core Principles

1. **Simplicity** - Clean interfaces that are easy to understand and extend
2. **Reliability** - Predictable behavior with comprehensive error handling
3. **Modularity** - Components that can be mixed and matched as needed
4. **Observability** - Full visibility into agent execution and state

## Token Documentation

The following control tokens are used to manage agent turn-taking and execution flow. These tokens are parsed by the execution engine to coordinate multi-agent interactions.

### Available Tokens

| Token | Description |
|-------|-------------|
| `[[` + `AGENT_PASS_TURN]]` | Signals that the current agent is yielding control to the next agent in the queue |
| `[[` + `AGENT_REQUEST_INPUT]]` | Indicates the agent needs user input before proceeding |
| `[[` + `AGENT_COMPLETE]]` | Marks the successful completion of an agent's task |
| `[[` + `AGENT_ERROR]]` | Signals an error condition that requires handling |
| `[[` + `AGENT_WAIT]]` | Pauses execution until an external condition is met |

### Usage Examples

When an agent finishes its subtask and needs to hand off:
```
Result: Analysis complete.
[[` + `AGENT_PASS_TURN]]
```

When an agent encounters an unrecoverable error:
```
Error: Unable to access resource.
[[` + `AGENT_ERROR]]
```

When all work is successfully completed:
```
Task finished successfully.
[[` + `AGENT_COMPLETE]]
```

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
