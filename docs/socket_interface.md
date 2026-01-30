# Unix Socket Interface for Agent Communication

## Overview

AXE provides a Unix domain socket interface that allows external agents (including Copilot coding agents) to programmatically interact with AXE when running in interactive mode. This enables agents to test and use AXE exactly as a human would, receiving the same output including ANSI color codes.

## Key Features

- **Bidirectional Communication**: Send commands and receive full output
- **ANSI Color Preservation**: Output includes all formatting and colors
- **Low Latency**: Unix sockets provide near-zero overhead
- **Security**: Local-only communication with no network exposure
- **Automatic Cleanup**: Socket files are removed on exit

## Socket and PID File Locations

When AXE is running in interactive mode, it creates two files:

```
/run/user/<uid>/axe.sock   # Unix domain socket
/run/user/<uid>/axe.pid    # PID file for process discovery
```

Where `<uid>` is the user's UID (from `os.getuid()`).

**Note**: These files are **only created in interactive mode**, not when using the `-c` batch mode flag.

## Communication Protocol

### Sending Commands

To send a command to AXE:

1. Connect to the Unix socket at `/run/user/<uid>/axe.sock`
2. Send your command as UTF-8 text with a trailing newline (`\n`)
3. Receive the response (which includes ANSI color codes)
4. Close the connection

### Command Format

Commands should be sent exactly as you would type them in the interactive REPL:

- **Agent commands**: `@agent task description\n`
- **Slash commands**: `/help\n`, `/agents\n`, `/quit\n`, etc.
- **Default agent**: `task description\n` (uses default agent)

### Response Format

The response includes:

- Echo of the command (with `>` prefix)
- Full output that would appear on the terminal
- ANSI color codes (e.g., `\x1b[32m` for green)
- Any errors or warnings
- Agent responses

## Python Example

```python
import socket
import os

# Get socket path
uid = os.getuid()
sock_path = f"/run/user/{uid}/axe.sock"
pid_path = f"/run/user/{uid}/axe.pid"

# Check if AXE is running
if not os.path.exists(pid_path):
    print("AXE is not running")
    exit(1)

with open(pid_path) as f:
    axe_pid = f.read().strip()
    print(f"AXE running with PID {axe_pid}")

# Connect and send command
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(sock_path)

# Send command
command = "@claude analyze this code\n"
s.sendall(command.encode('utf-8'))

# Receive response
response = s.recv(65536).decode('utf-8')
print(response)  # Includes ANSI colors!

s.close()
```

## Bash Example

Using `socat` or `nc` (netcat):

```bash
# Check if AXE is running
if [ ! -f "/run/user/$(id -u)/axe.pid" ]; then
    echo "AXE is not running"
    exit 1
fi

# Send command and receive response
echo "@claude help me debug this" | socat - UNIX-CONNECT:/run/user/$(id -u)/axe.sock
```

## Stale File Handling

AXE automatically handles stale files from crashed sessions:

1. **On startup**, AXE checks for existing PID and socket files
2. If a PID file exists, it checks if the process is still alive:
   - **Process alive**: Raises an error (another instance running)
   - **Process dead**: Cleans up stale files and continues
   - **Invalid PID**: Cleans up and continues
3. If only a socket file exists (orphaned), it's removed

## Signal Handling

AXE registers handlers for clean shutdown:

- `SIGTERM` - Graceful shutdown
- `SIGINT` (Ctrl+C) - Graceful shutdown
- `SIGHUP` - Graceful shutdown

All handlers remove the socket and PID files before exiting.

Additionally, `atexit` is used as a backup for normal exit scenarios.

## Security Considerations

### Local-Only Communication

Unix domain sockets are local-only and provide:

- No network exposure
- File system permissions (user-only access)
- Process isolation

### Permission Model

- Socket file permissions match the user's umask
- Only the creating user can connect to the socket
- PID file is readable by the user only

### Authentication

Currently, no additional authentication is implemented beyond file system permissions. The socket relies on:

1. File system access controls
2. Process ownership verification
3. Same-user restriction

For enhanced security in the future, consider adding:

- Optional authentication tokens
- Command whitelisting
- Rate limiting

## Error Handling

### Common Errors

**Connection Refused**
```python
# Socket file doesn't exist or AXE isn't running
ConnectionRefusedError: [Errno 111] Connection refused
```

**Another Instance Running**
```
RuntimeError: Another AXE instance is already running (PID 12345).
If this is incorrect, remove /run/user/1001/axe.pid and /run/user/1001/axe.sock
```

**Invalid Command**
```
Unknown agent: xyz
# Agent responded but command was invalid
```

## Limitations

### Current Limitations

1. **Single Connection**: Socket accepts one connection at a time (sequential processing)
2. **Interactive Mode Only**: Socket is not available in batch mode (`-c` flag)
3. **No History**: Each connection is independent (no persistent history)
4. **Buffer Size**: Response limited to 65KB per message (can be increased)

### Design Considerations

These limitations are intentional to:

- Keep the implementation simple and reliable
- Avoid race conditions with concurrent access
- Maintain consistency with the interactive REPL behavior
- Minimize resource usage

## Testing

Run the test suite to verify socket interface functionality:

```bash
python3 tests/test_socket_interface.py
```

Tests cover:

- Socket path construction
- File cleanup operations
- PID file operations
- Stale file detection
- Socket server creation
- Communication protocol

## Troubleshooting

### Socket File Not Found

**Problem**: `/run/user/<uid>/axe.sock` doesn't exist

**Solutions**:
1. Verify AXE is running in interactive mode (not with `-c` flag)
2. Check the PID file exists: `ls -l /run/user/$(id -u)/axe.pid`
3. Verify the process is running: `ps aux | grep axe.py`

### Permission Denied

**Problem**: Cannot connect to socket

**Solutions**:
1. Verify you're running as the same user that started AXE
2. Check socket file permissions: `ls -l /run/user/$(id -u)/axe.sock`
3. Ensure `/run/user/<uid>` directory exists

### Stale Files

**Problem**: "Another instance running" but no process exists

**Solutions**:
1. Manually remove files: `rm /run/user/$(id -u)/axe.{sock,pid}`
2. AXE should auto-clean stale files on next startup

## Future Enhancements

Potential improvements for future versions:

1. **Connection Queuing**: Support multiple simultaneous connections
2. **Authentication**: Optional token-based authentication
3. **Rate Limiting**: Prevent abuse from rapid requests
4. **WebSocket Bridge**: Enable remote agent communication
5. **Event Streaming**: Push notifications for agent actions
6. **Session Persistence**: Maintain state across connections

## Related Documentation

- [INTERACTIVE.md](../INTERACTIVE.md) - Full discussion and design rationale
- [AGENTS.md](../AGENTS.md) - Agent system overview
- [tests/test_socket_interface.py](../tests/test_socket_interface.py) - Test suite

## API Reference

### Functions

#### `start_socket_server() -> socket.socket`

Creates and binds a Unix domain socket for agent communication.

**Returns**: Non-blocking socket object

**Side Effects**: Creates `/run/user/<uid>/axe.sock`

#### `write_pid_file() -> None`

Writes the current process PID to the PID file.

**Side Effects**: Creates `/run/user/<uid>/axe.pid`

#### `check_and_cleanup_stale_files() -> None`

Checks for and cleans up stale socket/PID files from crashed sessions.

**Raises**: `RuntimeError` if another AXE instance is running

#### `cleanup_files() -> None`

Removes socket and PID files.

**Side Effects**: Deletes `/run/user/<uid>/axe.{sock,pid}`

#### `setup_signal_handlers() -> None`

Registers signal handlers for clean shutdown (SIGTERM, SIGINT, SIGHUP).

### Constants

```python
RUNTIME_DIR = f"/run/user/{os.getuid()}"
SOCKET_PATH = f"{RUNTIME_DIR}/axe.sock"
PID_PATH = f"{RUNTIME_DIR}/axe.pid"
```

## License

This feature is part of AXE and is licensed under the same terms. See [LICENSE](../LICENSE) for details.
