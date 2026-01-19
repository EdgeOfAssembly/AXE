# Tool Call Parsers

## Overview

AXE supports **multiple tool-calling formats** to work seamlessly with different LLM providers. All formats are parsed and executed with the same security guarantees and functionality.

## Supported Formats

### 1. Bash XML Tags (Claude's Favorite)
```xml
<bash>cat /tmp/file.txt</bash>
<bash>ls -la</bash>
<bash>echo "hello"</bash>
```

### 2. Shell Code Blocks
````markdown
```bash
ls -la /tmp
cat file.txt
pwd
```
````

Also supports:
- ` ```shell\ncommand\n``` `
- ` ```sh\ncommand\n``` `
- ` ```bash command``` ` (inline, no newline)

### 3. AXE Native Blocks

**Read a file:**
````
```READ /path/to/file.txt```
````

**Write to a file:**
````
```WRITE /path/to/output.txt
This is the content
That goes in the file
```
````

**Execute a command:**
````
```EXEC ls -la /tmp```
````

### 4. Simple XML Tags

**Read:**
```xml
<read_file>/path/to/file.txt</read_file>
```

**Execute:**
```xml
<shell>ls -la</shell>
```

**Write:**
```xml
<write_file path="/tmp/output.txt">Content here</write_file>
```

### 5. XML Function Calls (Standard LLM Format)

```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">/tmp/file.txt</parameter>
</invoke>
</function_calls>
```

## XML Function Call Support

AXE natively supports the standard XML function call format used by LLM agents (Claude, GPT, Llama, Grok).

### Supported Operations

#### READ - Read Files
```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">path/to/file.txt</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `read`, `cat`, `get_file`, `view_file`

#### WRITE - Create/Write Files
```xml
<function_calls>
<invoke name="write_file">
<parameter name="file_path">output.txt</parameter>
<parameter name="content">File content here</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `write`, `create_file`, `save_file`

#### APPEND - Append to Files
```xml
<function_calls>
<invoke name="append_file">
<parameter name="file_path">log.txt</parameter>
<parameter name="content">New log entry</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `append`, `append_to_file`

#### EXEC - Run Commands
```xml
<function_calls>
<invoke name="shell">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `bash`, `exec`, `run_shell`, `execute`, `run_command`

#### LIST_DIR - List Directory
```xml
<function_calls>
<invoke name="list_dir">
<parameter name="path">.</parameter>
</invoke>
</function_calls>
```

Alternative tool names: `list_directory`, `ls`, `listdir`

### Parameter Names

The parser accepts multiple parameter name variants:

- **File path:** `file_path`, `path`, `filename`, `file`
- **Content:** `content`, `data`, `text`, `contents`
- **Command:** `command`, `cmd`, `shell_command`
- **Directory:** `path`, `directory`, `dir`

## Features

- **Smart Deduplication**: Identical commands only run once
- **Comment Filtering**: Lines starting with `#` are ignored in shell blocks
- **Multi-line Support**: Each line in a shell block executes separately
- **Empty Commands Ignored**: Whitespace-only commands are skipped
- **Mixed Formats**: Use different formats in the same response!
- **Results in History**: XML function call results are automatically added to conversation history

## Examples

### Example 1: Reading a File (Multiple Ways)

All of these work:

```xml
<bash>cat /tmp/mission.md</bash>
```

````markdown
```bash
cat /tmp/mission.md
```
````

````
```READ /tmp/mission.md```
````

```xml
<read_file>/tmp/mission.md</read_file>
```

### Example 2: Creating a File

````
```WRITE /tmp/report.txt
# Project Status Report

- Task 1: Complete
- Task 2: In Progress
```
````

### Example 3: Mixed Operations

```
Let me complete this task:

First, read the config:
```READ config.yaml```

Then check the files:
<bash>ls -la</bash>

Finally, create output:
```WRITE output.txt
Processing complete!
```

All done!
```

### Example 4: XML Function Calls

```xml
<function_calls>
<invoke name="read_file">
<parameter name="file_path">input.json</parameter>
</invoke>
</function_calls>

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

Results appear in conversation as:
```xml
<result>
<function_result>
<result>
{"key": "value", "data": [1, 2, 3]}
</result>
</function_result>
</result>
```

## Security

All operations respect AXE's security policies:

✅ Path traversal prevention  
✅ Directory access control  
✅ Tool whitelist enforcement  
✅ Project boundary enforcement  

Attempts to access forbidden paths or run unauthorized commands will be blocked.

## Tips

1. **Use what feels natural**: Don't worry about format - AXE understands them all
2. **Combine formats**: Mix and match in the same response
3. **Multi-line commands**: Put each command on its own line in code blocks
4. **Comments are OK**: Use `#` for comments in shell blocks
5. **Paths with spaces**: They work fine in all formats

## Error Handling

- Invalid paths are rejected with clear error messages
- Path traversal attempts (e.g., `../../etc/passwd`) are blocked
- Empty commands are silently ignored
- Results appear in the conversation history

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

## Testing

Run comprehensive tests:
```bash
python3 tests/test_xml_tool_parser.py
python3 tests/test_inline_exec_blocks.py
```

## Backward Compatibility

✅ All existing markdown block syntax still works  
✅ No breaking changes to existing code  
✅ Can mix XML and markdown in same response  
✅ All existing tests pass  
