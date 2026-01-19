# Multi-Format Tool Call Parser Implementation

## Summary

Successfully extended `xml_tool_parser.py` to support ALL common LLM tool-calling formats, solving the critical issue where agents get stuck when using non-standard syntax.

## Problem Solved

**Before**: Agents could only use `<function_calls><invoke>` XML format. When Claude or other LLMs used natural formats like `<bash>command</bash>` or ` ```bash\ncommand\n``` `, these were NOT parsed, leaving agents stuck for hours.

**After**: The parser now recognizes and executes 10+ different tool-calling formats, allowing agents to use whatever syntax feels natural.

## Supported Formats

| Format | Example | Status |
|--------|---------|--------|
| XML function_calls | `<invoke name="read_file">...</invoke>` | ✅ Existing (PR #6) |
| Bash XML tags | `<bash>cat /tmp/file.txt</bash>` | ✅ NEW |
| Shell code blocks | ` ```bash\nls -la\n``` ` | ✅ NEW |
| Shell variants | ` ```shell\nfind .\n``` `, ` ```sh\necho\n``` ` | ✅ NEW |
| Inline code blocks | ` ```bash ls -la``` ` | ✅ NEW |
| AXE READ | ` ```READ /path``` ` | ✅ NEW |
| AXE WRITE | ` ```WRITE /path\ncontent``` ` | ✅ NEW |
| AXE EXEC | ` ```EXEC command``` ` | ✅ NEW |
| Simple read_file | `<read_file>/path</read_file>` | ✅ NEW |
| Simple shell | `<shell>ls -la</shell>` | ✅ NEW |
| Simple write_file | `<write_file path="/tmp/x">content</write_file>` | ✅ NEW |

## Implementation

### New Functions Added

1. **`parse_bash_tags()`** - Parses `<bash>...</bash>` format
2. **`parse_shell_codeblocks()`** - Parses ` ```bash/shell/sh ``` ` blocks
3. **`parse_axe_native_blocks()`** - Parses ` ```READ/WRITE/EXEC ``` ` blocks
4. **`parse_simple_xml_tags()`** - Parses simple XML tags
5. **`deduplicate_calls()`** - Removes duplicate tool calls (optimized with frozenset)
6. **`parse_all_tool_formats()`** - Unified parser calling all format parsers
7. **`clean_tool_syntax()`** - Removes tool syntax for cleaner display

### Updated Functions

- **`process_agent_response()`** - Now uses `parse_all_tool_formats()` to handle all formats

### Key Features

- **Deduplication**: Identical commands are deduplicated to avoid redundant execution
- **Comment filtering**: Lines starting with `#` in shell blocks are ignored
- **Empty command filtering**: Whitespace-only commands are ignored
- **Multi-line support**: Multi-line shell blocks execute each line separately
- **Optional content**: WRITE blocks can have empty content for creating empty files
- **Inline support**: Code blocks without newlines after language specifier are supported

## Code Quality

### Code Review Issues Addressed

✅ Made newline optional in shell codeblocks for inline format  
✅ Improved regex patterns to use non-greedy matching  
✅ Escaped backticks in regex for clarity  
✅ Optimized deduplication using frozenset (better performance than JSON)  
✅ Made content optional in WRITE blocks  
✅ Fixed clean_tool_syntax to match parser logic  

### Security Scan

✅ **0 security alerts** from CodeQL

## Testing

### Test Coverage

**30+ tests** covering all formats and edge cases:

- ✅ All parser functions tested individually
- ✅ Inline code blocks without newlines
- ✅ Commands with backticks (command substitution)
- ✅ Paths with spaces
- ✅ Multi-line commands
- ✅ Empty WRITE blocks
- ✅ Deduplication
- ✅ Comment filtering
- ✅ Empty command filtering
- ✅ Tool syntax cleaning
- ✅ Integration tests with actual file operations
- ✅ Mixed format responses
- ✅ All existing PR #6 tests still pass

### Test Results

```
XML TOOL PARSER TEST SUITE: ✅ ALL 30+ TESTS PASSED
INTEGRATION TESTS: ✅ ALL 7 SCENARIOS PASSED
EDGE CASE TESTS: ✅ ALL TESTS PASSED
EXISTING TESTS (write_blocks): ✅ ALL TESTS PASSED
```

## Files Changed

1. **`utils/xml_tool_parser.py`** - Core parser implementation (+230 lines)
2. **`test_xml_tool_parser.py`** - Comprehensive test suite (+240 lines)

## Backward Compatibility

✅ **100% backward compatible** - All existing XML function call parsing from PR #6 continues to work exactly as before.

## Impact

This change will prevent agents from getting stuck when they naturally use different tool-calling formats. Instead of spending 4+ hours blocked (as happened in the reported incident), agents can now use any common format and immediately get results.

## Examples

### Example 1: Claude's Natural Format
```
Agent: <bash>cat /tmp/playground/MISSION.md</bash>
Result: ✅ File contents returned
```

### Example 2: Code Block Format
```
Agent: ```bash
ls -la /tmp
```
Result: ✅ Directory listing returned
```

### Example 3: AXE Native Format
```
Agent: ```READ /tmp/file.txt```
Result: ✅ File contents returned
```

### Example 4: Mixed Formats in Single Response
```
Agent: Let me complete this task:

First, read the input:
```READ input.txt```

Then list files:
<bash>ls -la</bash>

Finally, create output:
```WRITE result.txt
Processing complete!
```

Result: ✅ All 3 commands executed, results returned
```

## Success Criteria

All requirements from the problem statement have been met:

- ✅ `<bash>command</bash>` tags parsed and executed
- ✅ ` ```bash\n...\n``` ` code blocks parsed and executed
- ✅ ` ```shell\n...\n``` ` code blocks parsed and executed
- ✅ ` ```sh\n...\n``` ` code blocks parsed and executed
- ✅ ` ```READ /path``` ` blocks parsed and executed
- ✅ ` ```WRITE /path\ncontent``` ` blocks parsed and executed
- ✅ ` ```EXEC command``` ` blocks parsed and executed
- ✅ Simple XML tags (`<read_file>`, `<shell>`) parsed
- ✅ Duplicate commands deduplicated
- ✅ Empty/whitespace-only commands ignored
- ✅ Comments in code blocks ignored
- ✅ Multi-line code blocks execute each line
- ✅ All existing PR #6 functionality still works
- ✅ Comprehensive test coverage for all formats
- ✅ Results appear in conversation history for agents to see
