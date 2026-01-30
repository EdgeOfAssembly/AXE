# Workspace Path Bug Fix and Multiple Workspace Support

## Summary

Fixed critical bug where agents couldn't see files outside the AXE directory when using `--workspace` flag. Also added support for multiple comma-separated workspaces and a `/workspace` command for managing workspaces interactively.

## Changes Made

### 1. Core Sandbox Fix (`core/sandbox.py`)

**Problem**: `SandboxManager.__init__()` was only reading workspaces from config file, ignoring the `workspace_path` parameter passed from command line or `/collab` command.

**Solution**:
- Added `workspace_paths` parameter to `SandboxManager.__init__()`
- Updated `build_bwrap_command()` to bind ALL workspace paths with `--bind` flags
- Workspaces from CLI/command now properly override config workspaces

### 2. Tool Runner Integration (`core/tool_runner.py`)

**Problem**: `ToolRunner` wasn't passing workspace paths to `SandboxManager`.

**Solution**:
- Added `workspace_paths` parameter to `ToolRunner.__init__()`
- Passes workspace paths to `SandboxManager` when sandbox is enabled

### 3. CLI Argument Parsing (`axe.py`)

**Problem**: `--workspace` flag only accepted single workspace.

**Solution**:
- Updated `--workspace` help text to indicate comma-separated support
- Parse comma-separated workspace paths: `/tmp/a,/tmp/b,/tmp/c`
- Convert relative paths to absolute paths before use

### 4. Collaborative Session Support (`axe.py`)

**Problem**: `/collab` command didn't support multiple workspaces.

**Solution**:
- Updated `CollaborativeSession.__init__()` to accept `workspace_paths` list
- Updated `ChatSession.__init__()` to accept `workspace_paths` list
- Updated `/collab` command parser to support comma-separated workspaces
- Pass workspace paths through entire initialization chain

### 5. New `/workspace` Command (`axe.py`)

Added interactive workspace management command:

```
/workspace                      # Show current workspace(s)
/workspace /path/to/dir         # Set single workspace
/workspace /path1,/path2        # Set multiple workspaces
/workspace +/path/to/add        # Add workspace to existing list
/workspace -/path/to/remove     # Remove workspace from list
/workspace clear                # Clear all workspaces (use AXE dir only)
```

## Usage Examples

### Command Line

```bash
# Single workspace
./axe.py --workspace /tmp/playground

# Multiple workspaces (comma-separated, no spaces)
./axe.py --workspace /tmp/playground,/tmp/projectX,/home/user/code

# Collaborative mode with workspace
./axe.py --collab llama,copilot --workspace /tmp/test --time 30 --task "Review code"

# Collaborative mode with multiple workspaces
./axe.py --collab grok,copilot --workspace /tmp/a,/tmp/b --time 60 --task "Cross-project analysis"
```

### Interactive Mode

```bash
# Start interactive mode
./axe.py

# Show current workspaces
> /workspace

# Set workspace
> /workspace /tmp/playground

# Set multiple workspaces
> /workspace /tmp/a,/tmp/b

# Add workspace
> /workspace +/tmp/projectX

# Remove workspace
> /workspace -/tmp/a

# Clear all
> /workspace clear

# Start collaboration with workspaces
> /collab llama,copilot /tmp/a,/tmp/b 30 "Review code"
```

## Testing

### Unit Tests

All unit tests pass:

```bash
python3 tests/test_workspace_paths.py
```

Tests verify:
- ✅ Single workspace configuration
- ✅ Multiple workspaces configuration
- ✅ Fallback to default workspace
- ✅ ToolRunner passes workspaces to SandboxManager
- ✅ Non-existent workspace handling
- ✅ Absolute path conversion

### Manual Testing (Requires bubblewrap + ollama)

**Prerequisites**:
```bash
# Install bubblewrap
sudo apt-get update && sudo apt-get install -y bubblewrap

# Install ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a small model
ollama pull tinyllama
# or
ollama pull phi
```

**Test 1: Single workspace from CLI**
```bash
# Create test workspace
mkdir -p /tmp/test_workspace
echo "test content" > /tmp/test_workspace/test.txt

# Start AXE with workspace
./axe.py --workspace /tmp/test_workspace

# Ask agent to list files
@claude list all files in /tmp/test_workspace
@claude read /tmp/test_workspace/test.txt
@claude create /tmp/test_workspace/hello.txt with content "Hello World"
```

**Test 2: Multiple workspaces from CLI**
```bash
# Create test workspaces
mkdir -p /tmp/workspace_a /tmp/workspace_b
echo "File A" > /tmp/workspace_a/a.txt
echo "File B" > /tmp/workspace_b/b.txt

# Start AXE with multiple workspaces
./axe.py --workspace /tmp/workspace_a,/tmp/workspace_b

# Agent should see both workspaces
@claude list files in /tmp/workspace_a
@claude list files in /tmp/workspace_b
@claude read /tmp/workspace_a/a.txt
@claude read /tmp/workspace_b/b.txt
```

**Test 3: /collab with workspaces**
```bash
./axe.py

# In interactive mode
> /collab ollama /tmp/workspace_a,/tmp/workspace_b 60 "List all files in both workspaces and create a summary"
```

**Test 4: /workspace command**
```bash
./axe.py

> /workspace
# Should show: No workspaces or current dir

> /workspace /tmp/test
# Should show: Workspaces set to: /tmp/test

> /workspace +/tmp/another
# Should show: Added workspace: /tmp/another

> /workspace
# Should show list of workspaces

> /workspace -/tmp/test
# Should show: Removed workspace: /tmp/test

> /workspace clear
# Should show: Workspaces cleared
```

## Technical Details

### Bubblewrap Command Generation

Before fix (single workspace from config):
```bash
bwrap --bind /path/to/axe /path/to/axe ...
```

After fix (multiple workspaces from CLI):
```bash
bwrap --bind /tmp/workspace_a /tmp/workspace_a \
      --bind /tmp/workspace_b /tmp/workspace_b \
      --bind /tmp/workspace_c /tmp/workspace_c \
      ...
```

### Data Flow

```
CLI: --workspace /tmp/a,/tmp/b
  ↓
main(): Parse comma-separated paths
  ↓
CollaborativeSession(workspace_paths=['/tmp/a', '/tmp/b'])
  ↓
ToolRunner(workspace_paths=['/tmp/a', '/tmp/b'])
  ↓
SandboxManager(workspace_paths=['/tmp/a', '/tmp/b'])
  ↓
build_bwrap_command(): Add --bind for each workspace
  ↓
bwrap --bind /tmp/a /tmp/a --bind /tmp/b /tmp/b ...
```

## Backward Compatibility

- ✅ Single workspace still works: `--workspace /tmp/test`
- ✅ No workspace specified defaults to project directory
- ✅ Config file workspaces still work (if no CLI workspace specified)
- ✅ Existing code unchanged (workspace_paths defaults to None)

## Known Limitations

1. **Sandbox disabled**: If bubblewrap is not installed or sandbox is disabled in config, workspaces are not enforced but agents can still access files normally.

2. **Non-existent workspaces**: Non-existent workspace paths are tracked but skipped during bwrap binding (won't cause errors).

3. **Path resolution**: Relative paths are converted to absolute paths based on the current directory at startup.

## Files Modified

- `core/sandbox.py` - SandboxManager workspace binding fix
- `core/tool_runner.py` - Workspace paths parameter added
- `axe.py` - CLI parsing, /collab, /workspace command, ChatSession/CollaborativeSession updates

## Files Added

- `tests/test_workspace_paths.py` - Comprehensive test suite
- `WORKSPACE_FIX.md` - This documentation file
