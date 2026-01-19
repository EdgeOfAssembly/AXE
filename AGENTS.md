# AGENTS.md for AXE

## Project Overview

**AXE (Agent eXecution Engine)** is a terminal-based multiagent coding assistant designed for C, C++, Python, and reverse engineering tasks. It orchestrates multiple specialized AI agents (Claude, GPT, Llama, Grok, etc.) to collaborate on complex coding, debugging, security auditing, and binary analysis tasks.

## Development Environment

### Requirements
- **Python 3.9+** (tested on Python 3.12)
- See `requirements.txt` for dependencies

### Installation
```bash
# Clone the repository
git clone https://github.com/EdgeOfAssembly/AXE.git
cd AXE

# Install dependencies
pip install -r requirements.txt
```

### Running AXE
```bash
# Basic usage
python axe.py

# With specific agent
python axe.py --agent claude

# Multi-agent collaboration
python axe.py --collab
```

## Testing

### Running Tests
```bash
# Run all tests
python3 tests/test_<module_name>.py

# Example: Test skills manager
python3 tests/test_skills_manager.py

# Example: Test Anthropic features
python3 tests/test_anthropic_features.py
```

### Test Requirements
- All tests must pass before PR submission
- New features must include corresponding tests
- Target 90%+ coverage for new code

## Coding Conventions

### Python Style
- **Follow PEP 8** for Python code style
- **Use type hints** for all function signatures
- **Extensive docstrings** required (Google or NumPy style)
- **All new code must have tests**

### Example
```python
def process_skill(name: str, content: str) -> Dict[str, Any]:
    """
    Process a skill file and extract metadata.
    
    Args:
        name: The skill name (without extension)
        content: The raw skill content from markdown file
        
    Returns:
        Dictionary containing skill metadata and content
    """
    # Implementation here
    pass
```

### File Naming
- Use **lowercase_snake_case** for all Python modules and skill files
- Examples: `skills_manager.py`, `reverse_engineering_expert.md`

## Skills System

AXE features a comprehensive Agent Skills system that provides domain-specific expertise without prompt bloat.

### Skills Directory Structure
```
skills/
├── manifest.json                    # Central skill registry
├── build.md                         # Silent build guidelines
├── claude_build.md                  # Security-focused build guidelines
├── reverse_engineering_expert.md   # Binary analysis & RE patterns
├── cpp_refactoring_expert.md       # C++ refactoring patterns
├── ida_pro_analysis_patterns.md    # Decompiler output analysis
├── c_modernization_expert.md       # Modern C standards (C11/C17/C23)
├── cpp_modernization_expert.md     # Modern C++ (C++20/23/26)
├── python_agent_expert.md          # Python best practices
└── x86_assembly_expert.md          # x86/x64 assembly analysis
```

### Creating New Skills
1. **Use lowercase_snake_case** for filenames
2. Each skill needs:
   - `SKILL_NAME.md` - The skill content (instructions, patterns, workflows)
   - Entry in `skills/manifest.json` with metadata
3. Include in manifest:
   - Skill name and description
   - Keywords for auto-activation
   - Provider compatibility (anthropic, all, etc.)
   - Optional: tool integrations

### Example Skill Template
```markdown
# Skill Name

Brief description of the skill's expertise.

## Core Principles
- Key principle 1
- Key principle 2

## Workflow Template
1. Step 1
2. Step 2
3. Step 3

## Best Practices
- Best practice 1
- Best practice 2
```

## Build Guidelines

AXE emphasizes **silent builds** to reduce token consumption and improve log readability.

### Default Build Approach
Use silent/quiet flags for all build systems:
- **Make**: `make -s V=0` or `make --silent`
- **CMake**: `cmake --build . -- VERBOSE=0`
- **Ninja**: Silent by default; use `-v` only for debugging
- **Gradle**: `gradle --quiet` or `gradle -q`
- **Maven**: `mvn -q` or `mvn --quiet`

### When to Use Verbose Output
- Build fails and you need diagnostic information
- Debugging build configuration issues
- Security tool generates false positives

See `skills/build.md` for comprehensive build system guidelines.

## Architecture

### Core Components
- **`core/agent_manager.py`**: Manages LLM provider connections and API calls
- **`core/skills_manager.py`**: Loads, discovers, and injects agent skills
- **`core/multiprocess.py`**: Multi-agent coordination and communication
- **`core/tool_runner.py`**: Executes READ/EXEC/WRITE blocks from agent responses
- **`core/sandbox.py`**: Bubblewrap-based sandboxed command execution

### Configuration Files
- **`axe.yaml`**: Agent definitions, system prompts, tools, directories
- **`models.yaml`**: Model metadata, token limits, capabilities
- **`skills/manifest.json`**: Skill registry and metadata

## Contributing

### Pull Request Process
1. Create feature branch: `git checkout -b feature/my-feature`
2. Implement changes with tests
3. Run all tests to ensure they pass
4. Submit PR with clear description of changes
5. Address code review feedback

### Code Review Checklist
- [ ] All tests pass
- [ ] New features have tests
- [ ] Code follows PEP 8
- [ ] Type hints present
- [ ] Docstrings added
- [ ] No breaking changes (or documented if necessary)

## Security Considerations

- **Sandbox Mode**: Enable in `axe.yaml` for isolated command execution
- **Input Validation**: All user inputs and LLM outputs are validated
- **Tool Restrictions**: Configurable tool blacklists and directory restrictions
- **API Key Management**: Never commit API keys; use environment variables

## Additional Resources

- **Architecture**: See `ARCHITECTURE.md` for system design
- **API Providers**: See `docs/api-providers.md` for LLM provider details
- **Workshop Tools**: See `docs/workshop/quick-reference.md` for Chisel, Hammer, Saw, Plane
- **Quick Reference**: See `docs/references/quick-reference.md` for commands and patterns

## Contact & Support

- **GitHub Issues**: https://github.com/EdgeOfAssembly/AXE/issues
- **Documentation**: See `docs/` directory
- **Quick Reference**: See `QUICK_REFERENCE.md`

---

*This file follows the [agents.md](https://agents.md/) standard for AI agent collaboration.*
