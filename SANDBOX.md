# Bubblewrap Sandbox Security Model

## Overview

AXE now supports a **bubblewrap-based sandbox** that provides secure, isolated command execution. This replaces the traditional whitelist-based security model with a **default-allow** approach inside a hardened sandbox environment.

## Key Features

### 1. Default-Allow Execution
- **Inside sandbox**: All tools are allowed by default
- **Optional blacklist**: Block specific dangerous commands if needed
- **Host protection**: Host filesystem remains protected via namespace isolation

### 2. Linux Namespace Isolation
- **User namespace**: Commands run as root inside sandbox, unprivileged outside
- **Mount namespace**: Private filesystem view, only explicitly bound paths visible
- **PID namespace**: Process isolation - sandbox can't see host processes
- **Network namespace**: Optional network isolation (disabled by default for convenience)
- **IPC/UTS/CGroup namespaces**: Additional isolation layers

### 3. Filesystem Access Control
- **Workspace writable**: Project directory is read-write inside sandbox
- **System paths read-only**: `/usr`, `/lib`, `/bin`, `/etc` exposed read-only for tools
- **Hidden paths**: `~/.ssh`, `/root`, etc. completely inaccessible from sandbox

## Requirements

- **Linux operating system** (bubblewrap uses Linux-specific features)
- **bubblewrap package** installed:
  ```bash
  # Ubuntu/Debian
  sudo apt install bubblewrap
  
  # Fedora/RHEL
  sudo dnf install bubblewrap
  
  # Arch Linux
  sudo pacman -S bubblewrap
  ```

## Configuration

### Enabling Sandbox Mode

Edit `axe.yaml` and set `sandbox.enabled: true`:

```yaml
sandbox:
  enabled: true  # Enable sandbox mode
  runtime: bubblewrap
  
  # Workspace configuration
  workspaces:
    - path: .  # Project directory (writable)
      writable: true
  
  # Host directories to expose
  host_binds:
    readonly:
      - /usr
      - /lib
      - /lib64
      - /bin
      - /etc
      - /run
      - /sys
    writable: []  # Rarely needed
    none:  # Completely hidden from sandbox
      - ~/.ssh
      - ~/.gnupg
      - /root
  
  # Optional tool blacklist
  tool_blacklist: []
  # Example: ['rm', 'dd', 'mkfs', 'fdisk']
  
  # Namespace isolation
  namespaces:
    user: true
    mount: true
    pid: true
    uts: true
    network: false  # Set true for network isolation
    ipc: true
    cgroup: true
  
  # Additional options
  options:
    new_session: true
    die_with_parent: true
    proc: /proc
    dev: /dev
    tmpfs: /tmp
```

### Backward Compatibility

If `sandbox.enabled: false` or bubblewrap is not installed, AXE falls back to the legacy **whitelist mode**. Existing configurations continue to work without changes.

## Usage Examples

### Example 1: Default Sandbox Mode

```yaml
sandbox:
  enabled: true
  # Default configuration allows most operations safely
```

This configuration:
- ✅ Allows all tools inside sandbox
- ✅ Protects host filesystem (read-only)
- ✅ Workspace is writable
- ✅ System paths available for tools
- ❌ Cannot access `~/.ssh`, `/root`, etc.

### Example 2: Restricted Sandbox with Blacklist

```yaml
sandbox:
  enabled: true
  tool_blacklist:
    - rm      # Block file deletion
    - dd      # Block disk operations
    - mkfs    # Block filesystem creation
    - fdisk   # Block partition editing
```

This configuration:
- ✅ Most tools allowed
- ❌ Dangerous commands blocked even inside sandbox
- Useful for untrusted code execution

### Example 3: Network-Isolated Sandbox

```yaml
sandbox:
  enabled: true
  namespaces:
    network: true  # Enable network isolation
```

This configuration:
- ✅ Full isolation including network
- ❌ No network access (only loopback)
- Useful for analyzing potentially malicious code

## Security Boundaries

### What Sandbox Protects

✅ **Host filesystem** - Only bound paths accessible, rest hidden  
✅ **System processes** - PID isolation prevents process enumeration  
✅ **User credentials** - `~/.ssh`, `~/.gnupg` completely hidden  
✅ **Root access** - Commands run unprivileged despite appearing as root inside  
✅ **TTY attacks** - `new_session` prevents terminal control escape  

### What Sandbox Doesn't Protect (by design)

⚠️ **Workspace contents** - Workspace is writable, code can modify project files  
⚠️ **Network access** - Default config allows network (set `network: true` to isolate)  
⚠️ **CPU/memory** - No resource limits (use cgroups separately if needed)  

### Known Limitations

- **Linux-only**: Requires Linux kernel with namespace support
- **No block devices**: Cannot mount ext4/ntfs images (bubblewrap restriction)
- **FUSE supported**: FUSE filesystems work via `/dev/fuse`
- **Requires bubblewrap**: Fallback to whitelist mode if not installed

## Testing

Run the test suite:

```bash
cd /home/runner/work/AXE/AXE
python3 tests/test_sandbox.py
```

All tests should pass:
- Config parsing tests
- Command generation tests  
- Blacklist validation tests
- Integration tests (if bwrap installed)
- Backward compatibility tests

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│           ToolRunner (tool_runner.py)       │
│  ┌─────────────────────────────────────┐   │
│  │ Sandbox Mode          Whitelist Mode│   │
│  │ (default-allow)       (default-deny)│   │
│  └──────┬─────────────────────┬─────────┘   │
│         │                     │              │
│         v                     v              │
│  ┌─────────────┐      ┌─────────────┐       │
│  │ SandboxMgr  │      │  Whitelist  │       │
│  │  (sandbox)  │      │   Check     │       │
│  └──────┬──────┘      └─────────────┘       │
│         │                                    │
└─────────┼────────────────────────────────────┘
          │
          v
   ┌──────────────┐
   │  bubblewrap  │
   │    (bwrap)   │
   └──────┬───────┘
          │
          v
   ┌──────────────────┐
   │ Isolated Sandbox │
   │  - Namespaces    │
   │  - Bind mounts   │
   │  - Process isol. │
   └──────────────────┘
```

### Key Files

- **`core/sandbox.py`**: SandboxManager implementation
- **`core/tool_runner.py`**: Integration with ToolRunner
- **`core/constants.py`**: Default sandbox configuration
- **`axe.yaml`**: User configuration
- **`tests/test_sandbox.py`**: Test suite

## Migration Guide

### From Whitelist to Sandbox

**Before (whitelist mode):**
```yaml
tools:
  build: [gcc, make, cmake]
  python: [python3, pip]
  # Must list every tool explicitly
```

**After (sandbox mode):**
```yaml
sandbox:
  enabled: true
  # All tools available, optionally blacklist dangerous ones
  tool_blacklist: [rm, dd]
```

Benefits:
- ✅ No more approval prompts for unlisted tools
- ✅ Better agent autonomy
- ✅ Same or better security (namespace isolation)
- ✅ Easier configuration

## Troubleshooting

### "bubblewrap not available, falling back to whitelist mode"

**Cause**: bubblewrap not installed  
**Fix**: Install bubblewrap package (see Requirements section)

### "Sandbox execution error: ..."

**Cause**: Permission issue or invalid configuration  
**Fix**: Check that workspace path exists and is accessible

### Commands work in whitelist mode but not sandbox mode

**Cause**: Tool might be blacklisted or path not bound  
**Fix**: 
- Check `tool_blacklist` in config
- Ensure required system paths in `host_binds.readonly`

### "Permission denied" errors inside sandbox

**Cause**: Path not bound or bound as read-only  
**Fix**: Add path to `host_binds.writable` or ensure workspace contains needed files

## Manual Testing

On a system with bubblewrap installed:

```bash
# Run manual test script
bash /tmp/test_sandbox_manual.sh
```

This script tests:
1. Echo command execution
2. File operations in workspace
3. Pipe commands
4. Isolation verification (cannot access /root)
5. Workspace writability

## References

- **Bubblewrap GitHub**: https://github.com/containers/bubblewrap
- **Linux Namespaces**: `man 7 namespaces`
- **Bubblewrap Manual**: `man 1 bwrap`

## Future Enhancements

Potential improvements for future versions:

- [ ] Resource limits (CPU, memory) via cgroups
- [ ] Multiple concurrent sandboxes
- [ ] Sandbox profiles (restrictive, standard, permissive)
- [ ] Audit logging of sandbox operations
- [ ] Docker/Podman backend support
- [ ] Windows sandbox support (separate implementation)
