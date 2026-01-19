# AXE Workshop Tools

The Workshop provides dynamic analysis and security tools for reverse engineering, binary analysis, and code security auditing.

## Workshop Tools

### Core Tools

#### **Chisel** (Symbolic Execution)
Powered by angr for symbolic execution and constraint solving
- Path exploration
- Symbolic memory analysis
- Constraint solving
- State management

#### **Hammer** (Live Instrumentation)
Powered by Frida for dynamic instrumentation
- Runtime hooking
- Function interception
- Memory manipulation
- Live code modification

#### **Saw** (Taint Analysis)
Track data flow and information leaks
- Source-to-sink tracking
- Information flow analysis
- Vulnerability detection
- Data provenance

#### **Plane** (Source/Sink Enumeration)
Enumerate potential security sources and sinks
- Entry point discovery
- API surface mapping
- Vulnerability surface analysis
- Attack vector identification

## Documentation

### [quick-reference.md](quick-reference.md)
Complete guide to Workshop tools:
- Tool descriptions
- Command syntax
- Usage examples
- Integration patterns

### [benchmarks.md](benchmarks.md)
Performance metrics and benchmarks:
- Tool performance data
- Comparison metrics
- Resource usage
- Optimization recommendations

### [security-audit.md](security-audit.md)
Security audit results:
- Vulnerability findings
- Security recommendations
- Remediation steps
- Best practices

### [dependency-validation.md](dependency-validation.md)
Dependency validation reports:
- Required dependencies
- Version requirements
- Installation verification
- Compatibility matrix

### [test-results.md](test-results.md)
Workshop tool test results:
- Unit test results
- Integration tests
- Coverage reports
- Known issues

## Quick Start

### Accessing Workshop Tools

```bash
# From AXE main interface
/workshop

# Run specific tool
/workshop chisel <target>
/workshop hammer <binary>
/workshop saw <source_file>
/workshop plane <codebase>
```

### Basic Usage Examples

**Symbolic Execution with Chisel:**
```python
chisel analyze binary.exe --entry main --depth 10
```

**Dynamic Instrumentation with Hammer:**
```python
hammer hook process.exe --function malloc --action trace
```

**Taint Analysis with Saw:**
```python
saw trace input.c --source user_input --sink system_call
```

**Surface Enumeration with Plane:**
```python
plane enumerate ./src --find-sources --find-sinks
```

## Requirements

Workshop tools require additional dependencies:

```bash
# Install all workshop dependencies
pip install angr frida pwntools

# Verify installation
python -c "import angr; import frida; import pwn"
```

See [dependency-validation.md](dependency-validation.md) for detailed requirements.

## Use Cases

### Reverse Engineering
- Binary analysis
- Decompiler output processing
- Protocol reverse engineering
- Malware analysis (in sandbox!)

### Security Auditing
- Vulnerability discovery
- Code review automation
- Exploit development
- Penetration testing

### Development
- Debugging complex issues
- Performance analysis
- Memory leak detection
- Code coverage analysis

## Related Documentation

- **[../features/sandbox.md](../features/sandbox.md)** - Safe execution environment
- **[../references/quick-reference.md](../references/quick-reference.md)** - General AXE commands
- **[../security.md](../security.md)** - Security best practices
- **[../../ARCHITECTURE.md](../../ARCHITECTURE.md)** - System architecture

## Safety Notes

⚠️ **Always use Workshop tools in a sandboxed environment**

- Use `--sandbox` flag when analyzing untrusted binaries
- Review security audit results regularly
- Keep dependencies updated
- Follow security best practices

## Contributing

When adding Workshop documentation:
- Document all tool options
- Include safety warnings
- Provide realistic examples
- Cross-reference related tools
- Update dependency requirements

---

For the complete documentation index, see [../README.md](../README.md)
