# XML Function Call Support - Quick Reference

## What's New?

AXE now supports **native XML function call format** used by LLM agents (Claude, GPT, Llama, Grok) in addition to the existing markdown block syntax.

## Why This Matters

**Before:** Agents using XML format had tool calls silently fail
```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">mission.md</parameter>
</invoke>
</function_calls>
```
❌ No result, agent can't see file contents

**After:** XML calls execute properly and return results
```xml
<result>
<function_result>
<result>
# Mission Document
Your mission content here...
</result>
</function_result>
</result>
```
✅ Agent sees actual file contents in conversation history

## Supported Formats

### XML Format (New!)

```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">config.yaml</parameter>
</invoke>
</function_calls>
```

### Markdown Format (Original)

```
```READ config.yaml```
```

**Both formats work!** You can even mix them in the same response.

## Supported Operations

### READ - Read Files
```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">path/to/file.txt</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `read`, `cat`, `get_file`, `view_file`

### WRITE - Create/Write Files
```xml
<function_calls>
<invoke name="write_file">
<parameter name="file_path">output.txt</parameter>
<parameter name="content">File content here</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `write`, `create_file`, `save_file`

### APPEND - Append to Files
```xml
<function_calls>
<invoke name="append_file">
<parameter name="file_path">log.txt</parameter>
<parameter name="content">New log entry</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `append`, `append_to_file`

### EXEC - Run Commands
```xml
<function_calls>
<invoke name="shell">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `bash`, `exec`, `run_shell`, `execute`, `run_command`

### LIST_DIR - List Directory
```xml
<function_calls>
<invoke name="list_dir">
<parameter name="path">.</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `list_directory`, `ls`, `listdir`

## Parameter Names

The parser accepts multiple parameter name variants:

- **File path:** `file_path`, `path`, `filename`, `file`
- **Content:** `content`, `data`, `text`, `contents`
- **Command:** `command`, `cmd`, `shell_command`
- **Directory:** `path`, `directory`, `dir`

## Security

All operations respect AXE's security policies:

✅ Path traversal prevention
✅ Directory access control
✅ Tool whitelist enforcement
✅ Project boundary enforcement

Attempts to access forbidden paths or run unauthorized commands will be blocked.

## Results in Conversation History

**Key Feature:** Results from XML function calls are automatically added to the conversation history, so all agents in collaborative sessions can see the outputs.

**Example:**
1. Agent A reads a file using XML format
2. Result is added to conversation history
3. Agent B can reference the file contents in their response

This solves the "infinite retry loop" problem where agents kept trying to read files they couldn't see the results from.

## Testing

Run the test suites:

```bash
# Unit tests
python3 test_xml_tool_parser.py

# Manual verification
python3 manual_test_xml.py

# Existing tests (verify no breakage)
python3 test_write_blocks.py
python3 test_axe_improvements.py
```

## Examples

### Example 1: Read and Process
```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">input.json</parameter>
</invoke>
</function_calls>
```

Result appears in conversation as:
```xml
<result>
<function_result>
<result>
{"key": "value", "data": [1, 2, 3]}
</result>
</function_result>
</result>
```

### Example 2: Create File
```xml
<function_calls>
<invoke name="write_file">
<parameter name="file_path">report.md</parameter>
<parameter name="content"># Analysis Report

Key findings:
- Item 1
- Item 2
</parameter>
</invoke>
</function_calls>
```

Result:
```xml
<result>
<function_result>
<result>
✓ File written successfully (85 bytes)
</result>
</function_result>
</result>
```

### Example 3: Multiple Operations
```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">data.csv</parameter>
</invoke>
</function_calls>

<function_calls>
<invoke name="write_file">
<parameter name="file_path">summary.txt</parameter>
<parameter name="content">Data summary goes here</parameter>
</invoke>
</function_calls>
```

Both operations execute and return results in sequence.

## Troubleshooting

### No Results Appearing?

1. Check that XML syntax is correct (closing tags, proper nesting)
2. Verify tool name is supported (see list above)
3. Check parameter names match expected values
4. Review security restrictions (forbidden paths, whitelist)

### Path Errors?

- Use relative paths from project root
- Absolute paths must be within project directory
- No `../` path traversal allowed

### Command Fails?

- Check tool whitelist in `axe.yaml`
- Commands must be explicitly allowed
- Commands execute immediately after passing validation

## Backward Compatibility

✅ All existing markdown block syntax still works
✅ No breaking changes to existing code
✅ Can mix XML and markdown in same response
✅ All existing tests pass

## More Information

See `XML_PARSER_IMPLEMENTATION.md` for detailed technical documentation.
