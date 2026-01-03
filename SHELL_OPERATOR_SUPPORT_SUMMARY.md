# Shell Operator Support Implementation Summary

## Overview
This document summarizes the shell operator support implementation in the `ToolRunner` class (`axe.py`), which resolves issues where shell commands with operators were incorrectly rejected due to simple string splitting.

## Problem Addressed
Previously, the `ToolRunner.is_tool_allowed()` method used simple `cmd.split()` which broke on shell features:
- **Pipes** (`|`) - Treated as command names
- **Logical operators** (`&&`, `||`) - Treated as command names
- **Redirects** (`>`, `>>`, `<`, `2>&1`) - Treated as command names
- **Heredocs** (`<< EOF`) - Content parsed as commands (causing errors like "Tool '-' not in whitelist", "Tool '1.' not in whitelist")

## Solution Implemented

### 1. Class Constants (Lines 1121-1125)
```python
class ToolRunner:
    # Shell operators that connect commands
    SHELL_OPERATORS = {'|', '&&', '||', ';'}
    
    # Redirect operators (not security risks, just I/O)
    REDIRECT_OPERATORS = {'>', '>>', '<', '2>', '2>>', '&>', '2>&1'}
```

### 2. `_strip_heredoc_content(cmd: str) -> str` (Lines 1135-1204)
- Removes heredoc content before parsing to prevent content like markdown lists from being treated as commands
- Handles: `<< EOF`, `<< 'EOF'`, `<< "EOF"`, `<<- EOF`, `<<< "string"`
- **CRITICAL**: For validation only, never used for execution

### 3. `_extract_commands_from_shell(cmd: str) -> List[str]` (Lines 1206-1268)
- Extracts actual command names from complex shell syntax
- Calls `_strip_heredoc_content()` first
- Splits on shell operators (`|`, `&&`, `||`, `;`)
- Skips redirect operators and their targets
- Skips environment variable assignments (`VAR=value`)
- **Edge case fixes**:
  - Strips parentheses from subshells: `(ls)` → `['ls']`
  - Handles redirects without spaces: `grep<input` → `['grep']`

### 4. `_needs_shell(cmd: str) -> bool` (Lines 1270-1286)
- Checks if command needs `shell=True` execution
- Detects: shell operators, redirects, command substitution, heredocs

### 5. Updated `is_tool_allowed(cmd: str)` (Lines 1288-1372)
- Uses `_extract_commands_from_shell()` to get actual command names
- Validates each command against whitelist
- Checks forbidden paths in full command

### 6. Updated `run(cmd: str, ...)` (Lines 1374-1459)
- Uses `_needs_shell()` to determine execution mode
- If shell features detected: `shell=True, cwd=self.project_dir`
- Otherwise: `shlex.split()` with `shell=False` (safer)

## Edge Cases Fixed

### 1. Subshells with Parentheses
**Before**: `(ls | grep)` → Commands: `['(ls', 'grep']` → **FAILED**
**After**: `(ls | grep)` → Commands: `['ls', 'grep']` → **ALLOWED**

### 2. Redirects Without Spaces
**Before**: `grep<input` → Commands: `['grep<input']` → **FAILED**
**After**: `grep<input` → Commands: `['grep']` → **ALLOWED**

### 3. Nested Subshells
**Before**: `((ls))` → Commands: `['((ls))']` → **FAILED**
**After**: `((ls))` → Commands: `['ls']` → **ALLOWED**

## Test Coverage

### Original Test Suite (`test_tool_runner.py`)
- ✅ Simple commands (ls, grep)
- ✅ Pipes (|)
- ✅ Logical operators (&&, ||)
- ✅ Redirects (>, >>, <, 2>&1)
- ✅ Heredocs with markdown content
- ✅ Complex combinations
- ✅ Security checks (non-whitelisted commands, forbidden paths)
- ✅ Integration tests with actual execution

**Result**: 10/10 test suites passed

### Edge Case Test Suite (`test_tool_runner_edge_cases.py`)
- ✅ Subshells: `(ls)`, `((ls))`, `(ls | grep)`
- ✅ Redirects without spaces: `grep<input`, `grep>output`
- ✅ Complex combinations: `(grep<input | head>output)`

**Result**: 3/3 test suites passed

## Security Maintained
- ✅ Non-whitelisted commands still blocked
- ✅ Forbidden paths still blocked (even in pipes/subshells)
- ✅ All security checks pass

## Commands Now Working

### Previously Failing (from problem statement):
1. ✅ `cat > notes.md << 'EOF'` with markdown content
2. ✅ `grep pattern file.py | head -20`
3. ✅ `ls -la && grep test`
4. ✅ `grep pattern file.txt || ls`
5. ✅ `grep pattern > output.txt`

### Edge Cases (newly fixed):
1. ✅ `(ls)` - Simple subshell
2. ✅ `(ls | grep test)` - Subshell with pipe
3. ✅ `grep<input` - Input redirect without space
4. ✅ `grep>output` - Output redirect without space
5. ✅ `((ls))` - Nested subshell

## Implementation Notes

1. **Heredoc stripping is for validation only**: The original command with heredoc content intact is always executed, never a stripped version.

2. **Graceful fallback**: If `shlex.split()` fails, falls back to simple `split()`.

3. **Comprehensive operator support**: Handles all common shell operators: `|`, `&&`, `||`, `;`, `>`, `>>`, `<`, `2>`, `&>`, `2>&1`, `$(...)`, backticks, heredocs.

4. **Maintains safety**: All commands in a pipeline are validated against the whitelist, and forbidden path checks work across the entire command string.

## Files Modified
- `axe.py` - Updated `ToolRunner` class with edge case fixes
- `test_tool_runner_edge_cases.py` - New comprehensive edge case test suite

## Verification
All requirements from the problem statement are met:
✅ Class constants defined
✅ All required methods implemented
✅ All test cases passing
✅ Security checks maintained
✅ No bugs remaining in parsing logic
