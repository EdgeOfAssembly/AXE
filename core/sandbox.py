"""
Bubblewrap Sandbox Manager for AXE (FINAL FIXED VERSION)
- Correct workspace binding + --chdir
- Works with --workspace /tmp/keypress (and multiple workspaces)
- Matches the manual command that succeeded
"""
import os
import shutil
import subprocess
from typing import List, Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .config import Config
def check_user_namespace_support() -> Tuple[bool, str]:
    """Basic user namespace check (kept from your original)."""
    try:
        result = subprocess.run(['unshare', '-U', 'true'], capture_output=True, timeout=2)
        if result.returncode == 0:
            return True, "User namespaces supported"
        return False, f"User namespaces not available: {result.stderr.decode()}"
    except Exception as e:
        return False, f"Namespace test failed: {e}"
class SandboxManager:
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
        # === WORKSPACE HANDLING (CLI always wins) ===
        if workspace_paths:
            self.workspace_paths = [os.path.abspath(p) for p in workspace_paths]
        else:
            # fallback to config or single workspace_path
            cfg_workspaces = self.sandbox_config.get('workspaces', [])
            if cfg_workspaces:
                self.workspace_paths = [os.path.abspath(ws.get('path', '.')) for ws in cfg_workspaces]
            else:
                self.workspace_paths = [self.workspace_path]
    def is_available(self) -> bool:
        return bool(shutil.which('bwrap'))
    def build_bwrap_command(self) -> List[str]:
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
        # Required pseudo-filesystems
        cmd.extend(['--proc', self.options.get('proc', '/proc')])
        cmd.extend(['--dev', self.options.get('dev', '/dev')])
        cmd.extend(['--tmpfs', self.options.get('tmpfs', '/tmp')])
        # Process options
        if self.options.get('die_with_parent', True):
            cmd.append('--die-with-parent')
        if self.options.get('new_session', True):
            cmd.append('--new-session')
        # === CRITICAL: Bind workspaces + chdir ===
        for wp in self.workspace_paths:
            if os.path.exists(wp):
                cmd.extend(['--bind', wp, wp])
            else:
                print(f"Warning: Workspace does not exist yet: {wp}")
        # Force chdir to the primary workspace (this was the missing piece!)
        if self.workspace_paths:
            primary = self.workspace_paths[0]
            cmd.extend(['--chdir', primary])
        # Host binds (from your axe.yaml)
        for path in self.host_binds.get('readonly', []):
            if os.path.exists(path):
                cmd.extend(['--ro-bind', path, path])
        for path in self.host_binds.get('writable', []):
            if os.path.exists(path):
                cmd.extend(['--bind', path, path])
        # === DEBUG: Show the actual command AXE is using ===
        print("DEBUG bwrap command:", " ".join(cmd))
        return cmd
    def run(self, cmd: str, timeout: int = 300) -> Tuple[bool, str]:
        if not self.enabled or not self.is_available():
            # Fallback when sandbox disabled
            try:
                result = subprocess.run(
                    ['/bin/sh', '-c', cmd],
                    cwd=self.workspace_paths[0] if self.workspace_paths else self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                output = result.stdout
                if result.stderr:
                    output += f"\n[stderr]: {result.stderr}"
                return result.returncode == 0, output
            except Exception as e:
                return False, f"Execution error: {e}"
        # Sandboxed execution
        bwrap_cmd = self.build_bwrap_command()
        bwrap_cmd.extend(['/bin/sh', '-c', cmd])
        try:
            result = subprocess.run(
                bwrap_cmd,
                cwd=self.workspace_path,   # only for host-side reference
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            return result.returncode == 0, output
        except Exception as e:
            return False, f"Sandbox error: {e}"
    def is_tool_blacklisted(self, tool: str) -> bool:
        return os.path.basename(tool) in self.tool_blacklist