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


class SandboxManager:
    """
    Manages bubblewrap sandbox lifecycle and command execution.
    
    Key responsibilities:
    - Build bwrap command line from config
    - Execute commands inside sandbox
    - Handle sandbox lifecycle (setup/teardown)
    - Support multiple concurrent workspaces (future)
    """
    
    def __init__(self, config: 'Config', workspace_path: str):
        """
        Initialize sandbox manager.
        
        Args:
            config: Configuration object containing sandbox settings
            workspace_path: Path to workspace directory (project root)
        """
        self.config = config
        self.workspace_path = os.path.abspath(workspace_path)
        self.sandbox_config = config.get('sandbox', default={})
        
        # Extract configuration
        self.enabled = self.sandbox_config.get('enabled', False)
        self.runtime = self.sandbox_config.get('runtime', 'bubblewrap')
        self.tool_blacklist = set(self.sandbox_config.get('tool_blacklist', []))
        self.namespaces = self.sandbox_config.get('namespaces', {})
        self.options = self.sandbox_config.get('options', {})
        self.host_binds = self.sandbox_config.get('host_binds', {})
        self.workspaces = self.sandbox_config.get('workspaces', [])
    
    def is_available(self) -> bool:
        """
        Check if bubblewrap is installed and usable.
        
        Returns:
            True if bwrap is available, False otherwise
        """
        if self.runtime != 'bubblewrap':
            return False
        
        # Check if bwrap is in PATH
        bwrap_path = shutil.which('bwrap')
        if not bwrap_path:
            return False
        
        # Try to run bwrap with --version to verify it works
        try:
            result = subprocess.run(
                ['bwrap', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def build_bwrap_command(self) -> List[str]:
        """
        Build the bwrap command line from configuration.
        
        Returns:
            List of command arguments for bwrap
        """
        cmd = ['bwrap']
        
        # Namespace configuration
        if self.namespaces.get('user', True):
            # Try user namespace, but don't fail if unsupported
            cmd.append('--unshare-user-try')
        
        if self.namespaces.get('mount', True):
            cmd.append('--unshare-mount')
        
        if self.namespaces.get('pid', True):
            cmd.append('--unshare-pid')
        
        if self.namespaces.get('uts', True):
            cmd.append('--unshare-uts')
        
        if self.namespaces.get('ipc', True):
            cmd.append('--unshare-ipc')
        
        if self.namespaces.get('cgroup', True):
            cmd.append('--unshare-cgroup-try')
        
        if self.namespaces.get('network', False):
            # Network isolation - only loopback available
            cmd.append('--unshare-net')
        
        # Process options
        proc_path = self.options.get('proc', '/proc')
        if proc_path:
            cmd.extend(['--proc', proc_path])
        
        dev_path = self.options.get('dev', '/dev')
        if dev_path:
            cmd.extend(['--dev', dev_path])
        
        tmpfs_path = self.options.get('tmpfs', '/tmp')
        if tmpfs_path:
            cmd.extend(['--tmpfs', tmpfs_path])
        
        # Additional options
        if self.options.get('die_with_parent', True):
            cmd.append('--die-with-parent')
        
        if self.options.get('new_session', True):
            cmd.append('--new-session')
        
        # Bind workspace (writable)
        # The first workspace is the primary one
        if self.workspaces:
            workspace_config = self.workspaces[0]
            workspace_path = workspace_config.get('path', '.')
            if not os.path.isabs(workspace_path):
                workspace_path = os.path.join(self.workspace_path, workspace_path)
            workspace_path = os.path.abspath(workspace_path)
            
            if workspace_config.get('writable', True):
                # Bind workspace to itself inside sandbox (writable)
                cmd.extend(['--bind', workspace_path, workspace_path])
        else:
            # Default: bind workspace directory as writable
            cmd.extend(['--bind', self.workspace_path, self.workspace_path])
        
        # Bind host directories (read-only by default)
        readonly_binds = self.host_binds.get('readonly', [])
        for path in readonly_binds:
            # Skip paths that don't exist
            if not os.path.exists(path):
                continue
            # Bind read-only
            cmd.extend(['--ro-bind', path, path])
        
        # Writable host binds (rarely needed, but supported)
        writable_binds = self.host_binds.get('writable', [])
        for path in writable_binds:
            if not os.path.exists(path):
                continue
            cmd.extend(['--bind', path, path])
        
        # Hidden paths (in 'none' list) are simply not bound, so they're inaccessible
        # No action needed - bwrap starts with empty filesystem except what we bind
        
        return cmd
    
    def run(self, cmd: str, timeout: int = 300) -> Tuple[bool, str]:
        """
        Execute command inside sandbox.
        
        Args:
            cmd: Shell command to execute
            timeout: Maximum execution time in seconds (default: 300)
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        if not self.is_available():
            return False, "Bubblewrap not available"
        
        # Build bwrap command
        bwrap_cmd = self.build_bwrap_command()
        
        # Append shell invocation with the user command
        # Use /bin/sh as it's universally available
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
            
            success = result.returncode == 0
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Sandbox execution error: {e}"
    
    def is_tool_blacklisted(self, tool: str) -> bool:
        """
        Check if tool is in the blacklist.
        
        Args:
            tool: Tool name to check (base command name)
        
        Returns:
            True if tool is blacklisted, False otherwise
        """
        # Get base command name (handle paths)
        base_tool = os.path.basename(tool)
        return base_tool in self.tool_blacklist
