# Workshop Tools Quick Reference

## Overview

The Workshop module provides dynamic analysis tools for AXE, themed after woodworking implements. These tools enable advanced code analysis, vulnerability detection, and runtime monitoring.

## Tools

### Chisel - Symbolic Execution
**Purpose**: Analyze program paths symbolically to find constraints, branches, and vulnerabilities.

**Usage**:
```bash
/workshop chisel <binary_path> [function_name]
```

**Example**:
```bash
/workshop chisel ./vulnerable.exe main
```

**Output**: JSON with paths explored, constraints found, and potential vulnerabilities.

### Saw - Taint Analysis
**Purpose**: Track tainted data flow through code to identify injection vulnerabilities.

**Usage**:
```bash
/workshop saw "<python_code>"
```

**Example**:
```bash
/workshop saw "import os; os.system(input())"
```

**Output**: JSON with taint sources, sinks, flows, and vulnerability classifications.

### Plane - Source/Sink Enumeration
**Purpose**: Catalog all data sources and sinks in a codebase.

**Usage**:
```bash
/workshop plane <project_path>
```

**Example**:
```bash
/workshop plane .
```

**Output**: JSON with enumerated sources, sinks, and summary statistics.

### Hammer - Live Instrumentation
**Purpose**: Instrument running processes for real-time monitoring and analysis.

**Usage**:
```bash
/workshop hammer <process_name>
```

**Example**:
```bash
/workshop hammer python.exe
```

**Output**: Session ID for monitoring. Use Ctrl+C to stop.

## Management Commands

### History
View analysis history and past results.

```bash
/workshop history [tool_name]
```

**Examples**:
```bash
/workshop history          # All analyses
/workshop history chisel   # Chisel analyses only
```

### Statistics
View usage statistics and performance metrics.

```bash
/workshop stats [tool_name]
```

**Examples**:
```bash
/workshop stats           # All tools
/workshop stats saw       # Saw statistics only
```

## Configuration

Workshop tools are configured in `axe.yaml` under the `workshop` section:

```yaml
workshop:
  enabled: true
  chisel:
    max_paths: 1000          # Maximum paths to explore
    timeout: 30              # Analysis timeout in seconds
    find_targets: []         # Addresses to find (empty = auto-detect)
    avoid_targets: []        # Addresses to avoid
    memory_limit: 1024       # Memory limit in MB

  saw:
    max_depth: 10            # Maximum taint propagation depth
    confidence_threshold: 0.7 # Minimum confidence for reporting

  plane:
    exclude_patterns:        # Patterns to exclude from enumeration
      - __pycache__
      - .git
      - venv
      - node_modules
    max_files: 1000          # Maximum files to analyze

  hammer:
    monitoring_interval: 0.1 # Polling interval for monitoring
    max_sessions: 5          # Maximum concurrent instrumentation sessions
```

## Database Integration

All workshop analyses are automatically saved to the AXE database with:
- Analysis results and metadata
- Performance metrics (duration, success/failure)
- XP awards for agent progression
- Historical tracking for analysis improvement

## XP System

Workshop tools award XP to agents based on:
- **Base XP**: Fixed amount per tool usage
- **Quality Bonuses**: Additional XP for finding vulnerabilities, exploring paths, etc.
- **Performance**: Bonuses for successful analyses and comprehensive results

### XP Awards
- Chisel: 25 XP base + path/vulnerability bonuses
- Saw: 20 XP base + taint flow/vulnerability bonuses
- Plane: 15 XP base + enumeration coverage bonuses
- Hammer: 30 XP base + instrumentation success bonuses

## Dependencies

Install required packages:
```bash
pip install angr frida-python psutil
```

## Integration with Agents

Agents can use workshop tools programmatically:

```python
from workshop import ChiselAnalyzer, SawTracker

analyzer = ChiselAnalyzer()
result = analyzer.analyze_binary("target.exe")

tracker = SawTracker()
result = tracker.analyze_code("code_here")
```

## Safety Considerations

- Workshop tools respect AXE's directory access controls
- Instrumentation requires appropriate permissions
- Symbolic execution may be resource-intensive
- Always review tool outputs before acting on findings
- Database persistence ensures analysis history is maintained across sessions

## Validation & Quality Assurance

The Workshop module has undergone comprehensive validation:

- **[Performance Benchmarks](workshop_benchmarks.md)**: Detailed performance analysis and optimization recommendations
- **[Security Audit](workshop_security_audit.md)**: Complete security assessment with all findings resolved
- **[Dependency Validation](workshop_dependency_validation.md)**: Compatibility testing and integration verification
- **[Test Results](workshop_test_results.md)**: Full test suite execution with 93% code coverage

All validation documents confirm the Workshop tools are production-ready with enterprise-grade security and performance characteristics.