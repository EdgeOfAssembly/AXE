"""
Bubblewrap Sandbox Manager for AXE.
Provides secure, isolated execution environments using Linux namespaces
via bubblewrap (bwrap). Implements default-allow model inside sandbox
with optional tool blacklisting.
"""
import os
import shutil
import subprocess
from typing import List, Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .config import Config
def check_user_namespace_support() -> Tuple[bool, str]:
    """
    Check if user namespaces are supported in the current environment.
    Uses multiple methods for robust detection.
    """
    # Method 1: Check unprivileged_userns_clone (Debian/Ubuntu style)
    try:
        with open('/proc/sys/kernel/unprivileged_userns_clone', 'r') as f:
            if f.read().strip() == '0':
                return False, "User namespaces disabled (unprivileged_userns_clone=0)"
    except (FileNotFoundError, PermissionError):
        pass
    # Method 2: Check max_user_namespaces
    try:
        with open('/proc/sys/user/max_user_namespaces', 'r') as f:
            max_ns = int(f.read().strip())
            if max_ns == 0:
                return False, "User namespaces disabled (max_user_namespaces=0)"
    except (FileNotFoundError, PermissionError, ValueError):
        pass
    # Method 3: Try unshare -U true (definitive basic test)
    try:
        result = subprocess.run(
            ['unshare', '-U', 'true'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return True, "User namespaces supported (unshare test passed)"
        else:
            error_msg = result.stderr.strip() or "Unknown error"
            return False, f"User namespaces not available: {error_msg}"
    except FileNotFoundError:
        return False, "unshare command not found"
    except subprocess.TimeoutExpired:
        return False, "User namespace test timed out"
    except Exception as e:
        return False, f"User namespace test failed: {e}"
class SandboxManager:
    """
    Manages bubblewrap sandbox lifecycle and command execution.
    """
    def __init__(self, config: 'Config', workspace_path: str, workspace_paths: Optional[List[str]] = None):
        self.config = config
        self.workspace_path = os.path.abspath(workspace_path)
        self.sandbox_config = config.get('sandbox', default={})
        self.enabled = self.sandbox_config.get('enabled', False)
        self.runtime = self.sandbox_config.get('runtime', 'bubblewrap')
        self.tool_blacklist = set(self.sandbox_config.get('tool_blacklist', []))
        self.namespaces = self.sandbox_config.get('namespaces', {})
        self.options = self.sandbox_config.get('options', {})
        self.host_binds = self.sandbox_config.get('host_binds', {})
        # Handle workspace paths (CLI/override > config)
        if workspace_paths:
            self.workspace_paths = [os.path.abspath(wp) for wp in workspace_paths]
        else:
            config_workspaces = self.sandbox_config.get('workspaces', [])
            if config_workspaces:
                self.workspace_paths = []
                for ws in config_workspaces:
                    path = ws.get('path', '.')
                    self.workspace_paths.append(os.path.abspath(path))
            else:
                self.workspace_paths = [self.workspace_path]
    def is_available(self) -> bool:
        """Check if bubblewrap is installed and usable."""
        return bool(shutil.which('bwrap'))
    def check_capability(self) -> Tuple[bool, str]:
        """Test if bubblewrap can run a trivial command with our mounts."""
        if not self.is_available():
            return False, "Bubblewrap binary not found"
        cmd = [
            'bwrap',
            '--unshare-user-try',
            '--ro-bind', '/bin', '/bin',
            '--ro-bind', '/lib', '/lib',
            '--ro-bind', '/lib64', '/lib64',
            '--ro-bind', '/usr', '/usr',
            '--tmpfs', '/tmp',
            'true'
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                return True, "Bubblewrap capability test passed"
            else:
                msg = result.stderr.strip() or "Unknown failure"
                return False, f"Bubblewrap test failed: {msg}"
        except Exception as e:
            return False, f"Capability check error: {e}"
    def build_bwrap_command(self) -> List[str]:
        """
        Build the bwrap command line from configuration.
        """
        cmd = ['bwrap']
        # Namespaces
        if self.namespaces.get('user', True):
            cmd.append('--unshare-user-try')
        if self.namespaces.get('pid', True):
            cmd.append('--unshare-pid')
        if self.namespaces.get('uts', True):
            cmd.append('--unshare-uts')
        if self.namespaces.get('ipc', True):
            cmd.append('--unshare-ipc')
        if self.namespaces.get('cgroup', True):
            cmd.append('--unshare-cgroup-try')
        if self.namespaces.get('network', False):
            cmd.append('--unshare-net')
        # Standard mounts
        if self.options.get('proc', '/proc'):
            cmd.extend(['--proc', self.options.get('proc')])
        if self.options.get('dev', '/dev'):
            cmd.extend(['--dev', self.options.get('dev')])
        if self.options.get('tmpfs', '/tmp'):
            cmd.extend(['--tmpfs', self.options.get('tmpfs')])
        # Process options
        if self.options.get('die_with_parent', True):
            cmd.append('--die-with-parent')
        if self.options.get('new_session', True):
            cmd.append('--new-session')
        # Bind all workspace paths (writable)
        for wp in self.workspace_paths:
            if os.path.exists(wp):
                cmd.extend(['--bind', wp, wp])
        # Read-only host binds
        for path in self.host_binds.get('readonly', []):
            if os.path.exists(path):
                cmd.extend(['--ro-bind', path, path])
        # Writable host binds (rare)
        for path in self.host_binds.get('writable', []):
            if os.path.exists(path):
                cmd.extend(['--bind', path, path])
        return cmd
    def run(self, cmd: str, timeout: int = 300) -> Tuple[bool, str]:
        """
        Execute command inside sandbox.
        """
        if not self.enabled or not self.is_available():
            return False, "Sandbox not enabled or bubblewrap unavailable"
        bwrap_cmd = self.build_bwrap_command()
        bwrap_cmd.extend(['/bin/sh', '-c', cmd])
        try:
            result = subprocess.run(
                bwrap_cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Sandbox execution error: {e}"
    def is_tool_blacklisted(self, tool: str) -> bool:
        base_tool = os.path.basename(tool)
        return base_tool in self.tool_blacklist