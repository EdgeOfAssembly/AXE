# WRITE Block Functionality - User Guide

## Overview

AXE agents can now read files, execute commands, and **write files** using special code blocks in their responses. This enables agents to create patches, scripts, configuration files, and any other text-based content directly.

## Syntax

### WRITE Block Format

```
```WRITE filename.ext
file content goes here
multiple lines supported
```
```

**Key Points:**
- The filename goes on the same line as `WRITE`
- The content starts on the next line
- Supports any text content including code, JSON, XML, etc.
- Automatically creates parent directories if needed

## Examples

### 1. Simple Text File

Agent response:
```
I'll create a configuration file for you.

```WRITE config.ini
[database]
host = localhost
port = 5432
user = admin
```

Configuration file created successfully!
```

Result: Creates `config.ini` with the specified content

### 2. Python Script

Agent response:
```
Here's the hello world script:

```WRITE hello.py
#!/usr/bin/env python3

def main():
    print("Hello, World!")
    print("This file was created by an AI agent!")

if __name__ == "__main__":
    main()
```

Run it with: python3 hello.py
```

Result: Creates executable Python script `hello.py`

### 3. File in Subdirectory

Agent response:
```
```WRITE patches/fix_001.patch
--- a/main.c
+++ b/main.c
@@ -10,7 +10,7 @@
 int main() {
-    printf("Hello\n");
+    printf("Hello, World!\n");
     return 0;
 }
```
```

Result: Creates `patches/` directory if it doesn't exist, then creates `fix_001.patch`

### 4. Multiple Files in One Response

Agent response:
```
I'll create both the script and its config:

```WRITE run.sh
#!/bin/bash
python3 app.py --config config.json
```

```WRITE config.json
{
  "mode": "production",
  "port": 8080
}
```

Files created successfully!
```

Result: Creates both `run.sh` and `config.json`

## Integration with Other Blocks

WRITE blocks work alongside READ and EXEC blocks:

```
Let me analyze the code and create a fixed version:

```READ broken.c
```

I found the issue. Here's the fix:

```WRITE fixed.c
// Fixed version
#include <stdio.h>

int main() {
    printf("Fixed!\n");
    return 0;
}
```

Now let's compile it:

```EXEC gcc -o fixed fixed.c
```
```

## Security and Permissions

### Directory Access Control

WRITE blocks respect the directory access rules in `axe.yaml`:

```yaml
directories:
  # Agents can read/write these
  allowed:
    - "."
    - ./src
    - ./patches
    - ./output
  
  # Agents can only read these
  readonly:
    - ./vendor
    - ./reference
  
  # Agents cannot access these
  forbidden:
    - /etc
    - /root
    - ~/.ssh
```

### Behavior

- ✅ Writing to allowed directories: Succeeds
- ❌ Writing to readonly directories: Blocked
- ❌ Writing to forbidden directories: Blocked
- ❌ Writing outside project directory: Blocked (unless explicitly allowed)

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python3 test_write_blocks.py
```

Tests cover:
- Simple file creation
- Multiline content
- Subdirectory paths
- Multiple blocks
- Permission checks
- Edge cases
- File overwrite behavior

### Manual Testing

Run the manual test script with real APIs:

```bash
# Set your API keys
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key

# Run manual test
python3 manual_test_write.py
```

### Interactive Testing

Test in single-agent mode:

```bash
./axe.py
```

```
axe> @gpt create a file called test.txt with "Hello World"
```

Test in collaborative mode:

```bash
./axe.py --collab gpt,claude ./workspace 10 "Create a Python script that prints system info"
```

## Implementation Details

### Code Block Parser

The `ResponseProcessor` class uses regex to extract code blocks:

```python
pattern = r'```(READ|EXEC|WRITE)\s*([^\n]*)\n(.*?)```'
```

- Matches all three block types
- Extracts arguments (filename for WRITE/READ, command for EXEC)
- Extracts content (file content or command body)

### File Writing Logic

1. Extract filename from block arguments
2. Check directory access permissions
3. Create parent directories if needed (with `os.makedirs`)
4. Write content to file
5. Report success or error

### Execution Order

Code blocks are executed in the order they appear in the agent's response:

```
```READ input.txt     <- Executed 1st
```

```EXEC process.sh   <- Executed 2nd
```

```WRITE output.txt  <- Executed 3rd
```
```

## Troubleshooting

### Agent doesn't use WRITE blocks

**Problem:** Agent writes file paths but doesn't use the WRITE block syntax.

**Solution:** Be explicit in your prompt:

❌ Bad: "Create a file called output.txt"
✅ Good: "Use a WRITE block to create a file called output.txt with the content..."

### Files created in wrong location

**Problem:** File created in unexpected directory.

**Solution:** Use absolute paths from project root:

```
```WRITE ./output/data.json  <- Explicit path from project root
```
```

### Permission denied errors

**Problem:** Agent tries to write to forbidden directory.

**Solution:** Check `axe.yaml` directory settings and ensure the target is in an allowed directory.

### Content not written correctly

**Problem:** File created but content is wrong or truncated.

**Solution:** 
- Check that the closing ` ``` ` is on its own line
- Ensure no extra backticks in content that might close the block early
- Content should start immediately after the newline following `WRITE filename`

## Use Cases

### 1. Patch Files

Agents can create patch files for code review:

```
```WRITE fix_memory_leak.patch
--- a/network.c
+++ b/network.c
@@ -45,6 +45,7 @@
     char *buffer = malloc(1024);
     process_data(buffer);
+    free(buffer);  // Fix: Free allocated memory
     return 0;
 }
```
```

### 2. Configuration Files

Generate config files based on requirements:

```
```WRITE .env
DATABASE_URL=postgresql://localhost/mydb
API_KEY=secret_key_here
DEBUG=false
```
```

### 3. Documentation

Create or update documentation:

```
```WRITE docs/api.md
# API Documentation

## Endpoints

### GET /users
Returns list of users...
```
```

### 4. Test Files

Generate test cases:

```
```WRITE tests/test_parser.py
import pytest
from parser import parse_config

def test_parse_valid_config():
    result = parse_config("config.ini")
    assert result["port"] == 8080
```
```

### 5. Build Scripts

Create build or deployment scripts:

```
```WRITE deploy.sh
#!/bin/bash
set -e
npm install
npm run build
rsync -av dist/ server:/var/www/app/
```
```

## Best Practices

1. **Be explicit in filenames:** Use full paths from project root
2. **Test permissions first:** Ensure target directory is allowed
3. **Review before executing:** Check generated files before running them
4. **Combine with EXEC:** Write scripts then execute them to verify
5. **Use version control:** Commit important files before letting agents modify them

## Changelog

### v1.0 (Current)
- ✅ WRITE block implementation
- ✅ READ block support
- ✅ EXEC block integration
- ✅ Directory access control
- ✅ Comprehensive test suite
- ✅ Single-agent mode support
- ✅ Collaborative mode support

## Future Enhancements

Potential improvements:
- Binary file support (base64 encoding)
- Append mode (`APPEND` block type)
- File templates with variable substitution
- Diff generation and application
- Automatic backup before overwrite
