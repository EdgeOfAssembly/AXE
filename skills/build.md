# Silent Builds Skill

## Overview

This skill provides guidelines for using silent/quiet compilation and configuration flags across multiple build systems. By defaulting to silent builds, agents can achieve **50-90% token savings** in log-related output while preserving build functionality.

## Why Silent Builds?

Build systems can generate verbose output that consumes hundreds or thousands of tokens per invocation. When build logs are included in LLM prompts or agent collaborations, this verbosity:

- **Wastes tokens**: Verbose compiler output rarely contains actionable information
- **Obscures errors**: Critical error messages get lost in noise
- **Slows iteration**: More output means slower agent processing
- **Costs money**: Every token sent to an LLM has a cost

Silent builds solve this by:
- Showing only warnings, errors, and critical output
- Preserving the ability to re-run with verbose output when debugging
- Reducing log size by 50-90% in typical projects

## Token Savings Estimates

| Build System | Typical Verbose Output | Silent Output | Savings |
|--------------|------------------------|---------------|---------|
| Make (large) | 5000-10000 tokens | 500-1000 tokens | 80-90% |
| CMake | 2000-4000 tokens | 200-500 tokens | 75-87% |
| Maven | 3000-6000 tokens | 300-800 tokens | 73-90% |
| Gradle | 2500-5000 tokens | 300-700 tokens | 76-88% |

## Supported Build Systems

### Make

**Silent flags:**
```bash
make -s          # Short form: silent
make --silent    # Long form: silent
make V=0         # Verbose level 0 (common in kernel builds)
make -s V=0      # Combine both for maximum silence
```

**Usage in EXEC blocks:**
```
```EXEC
make -s all
```
```

**When to use verbose:**
```bash
make V=1         # When build fails, retry with verbose output
make VERBOSE=1   # Alternative verbose flag in some projects
```

### Autoconf/Configure

**Silent flags:**
```bash
./configure --quiet                    # Suppress most output
./configure --enable-silent-rules      # Enable silent make rules
./configure --quiet --enable-silent-rules  # Recommended combination
```

**Usage in EXEC blocks:**
```
```EXEC
./configure --quiet --enable-silent-rules --prefix=/usr/local
```
```

**When to use verbose:**
```bash
./configure --verbose    # When configure fails, retry with verbose
```

### CMake

**Silent flags:**
```bash
cmake -S . -B build                    # CMAKE_VERBOSE_MAKEFILE=OFF (default)
cmake --build build -- VERBOSE=0       # Explicit silent build
cmake --build build --quiet            # Quiet mode (CMake 3.x+)
```

**Usage in EXEC blocks:**
```
```EXEC
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -- VERBOSE=0
```
```

**When to use verbose:**
```bash
cmake --build build -- VERBOSE=1       # When build fails
make -C build VERBOSE=1                # Alternative verbose syntax
```

### Meson

**Silent flags:**
```bash
meson setup --quiet builddir           # Quiet setup
meson compile -C builddir              # Ninja is quiet by default
```

**Usage in EXEC blocks:**
```
```EXEC
meson setup --quiet builddir
meson compile -C builddir
```
```

**When to use verbose:**
```bash
meson setup builddir                   # Normal output for debugging
meson compile -C builddir -v           # Verbose compilation
```

### Ninja

**Default behavior:**
Ninja is **silent by default**, showing only errors and warnings.

**Usage in EXEC blocks:**
```
```EXEC
ninja -C build
```
```

**When to use verbose:**
```bash
ninja -v -C build    # Verbose output for debugging
```

### Gradle

**Silent flags:**
```bash
gradle --quiet build       # Short form
gradle -q build            # Even shorter
gradle -q test            # Quiet tests
```

**Usage in EXEC blocks:**
```
```EXEC
gradle --quiet build
```
```

**When to use verbose:**
```bash
gradle build              # Normal output
gradle --info build       # More detailed output
gradle --debug build      # Maximum verbosity for debugging
```

### Maven

**Silent flags:**
```bash
mvn --quiet package        # Long form
mvn -q package            # Short form
mvn -q clean install      # Quiet clean + install
```

**Usage in EXEC blocks:**
```
```EXEC
mvn -q clean package
```
```

**When to use verbose:**
```bash
mvn package               # Normal output
mvn -X package            # Debug output when build fails
```

### SCons

**Silent flags:**
```bash
scons -Q                  # Quiet mode (suppress "scons: Reading/Building" messages)
scons -s                  # Silent mode (even quieter)
```

**Usage in EXEC blocks:**
```
```EXEC
scons -Q
```
```

**When to use verbose:**
```bash
scons                     # Normal output
scons --debug=explain     # Explain why targets are rebuilt
```

## Integration with axe.yaml

All agents in AXE have been configured with BUILD GUIDELINES in their system prompts. These guidelines instruct agents to:

1. **Default to silent builds** in all EXEC blocks
2. **Retry with verbose output** if a build fails and diagnostics are needed
3. **Preserve context** by minimizing log noise

Example from agent system prompt:
```
BUILD GUIDELINES:

To reduce token consumption in build logs, always use silent/quiet flags:

- Make: `make -s V=0` or `make --silent`
- CMake: `cmake --build . -- VERBOSE=0`
- Maven: `mvn -q` or `mvn --quiet`
- Gradle: `gradle --quiet` or `gradle -q`

If a build fails, retry with verbose output to diagnose issues.
```

## Integration with Collaborations

When multiple agents collaborate on a project, silent builds are especially important:

1. **Shared context**: Build logs appear in the shared collaboration notes
2. **Token budget**: Collaborations have a combined token limit across all agents
3. **Clarity**: Silent builds make it easier for agents to see what others have done

Example collaboration workflow:
```bash
# Start collaboration with silent builds enabled
/collab gpt,claude ./project 30 "Refactor build system"

# Agent GPT:
```EXEC
cmake --build build -- VERBOSE=0
```

# Agent Claude reviews the (minimal) output and continues
```

## Best Practices

### 1. Always Use Silent Flags First

When building code in an EXEC block, always use silent flags:
```
✓ GOOD:
```EXEC
make -s all
```

✗ BAD:
```EXEC
make all
```
```

### 2. Retry with Verbose on Failure

If a build fails, explain that you're retrying with verbose output:
```
The build failed. Let me retry with verbose output to diagnose:

```EXEC
make V=1 all
```
```

### 3. Document Your Choices

When choosing build flags, briefly explain why:
```
I'll use silent builds to minimize log output:

```EXEC
gradle -q build
```
```

### 4. Combine Multiple Silent Flags

When unsure, combine multiple silent flags for maximum quietness:
```
```EXEC
make -s V=0 --no-print-directory
```
```

### 5. Test Silently, Debug Verbosely

Run tests silently by default, but add verbosity when diagnosing failures:
```
```EXEC
pytest -q                    # Quiet tests
```

# If tests fail:
```EXEC
pytest -v                    # Verbose test output
```
```

## Common Pitfalls

### ❌ Don't Remove All Output

Silent builds should still show:
- **Errors**: Critical failures that stop the build
- **Warnings**: Potential issues in the code
- **Progress**: High-level status (e.g., "Building target X")

### ❌ Don't Assume Silence Means Success

Always check the exit code:
```
```EXEC
make -s all && echo "Build succeeded" || echo "Build failed"
```
```

### ❌ Don't Use Verbose by Default

Verbose output should be the exception, not the rule. Only use it when:
- A build has failed and you need diagnostics
- The user specifically requested detailed output
- You're debugging a build system configuration issue

## Examples

### Example 1: C++ Project with CMake

```
```EXEC
# Configure with quiet flags
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# Build silently
cmake --build build -- VERBOSE=0
```

# If build fails, retry with verbose:
```EXEC
cmake --build build -- VERBOSE=1
```
```

### Example 2: Java Project with Maven

```
```EXEC
# Clean and build quietly
mvn -q clean package

# Run tests quietly
mvn -q test
```

# If tests fail:
```EXEC
mvn test
```
```

### Example 3: Python Project with Make

```
```EXEC
# Install dependencies silently
make -s install-deps

# Run tests silently
make -s test
```

# If tests fail:
```EXEC
make test V=1
```
```

### Example 4: Multi-Agent Collaboration

```
@boss: "Team, refactor the build system to use CMake"

@gpt:
I'll set up the CMake build with silent flags to minimize log noise:

```EXEC
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -- VERBOSE=0
```

Build succeeded. The new CMake configuration is ready for review.

@claude:
Reviewing @gpt's work. I'll run a security-focused build check:

```EXEC
cmake --build build --target security-check -- VERBOSE=0
```

All security checks passed. The refactoring looks good.
```

## Summary

Silent builds are a best practice for:
- **Token efficiency**: Save 50-90% on build log tokens
- **Clarity**: Focus on errors and warnings, not noise
- **Collaboration**: Keep shared context clean and readable
- **Cost**: Reduce API costs by minimizing log verbosity

Remember: **Silent by default, verbose when debugging.**

## References

- **axe.yaml**: All agents configured with BUILD GUIDELINES
- **skills/claude_build.md**: Claude-specific security-focused build guidelines
- **AGENTS.md** (if exists): Integration notes for multi-agent workflows
