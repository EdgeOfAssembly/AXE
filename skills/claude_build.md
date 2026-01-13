# Claude Security-Focused Build Skill

## Overview

This skill provides **Claude-specific** guidelines for silent builds during security auditing and code review. Claude's role as a security auditor requires capturing only **critical security-relevant output** while minimizing noise from routine build processes.

## Security Auditing Workflow

When performing security audits, Claude should:

1. **Use silent builds** to minimize log noise
2. **Capture only security-relevant output** (warnings, errors, security tool findings)
3. **Re-run with verbose output** when investigating specific vulnerabilities
4. **Document security findings** clearly and concisely

## Silent Security Builds

### Core Build Systems

All standard build systems should use silent flags during security audits:

```bash
# Make
make -s V=0 all

# CMake
cmake --build build -- VERBOSE=0

# Autoconf/configure
./configure --quiet --enable-silent-rules

# Meson
meson setup --quiet builddir
meson compile -C builddir

# Gradle
gradle --quiet build

# Maven
mvn -q package

# SCons
scons -Q
```

### Security-Specific Tools

Many security analysis tools also support quiet modes:

#### Valgrind (Memory Analysis)

**Silent mode:**
```bash
valgrind --quiet ./program
valgrind -q ./program              # Short form
```

**When to use verbose:**
```bash
valgrind --leak-check=full ./program    # Detailed memory leak analysis
valgrind -v ./program                   # Verbose mode for debugging
```

**Usage in security audit:**
```
```EXEC
# Quick check for memory issues (silent)
valgrind --quiet --leak-check=yes ./suspicious_binary

# If issues found, re-run with full details:
valgrind --leak-check=full --show-leak-kinds=all ./suspicious_binary
```
```

#### Cppcheck (Static Analysis)

**Silent mode:**
```bash
cppcheck --quiet source.c              # Only show findings
cppcheck -q --enable=warning source.c  # Warnings only
```

**When to use verbose:**
```bash
cppcheck --verbose --enable=all source.c    # Full analysis with explanations
cppcheck -v source.c                        # Verbose mode
```

**Usage in security audit:**
```
```EXEC
# Run static analysis quietly
cppcheck --quiet --enable=warning,style,performance src/

# If critical issues found, re-run with full details:
cppcheck --verbose --enable=all src/
```
```

#### AddressSanitizer (ASan)

**Silent mode:**
```bash
# Compile with ASan (minimal output)
gcc -fsanitize=address -g -o program source.c 2>&1 | grep -E "(error|warning)"

# Run with minimal ASan output
ASAN_OPTIONS=verbosity=0 ./program
```

**When to use verbose:**
```bash
# Detailed ASan output for investigation
ASAN_OPTIONS=verbosity=1 ./program
```

**Usage in security audit:**
```
```EXEC
# Compile with ASan and run tests silently
gcc -fsanitize=address -g -o test_binary test.c
ASAN_OPTIONS=verbosity=0 ./test_binary

# If issues detected, re-run with verbose output:
ASAN_OPTIONS=verbosity=1 ./test_binary
```
```

#### Clang Static Analyzer

**Silent mode:**
```bash
scan-build --status-bugs -o reports make -s
```

**When to use verbose:**
```bash
scan-build -v --status-bugs -o reports make    # Verbose analysis
```

**Usage in security audit:**
```
```EXEC
# Run Clang static analyzer quietly
scan-build --status-bugs -o scan-results make -s clean all

# Review findings
cat scan-results/*/report-*.html
```
```

#### Flawfinder (C/C++ Security Scanner)

**Silent mode:**
```bash
flawfinder --quiet --minlevel=3 src/    # Only show level 3+ issues
```

**When to use verbose:**
```bash
flawfinder --minlevel=0 src/            # Show all findings
```

**Usage in security audit:**
```
```EXEC
# Quick security scan (high severity only)
flawfinder --quiet --minlevel=3 src/

# If issues found, run full scan:
flawfinder --minlevel=0 --html src/ > security_report.html
```
```

## Security Audit Workflow Example

### Phase 1: Initial Silent Build

```
I'll perform a security audit of the codebase. Starting with a silent build to check for compilation warnings:

```EXEC
# Configure with security flags
./configure --quiet --enable-silent-rules CFLAGS="-Wall -Wextra -Werror"

# Build silently
make -s all
```

Build completed successfully with no warnings.
```

### Phase 2: Static Analysis (Silent)

```
Running static analysis tools quietly to identify potential vulnerabilities:

```EXEC
# Cppcheck for C/C++ issues
cppcheck --quiet --enable=warning,performance,portability src/

# Flawfinder for security issues
flawfinder --quiet --minlevel=3 src/
```

Found 2 potential issues:
- Buffer overflow in parse_input() (src/parser.c:45)
- Format string vulnerability in log_message() (src/logger.c:78)
```

### Phase 3: Detailed Investigation (Verbose)

```
Investigating the buffer overflow with verbose output:

```EXEC
# Re-run cppcheck with full details
cppcheck --verbose --enable=all src/parser.c

# Compile with AddressSanitizer for runtime detection
gcc -fsanitize=address -g -o parser_test src/parser.c src/test_parser.c
ASAN_OPTIONS=verbosity=1 ./parser_test
```

Confirmed: Buffer overflow occurs when input exceeds 256 bytes...
```

### Phase 4: Security Report

```
## Security Audit Report

**SEVERITY: HIGH**

### Vulnerability 1: Buffer Overflow in parse_input()

**Location:** src/parser.c:45
**Type:** CWE-120 (Buffer Copy without Checking Size of Input)

**Details:**
The parse_input() function uses strcpy() without bounds checking...

**Recommendation:**
Replace strcpy() with strncpy() or use safer alternatives like strlcpy()...

**Verified with:**
- Cppcheck static analysis
- AddressSanitizer runtime detection
- Manual code review
```

## Token Savings in Security Audits

Security audits benefit significantly from silent builds:

| Audit Phase | Verbose Tokens | Silent Tokens | Savings |
|-------------|----------------|---------------|---------|
| Initial build | 3000 | 200 | 93% |
| Static analysis | 5000 | 500 | 90% |
| Runtime testing | 4000 | 600 | 85% |
| **Total** | **12000** | **1300** | **89%** |

## Best Practices for Security Audits

### 1. Start Silent, Investigate Verbose

Always begin with silent builds to get a clean overview:
```
✓ GOOD:
```EXEC
cppcheck --quiet --enable=warning src/
```

Then drill down with verbose output when issues are found:
```EXEC
cppcheck --verbose --enable=all src/vulnerable_file.c
```

✗ BAD:
```EXEC
cppcheck --verbose --enable=all src/    # Too much noise from the start
```
```

### 2. Focus on Security-Relevant Output

Filter output to show only security findings:
```
```EXEC
# Good: Only security warnings
make -s CFLAGS="-Wall -Wextra" 2>&1 | grep -E "(warning|error)"

# Good: Only high-severity findings
flawfinder --quiet --minlevel=3 src/
```
```

### 3. Document Severity Levels

Always flag findings with severity levels:
```
## Security Findings

**CRITICAL:** Buffer overflow in authentication module (src/auth.c:123)
**HIGH:** SQL injection in query builder (src/db.c:456)
**MEDIUM:** Potential race condition in thread pool (src/pool.c:789)
**LOW:** Weak random number generation (src/rand.c:34)
```

### 4. Use Quiet Flags in CI/CD Security Checks

In security-focused CI/CD pipelines:
```yaml
# .github/workflows/security.yml
- name: Static Analysis
  run: |
    cppcheck --quiet --enable=all --error-exitcode=1 src/
    
- name: Dynamic Analysis
  run: |
    make -s sanitize
    ASAN_OPTIONS=verbosity=0 ./test_suite
```

### 5. Combine Multiple Security Tools Quietly

Run multiple security tools in sequence, all with quiet flags:
```
```EXEC
# Comprehensive security scan with minimal noise
cppcheck --quiet --enable=warning src/ && \
flawfinder --quiet --minlevel=2 src/ && \
valgrind --quiet --leak-check=yes ./program && \
echo "All security checks passed"
```
```

## Security Tool Quick Reference

| Tool | Silent Flag | Verbose Flag | Use Case |
|------|-------------|--------------|----------|
| **Valgrind** | `--quiet`, `-q` | `-v`, `--verbose` | Memory safety |
| **Cppcheck** | `--quiet` | `--verbose` | Static analysis |
| **ASan** | `ASAN_OPTIONS=verbosity=0` | `verbosity=1` | Runtime memory errors |
| **scan-build** | `--status-bugs` | `-v` | Clang static analysis |
| **Flawfinder** | `--quiet` | `--minlevel=0` | Security vulnerability scanning |
| **Bandit** (Python) | `-q` | `-v` | Python security linting |
| **Brakeman** (Ruby) | `-q` | `--debug` | Rails security scanner |
| **SonarQube** | `sonar.log.level=WARN` | `DEBUG` | Multi-language security analysis |

## Integration with AGENTS.md

When collaborating with other agents on security-focused tasks, Claude should:

1. **Lead security reviews** using silent builds
2. **Share only critical findings** with other agents
3. **Request verbose output** only when diagnosing specific vulnerabilities
4. **Summarize security status** concisely for other agents

Example collaboration:
```
@gpt: "I've refactored the authentication module. Can you review it for security issues?"

@claude:
I'll perform a security audit of the authentication module using silent builds to minimize log noise:

```EXEC
# Static analysis (silent)
cppcheck --quiet --enable=warning src/auth.c

# Runtime analysis (silent)
gcc -fsanitize=address -g -o auth_test src/auth.c test/test_auth.c
ASAN_OPTIONS=verbosity=0 ./auth_test
```

**Security Review Summary:**
- ✓ No buffer overflows detected
- ✓ No format string vulnerabilities
- ✓ Proper input validation
- ⚠️  MEDIUM: Consider adding rate limiting to prevent brute force attacks

The refactoring looks secure. I recommend adding the rate limiting enhancement.
```

## Common Security Build Patterns

### Pattern 1: Hardening Flags (Silent Build)

```bash
# Compile with security hardening flags, silent output
make -s CFLAGS="-Wall -Wextra -Werror -D_FORTIFY_SOURCE=2 -fstack-protector-strong -fPIE -O2"
```

### Pattern 2: Security Tool Chain (Silent)

```bash
# Run complete security tool chain silently
cppcheck --quiet --enable=all src/ && \
flawfinder --quiet --minlevel=2 src/ && \
make -s clean all && \
valgrind --quiet --leak-check=yes ./program
```

### Pattern 3: Regression Testing (Silent)

```bash
# Security regression tests (quiet unless failures)
pytest -q tests/security/ --tb=short
```

### Pattern 4: Fuzzing Setup (Silent)

```bash
# Build with AFL fuzzing support (silent)
CC=afl-gcc make -s all
```

## Summary

As Claude, the security auditor, you should:

1. **Default to silent builds** to minimize log noise
2. **Use quiet flags** for security tools (valgrind, cppcheck, etc.)
3. **Capture only critical output** during initial scans
4. **Re-run with verbose output** when investigating specific vulnerabilities
5. **Document findings** with clear severity levels (CRITICAL, HIGH, MEDIUM, LOW)
6. **Preserve context** by keeping shared collaboration notes clean

Remember: **Silent builds → clearer security findings → better audits → safer code**

## References

- **skills/build.md**: General silent builds skill for all agents
- **axe.yaml**: Claude agent configured with security-focused BUILD GUIDELINES
- Security tool documentation:
  - [Valgrind Manual](https://valgrind.org/docs/manual/)
  - [Cppcheck Manual](https://cppcheck.sourceforge.io/)
  - [AddressSanitizer Documentation](https://github.com/google/sanitizers/wiki/AddressSanitizer)
