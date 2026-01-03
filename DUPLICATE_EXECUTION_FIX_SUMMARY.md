# Duplicate Execution and Heredoc Parsing Bug Fixes

## Summary

This document describes the fixes implemented for two critical bugs in the AXE tool execution system that affected both interactive mode (`@agent` commands) and collaborative mode (`/collab`).

## Bug 1: Duplicate Command Execution ❌ → ✅

### Problem
Commands in agent responses were being executed **twice**, causing:
- Double execution of side-effect commands (e.g., `rm` deleting a file, then failing on second attempt)
- Duplicate output with confusing XML tags showing
- Wasted resources and potential data corruption

### Root Cause
Both `xml_tool_parser.py` and `axe.py` were parsing the same code blocks:
1. `xml_tool_parser.parse_axe_native_blocks()` parsed ` ```EXEC`, ` ```READ`, ` ```WRITE` blocks
2. `axe.py` `ResponseProcessor.process_response()` ALSO parsed the same blocks with regex

### Example of Duplicate Execution (Before Fix)
```
--- Execution Results ---
<result>                              ← XML parser execution
<function_result>
<result>
[Command executed successfully]
</result>
</function_result>
</result>
[EXEC: rm /tmp/AXE/gpt.txt]           ← Markdown parser execution (FAILS!)
ERROR: Exit code 1: rm: cannot remove '/tmp/AXE/gpt.txt': No such file
```

### Solution
**Removed `parse_axe_native_blocks()` from `parse_all_tool_formats()`**

The native ` ```READ`, ` ```EXEC`, ` ```WRITE` blocks are now handled exclusively by `axe.py`'s `ResponseProcessor`, which is the original and more robust handler with full heredoc support.

**Changes in `utils/xml_tool_parser.py`:**
```python
def parse_all_tool_formats(response: str) -> List[Dict[str, Any]]:
    calls = []
    
    # 1. XML function_calls format
    calls.extend(parse_xml_function_calls(response))
    
    # 2. <bash> format
    calls.extend(parse_bash_tags(response))
    
    # 3. ```bash / ```shell / ```sh code blocks
    calls.extend(parse_shell_codeblocks(response))
    
    # 4. REMOVED: AXE native ```READ/WRITE/EXEC``` blocks
    # These are now handled EXCLUSIVELY by axe.py ResponseProcessor
    # to prevent duplicate execution
    # calls.extend(parse_axe_native_blocks(response))  # COMMENTED OUT
    
    # 5. Simple XML tags like <read_file>, <shell>
    calls.extend(parse_simple_xml_tags(response))
    
    return deduplicate_calls(calls)
```

### After Fix
Commands are executed only once:
```
--- Execution Results ---
[EXEC: rm /tmp/AXE/gpt.txt]
[Command executed successfully]
```

## Bug 2: Heredoc Parsing Errors ❌ → ✅

### Problem
When agents used heredocs in shell code blocks, content lines were incorrectly parsed as separate commands:

```bash
cat << EOF > file.md
- Item 1
- Item 2  
1. First step
EOF
```

Caused errors like:
```
ERROR: Tool '-' not in whitelist
ERROR: Tool '1.' not in whitelist
ERROR: Tool 'EOF' not in whitelist
```

### Root Cause
`parse_shell_codeblocks()` in `xml_tool_parser.py` split on newlines without detecting heredocs.

### Solution
**Added heredoc detection and proper handling**

**New helper function:**
```python
def _contains_heredoc(content: str) -> bool:
    """
    Check if content contains a heredoc marker.
    Detects: << EOF, <<- EOF, <<'EOF', <<"EOF", <<< (here-string)
    """
    heredoc_pattern = r'<<-?\s*[\'"]?\w+[\'"]?|<<<'
    return bool(re.search(heredoc_pattern, content))
```

**Modified `parse_shell_codeblocks()`:**
```python
def parse_shell_codeblocks(response: str) -> List[Dict[str, Any]]:
    pattern = r'```(?:bash|shell|sh)\n?(.*?)```'
    calls = []
    for match in re.findall(pattern, response, re.DOTALL):
        cmd = match.strip()
        if cmd:
            # Check if the entire block contains a heredoc
            # If so, treat the whole block as a single command
            if _contains_heredoc(cmd):
                calls.append({
                    'tool': 'EXEC',
                    'params': {'command': cmd},
                    'raw_name': 'shell'
                })
            else:
                # No heredoc - process line by line as before
                for command in _split_shell_commands(cmd):
                    if command and not command.startswith('#'):
                        calls.append({
                            'tool': 'EXEC',
                            'params': {'command': command},
                            'raw_name': 'shell'
                        })
    return calls
```

### Supported Heredoc Formats
- `<< EOF` - Standard heredoc
- `<<- EOF` - Indented heredoc (strips leading tabs)
- `<< 'EOF'` - Quoted delimiter (no variable expansion)
- `<< "EOF"` - Quoted delimiter (with variable expansion)
- `<<< "string"` - Here-string

### After Fix
Heredocs are preserved as single commands:
```python
# Input:
"""```bash
cat << EOF > notes.md
- Item 1
- Item 2
EOF
```"""

# Parsed as:
[
    {
        'tool': 'EXEC',
        'params': {
            'command': 'cat << EOF > notes.md\n- Item 1\n- Item 2\nEOF'
        },
        'raw_name': 'shell'
    }
]
```

## Test Coverage

### New Tests Added

1. **`test_no_duplicate_execution()`** - Verifies commands are only parsed once
2. **`test_heredoc_in_shell_block()`** - Verifies heredocs are preserved as single commands
3. **`test_multiline_without_heredoc()`** - Ensures regular multi-line commands still work
4. **`test_heredoc_variations()`** - Tests various heredoc formats (<<, <<-, <<<)

### Test Results
```
======================================================================
✅ ALL TESTS PASSED! (43/43)
======================================================================
```

## Examples

### Example 1: No Duplicate Execution
```python
# Agent response with EXEC block
response = """I'll delete the file:
```EXEC
rm test.txt
```
Done!"""

# Before fix: parse_all_tool_formats would parse it, then ResponseProcessor would parse it again
# After fix: Only ResponseProcessor handles it
calls = parse_all_tool_formats(response)
assert len(calls) == 0  # ✅ Not parsed by xml_tool_parser anymore
```

### Example 2: Heredoc Preserved
```python
# Agent response with heredoc
response = """```bash
cat << EOF > output.md
# Header
- Item 1
- Item 2
EOF
```"""

# Before fix: Would create 4 separate commands (cat, "# Header", "- Item 1", "- Item 2")
# After fix: Creates 1 command with entire heredoc
calls = parse_shell_codeblocks(response)
assert len(calls) == 1  # ✅ Single command
assert '- Item 1' in calls[0]['params']['command']  # ✅ Content preserved
```

### Example 3: Backward Compatibility
```python
# Regular multi-line commands still work
response = """```bash
echo "line 1"
echo "line 2"
```"""

# Still creates 2 separate commands (no heredoc detected)
calls = parse_shell_codeblocks(response)
assert len(calls) == 2  # ✅ Backward compatible
```

## Impact

- ✅ **Interactive mode (`@agent`)**: Fixed - no more duplicate executions
- ✅ **Collaborative mode (`/collab`)**: Fixed - no more duplicate executions  
- ✅ **Backward compatibility**: Maintained - all existing functionality works
- ✅ **Performance**: Slightly improved (no duplicate executions)
- ✅ **Heredoc support**: Now properly handled in shell blocks
- ✅ **Error reduction**: No more "tool not in whitelist" errors for heredoc content

## Files Modified

1. **`utils/xml_tool_parser.py`**:
   - Commented out `parse_axe_native_blocks()` call in `parse_all_tool_formats()`
   - Added `_contains_heredoc()` helper function
   - Modified `parse_shell_codeblocks()` to handle heredocs
   - Added documentation explaining the changes

2. **`test_xml_tool_parser.py`**:
   - Updated `test_mixed_formats()` to reflect changes
   - Added 4 new test functions for bug fixes
   - All 43 tests pass

## Verification

To verify the fixes work:

```bash
# Run the test suite
python3 test_xml_tool_parser.py

# Quick verification
python3 -c "
from utils.xml_tool_parser import parse_all_tool_formats, parse_shell_codeblocks

# Test 1: No duplicate parsing
response1 = '\`\`\`EXEC ls\n\`\`\`'
calls1 = parse_all_tool_formats(response1)
assert len(calls1) == 0, 'Native blocks should not be parsed'

# Test 2: Heredoc preserved
response2 = '\`\`\`bash\ncat << EOF\nline1\nEOF\n\`\`\`'
calls2 = parse_shell_codeblocks(response2)
assert len(calls2) == 1, 'Heredoc should be single command'
assert '<< EOF' in calls2[0]['params']['command'], 'Heredoc marker preserved'

print('✅ All verifications passed!')
"
```

## Conclusion

Both bugs have been successfully fixed:
1. ✅ Commands are no longer executed twice
2. ✅ Heredocs are properly handled in shell blocks
3. ✅ All existing tests pass
4. ✅ New tests verify the fixes
5. ✅ Backward compatibility maintained
