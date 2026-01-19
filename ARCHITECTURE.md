# AXE Architecture and Extensibility Guide

This document describes the AXE architecture and provides guidance for extending the codebase with new features like local models (Ollama) and distributed AI (Python Ray).

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AXE System Architecture                        │
└─────────────────────────────────────────────────────────────────────────────┘

                                  ┌──────────┐
                                  │  User    │
                                  │Terminal  │
                                  └────┬─────┘
                                       │
                       ┌───────────────▼────────────────┐
                       │         axe.py                 │
                       │   (Main Entry Point)           │
                       │   - Session management         │
                       │   - Command loop               │
                       │   - Agent coordination         │
                       └───────────────┬────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────▼────────┐          ┌──────────▼──────────┐       ┌──────────▼─────────┐
│   Configuration│          │   Core Modules      │       │  Agent Managers    │
│   ────────────│          │   ──────────────    │       │  ──────────────    │
│ • axe.yaml    │          │ • agent_manager.py  │       │ • break_system.py  │
│ • models.yaml │          │ • tool_runner.py    │       │ • dynamic_spawner  │
│ • skills/     │◄─────────┤ • skills_manager.py │       │ • emergency_mailbox│
│   manifest    │          │ • sandbox.py        │       └────────────────────┘
└───────────────┘          │ • session_manager   │
                           │ • multiprocess.py   │
                           └──────────┬──────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
        ┌───────────▼───────┐  ┌──────▼──────┐  ┌──────▼──────────┐
        │   AI Providers    │  │ Tool Parser │  │  Skills System  │
        │   ────────────    │  │ ────────────│  │  ────────────   │
        │ • Anthropic       │  │ • XML calls │  │ • manifest.json │
        │   (Claude)        │  │ • Bash tags │  │ • *.md skills   │
        │ • OpenAI (GPT)    │  │ • Code blks │  │ • Auto-inject   │
        │ • xAI (Grok)      │  │ • READ/WRITE│  │ • Domain expert │
        │ • HuggingFace     │  │ • EXEC      │  │   patterns      │
        │ • GitHub Copilot  │  └─────────────┘  └─────────────────┘
        └───────────────────┘
                │
        ┌───────▼────────┐
        │  Response      │
        │  Processing    │
        │  ────────────  │
        │ • Parse output │
        │ • Execute tools│
        │ • Update conv  │
        └────────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐  ┌────▼────┐  ┌───▼──────┐
│Database│  │Workshop │  │Security  │
│────────│  │─────────│  │─────────-│
│• SQLite│  │• Chisel │  │• Sandbox │
│• Agent │  │• Hammer │  │• Whitelist│
│  state │  │• Saw    │  │• Path    │
│• XP/lvl│  │• Plane  │  │  checks  │
└────────┘  └─────────┘  └──────────┘
```

## Module Structure

```
AXE/
├── axe.py                        # Main entry point and session management
├── axe.yaml                      # Configuration file
├── models.yaml                   # Model metadata and capabilities
│
├── core/                         # Core functionality
│   ├── __init__.py
│   ├── constants.py              # Global constants and default config
│   ├── config.py                 # Configuration management
│   ├── agent_manager.py          # Agent connections and API calls
│   ├── tool_runner.py            # Command execution with safety checks
│   ├── multiprocess.py           # Multi-agent collaboration
│   ├── session_manager.py        # Session save/load persistence
│   ├── session_preprocessor.py   # Input preprocessing pipeline
│   ├── skills_manager.py         # Agent skills loading & injection
│   ├── sandbox.py                # Bubblewrap sandboxed execution
│   ├── resource_monitor.py       # System resource monitoring
│   ├── acp_validator.py          # Agent Communication Protocol validation
│   ├── anthropic_features.py     # Anthropic-specific features
│   ├── github_agent.py           # GitHub Copilot integration
│   └── environment_probe.py      # Environment detection & setup
│
├── managers/                     # Agent lifecycle management
│   ├── __init__.py
│   ├── break_system.py           # Agent break requests
│   ├── dynamic_spawner.py        # Dynamic agent spawning
│   └── emergency_mailbox.py      # GPG-encrypted agent-to-human comms
│
├── database/                     # Persistence layer
│   ├── __init__.py
│   ├── schema.py                 # SQL table definitions
│   └── agent_db.py               # SQLite operations
│
├── progression/                  # Agent progression system
│   ├── __init__.py
│   ├── xp_system.py              # XP calculation
│   └── levels.py                 # Level titles and milestones
│
├── safety/                       # Safety and rules
│   ├── __init__.py
│   └── rules.py                  # Session rules
│
├── utils/                        # Utility modules
│   ├── __init__.py
│   ├── formatting.py             # Terminal colors and formatting
│   ├── token_stats.py            # Token tracking and cost estimation
│   ├── rate_limiter.py           # API rate limiting
│   ├── context_optimizer.py      # Context window optimization
│   ├── prompt_compressor.py      # Prompt compression
│   └── xml_tool_parser.py        # Multi-format tool call parsing
│
├── models/                       # Model metadata
│   ├── __init__.py
│   └── metadata.py               # Model info and capabilities
│
├── tools/                        # Analysis tools
│   ├── __init__.py
│   ├── llmprep.py                # Codebase context preparation
│   └── build_analyzer.py         # Build system detection
│
├── workshop/                     # Dynamic analysis tools
│   ├── __init__.py
│   ├── chisel.py                 # Symbolic execution (angr)
│   ├── saw.py                    # Taint analysis
│   ├── plane.py                  # Source/sink enumeration
│   └── hammer.py                 # Live instrumentation (frida)
│
├── skills/                       # Agent skills system
│   ├── manifest.json             # Skill registry and metadata
│   ├── build.md                  # Silent build guidelines
│   ├── claude_build.md           # Security-focused builds
│   ├── reverse_engineering_expert.md
│   ├── cpp_refactoring_expert.md
│   ├── ida_pro_analysis_patterns.md
│   ├── c_modernization_expert.md
│   ├── cpp_modernization_expert.md
│   ├── python_agent_expert.md
│   └── x86_assembly_expert.md
│
└── docs/                         # Documentation
    ├── README.md                 # Documentation hub
    ├── api-providers.md          # API provider details
    ├── security.md               # Security report
    ├── features/                 # Feature documentation
    │   ├── sandbox.md
    │   ├── write-blocks.md
    │   ├── parsers.md
    │   └── README.md
    ├── references/               # Quick references
    │   ├── quick-reference.md
    │   └── README.md
    ├── workshop/                 # Workshop tool docs
    │   ├── quick-reference.md
    │   ├── benchmarks.md
    │   ├── security-audit.md
    │   ├── dependency-validation.md
    │   ├── test-results.md
    │   └── README.md
    └── archive/                  # Historical documentation
        ├── implementation-summaries/
        ├── pr-reports/
        └── README.md
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Request Flow                                │
└─────────────────────────────────────────────────────────────────────┘

User Input
    │
    ▼
┌─────────────────┐
│ Session         │
│ Preprocessor    │──► Token detection
│                 │──► Skill injection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Manager   │──► Select provider (Anthropic/OpenAI/xAI/etc)
│                 │──► Load model config
│                 │──► Add system prompt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Provider API │──► Send request
│                 │──► Stream response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tool Parser     │──► Parse XML/Bash/Code blocks
│                 │──► Extract tool calls
│                 │──► Deduplicate commands
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tool Runner     │──► Validate against whitelist
│                 │──► Check path security
│                 │──► Execute (sandboxed if enabled)
│                 │──► Capture output
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Conversation    │──► Append to history
│ History         │──► Format results
│                 │──► Update context
└────────┬────────┘
         │
         ▼
    Display to User
```

## Key Extension Points

### 1. Adding New AI Providers

**File:** `core/agent_manager.py`

To add a new provider (e.g., Ollama for local models):

```python
# In AgentManager._init_clients()

# Add at top of file:
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

# In _init_clients():
elif name == 'ollama' and HAS_OLLAMA:
    # Ollama runs locally, no API key needed
    self.clients[name] = ollama.Client(
        host=prov_config.get('base_url', 'http://localhost:11434')
    )

# In call_agent():
elif provider == 'ollama':
    resp = client.chat(
        model=model,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': full_prompt}
        ]
    )
    return resp['message']['content']
```

**Configuration (axe.yaml):**
```yaml
providers:
  ollama:
    enabled: true
    base_url: http://localhost:11434
    models:
      - llama2
      - codellama
      - mistral

agents:
  local:
    alias: [loc, ollama]
    provider: ollama
    model: codellama
    role: Local code assistant (no API costs)
    context_window: 4096
    capabilities: [text]
```

### 2. Adding Distributed Processing (Ray)

**New File:** `core/distributed.py`

```python
"""
Distributed AI processing with Ray.

Enables parallel agent execution across multiple machines.
"""

try:
    import ray
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

from typing import List, Dict, Any


@ray.remote
class DistributedAgent:
    """Ray actor for distributed agent execution."""
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.config = agent_config
        # Initialize agent-specific resources
        
    def process(self, prompt: str, context: str) -> str:
        """Process a prompt and return response."""
        # Agent-specific processing
        pass


class DistributedCoordinator:
    """Coordinates distributed agent execution."""
    
    def __init__(self, agents: List[Dict[str, Any]]):
        if not HAS_RAY:
            raise ImportError("Ray not installed. pip install ray")
        
        ray.init(ignore_reinit_error=True)
        self.actors = [
            DistributedAgent.remote(config) 
            for config in agents
        ]
    
    def parallel_process(self, prompts: List[str]) -> List[str]:
        """Process multiple prompts in parallel."""
        futures = [
            actor.process.remote(prompt, "")
            for actor, prompt in zip(self.actors, prompts)
        ]
        return ray.get(futures)
    
    def shutdown(self):
        """Shutdown Ray cluster."""
        ray.shutdown()
```

### 3. Adding New Workshop Tools

**File:** `workshop/__init__.py`

1. Create your tool in `workshop/my_tool.py`:

```python
"""
MyTool - Description of what it does.
"""

from typing import Dict, Any, Optional

class MyToolAnalyzer:
    """Tool description."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def analyze(self, target: str) -> Dict[str, Any]:
        """
        Analyze the target.
        
        Args:
            target: What to analyze
            
        Returns:
            Analysis results
        """
        results = {
            'status': 'completed',
            'findings': []
        }
        # Your analysis logic
        return results
```

2. Register in `workshop/__init__.py`:
```python
try:
    from .my_tool import MyToolAnalyzer
    HAS_MY_TOOL = True
except ImportError:
    HAS_MY_TOOL = False
```

3. Add CLI handler in `axe.py` (ChatSession.handle_workshop_command)

### 4. Adding New Token Optimization Strategies

**File:** `utils/context_optimizer.py`

```python
def my_optimization_strategy(
    messages: List[Message],
    max_tokens: int
) -> List[Message]:
    """
    Custom optimization strategy.
    
    Args:
        messages: Conversation history
        max_tokens: Token budget
        
    Returns:
        Optimized messages
    """
    # Your optimization logic
    return optimized_messages
```

## Design Principles

1. **Provider Abstraction**: All AI providers implement the same interface in `AgentManager.call_agent()`. New providers should follow this pattern.

2. **Configuration-Driven**: Features are enabled via `axe.yaml`. New features should support both YAML configuration and sensible defaults.

3. **Graceful Degradation**: Use try/except for optional dependencies. Features should degrade gracefully when dependencies are missing.

4. **Safety First**: All tool execution goes through `ToolRunner` with whitelist validation. New tools should integrate with this system.

5. **Persistence**: Agent state is stored in SQLite via `AgentDatabase`. New features needing persistence should add appropriate tables/columns.

## Future Enhancements

### Ollama Integration (Local Models)
- Zero API cost for development
- Privacy-sensitive operations
- Offline capability
- Custom fine-tuned models

### Ray Integration (Distributed AI)
- Parallel agent processing
- Horizontal scaling
- Multi-machine clusters
- GPU resource sharing

### Plugin System
- Dynamic tool loading
- Third-party extensions
- Custom provider plugins

## Contributing

When extending AXE:

1. Follow existing code patterns
2. Add type hints to all new functions
3. Write docstrings for public APIs
4. Add tests for new functionality
5. Update relevant documentation
