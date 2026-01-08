# AXE Architecture Diagrams

This directory contains architecture diagrams for the AXE codebase in GraphViz DOT format.

## Files

- `class_diagram.dot` - UML class diagram showing main classes and their relationships
- `module_dependencies.dot` - Module dependency graph showing how packages depend on each other
- `call_graph.dot` - Call flow diagram showing execution paths through the system

## Viewing Diagrams

### Online (No installation required)

1. Copy the contents of a `.dot` file
2. Visit [GraphViz Online](https://dreampuf.github.io/GraphvizOnline/)
3. Paste the DOT content to see the rendered diagram

### Command Line (Requires GraphViz)

```bash
# Install GraphViz
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Generate PNG images
dot -Tpng class_diagram.dot -o class_diagram.png
dot -Tpng module_dependencies.dot -o module_dependencies.png
dot -Tpng call_graph.dot -o call_graph.png

# Generate SVG (better quality)
dot -Tsvg class_diagram.dot -o class_diagram.svg
```

### VS Code

Install the "Graphviz (dot) language support for Visual Studio Code" extension to preview DOT files.

## Diagram Descriptions

### Class Diagram

Shows the main classes organized by package:

- **axe** (green): Main entry point classes
  - `ResponseProcessor` - Processes agent responses and executes code blocks
  - `ProjectContext` - Manages project context for agents
  - `SharedWorkspace` - Shared workspace for multi-agent collaboration
  - `CollaborativeSession` - Multi-agent collaborative sessions
  - `ChatSession` - Interactive chat session

- **core** (blue): Core components
  - `Config` - Configuration management
  - `AgentManager` - Agent connections and API calls
  - `ToolRunner` - Command execution with safety checks
  - `SharedContext` - Thread-safe shared state
  - `MultiAgentCoordinator` - Parallel agent orchestration

- **database** (orange): Persistence layer
  - `AgentDatabase` - SQLite database operations

- **managers** (purple): Agent lifecycle
  - `SleepManager` - Mandatory sleep system
  - `BreakSystem` - Agent break management
  - `DynamicSpawner` - Dynamic agent spawning
  - `EmergencyMailbox` - Encrypted human communication

- **utils** (cyan): Utility classes
  - `ContextOptimizer` - Context window optimization
  - `TokenStats` - Token usage statistics
  - `PromptCompressor` - Prompt compression

- **workshop** (peach): Analysis tools
  - `ChiselAnalyzer` - Symbolic execution
  - `SawTracker` - Taint analysis
  - `PlaneEnumerator` - Source/sink enumeration
  - `HammerInstrumentor` - Live instrumentation

### Module Dependencies

Shows how the main packages depend on each other:

- `axe.py` depends on all other packages (entry point)
- `core` depends on `utils` and `models`
- `managers` depends on `core`, `database`, and `utils`
- `database` depends on `progression`
- `workshop` depends on `utils`

### Call Graph

Shows the execution flow:

1. **Entry**: `main()` parses arguments and loads config
2. **Mode Selection**: 
   - Interactive mode → `ChatSession.run()`
   - Collaborative mode → `CollaborativeSession.start_session()`
   - Single command → `process_agent_message()`
3. **Processing**: Commands and messages are processed
4. **Tool Execution**: READ/EXEC/WRITE blocks are executed via `ToolRunner`
5. **Persistence**: Agent state is saved to database

## Updating Diagrams

When the codebase structure changes, update these diagrams to reflect:

1. New classes and their relationships
2. Changed module dependencies
3. Modified execution flows

The diagrams use standard DOT syntax. See [GraphViz documentation](https://graphviz.org/documentation/) for syntax reference.
