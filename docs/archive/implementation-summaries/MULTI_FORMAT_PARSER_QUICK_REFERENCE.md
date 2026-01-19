# Multi-Format Tool Call Parser - Quick Reference

## Overview

AXE now supports **ALL common LLM tool-calling formats**. Use whatever syntax feels natural!

## Supported Formats

### 1. Bash XML Tags (Claude's Favorite)
```
<bash>cat /tmp/file.txt</bash>
<bash>ls -la</bash>
<bash>echo "hello"</bash>
```

### 2. Shell Code Blocks
```
```bash
ls -la /tmp
cat file.txt
pwd
```
```

Also supports:
- ` ```shell\ncommand\n``` `
- ` ```sh\ncommand\n``` `
- ` ```bash command``` ` (inline, no newline)

### 3. AXE Native Blocks

**Read a file:**
```
```READ /path/to/file.txt```
```

**Write to a file:**
```
```WRITE /path/to/output.txt
This is the content
That goes in the file
```
```

**Execute a command:**
```
```EXEC ls -la /tmp```
```

### 4. Simple XML Tags

**Read:**
```
<read_file>/path/to/file.txt</read_file>
```

**Execute:**
```
<shell>ls -la</shell>
```

**Write:**
```
<write_file path="/tmp/output.txt">Content here</write_file>
```

### 5. XML Function Calls (Original Format)
```
<function_calls>
<invoke name="read_file">
<parameter name="file_path">/tmp/file.txt</parameter>
</invoke>
</function_calls>
```

## Features

- **Smart Deduplication**: Identical commands only run once
- **Comment Filtering**: Lines starting with `#` are ignored in shell blocks
- **Multi-line Support**: Each line in a shell block executes separately
- **Empty Commands Ignored**: Whitespace-only commands are skipped
- **Mixed Formats**: Use different formats in the same response!

## Examples

### Example 1: Reading a File (Multiple Ways)

All of these work:

```
<bash>cat /tmp/mission.md</bash>
```

```
```bash
cat /tmp/mission.md
```
```

```
```READ /tmp/mission.md```
```

```
<read_file>/tmp/mission.md</read_file>
```

### Example 2: Creating a File

```
```WRITE /tmp/report.txt
# Project Status Report

- Task 1: Complete
- Task 2: In Progress
```
```

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

## Testing

Run comprehensive tests:
```bash
python3 test_xml_tool_parser.py
```

All 30+ tests should pass! ✅
