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
    
    Uses multiple methods for robust detection:
    1. Check /proc/sys/kernel/unprivileged_userns_clone (Debian/Ubuntu)
    2. Check /proc/sys/user/max_user_namespaces (most Linux)
    3. Try to actually create a user namespace (definitive test)
    
    Returns:
        Tuple of (supported: bool, message: str)
    """
    # Method 1: Check unprivileged_userns_clone (Debian/Ubuntu specific)
    try:
        with open('/proc/sys/kernel/unprivileged_userns_clone', 'r') as f:
            if f.read().strip() == '0':
                return False, "User namespaces disabled (unprivileged_userns_clone=0)"
    except (FileNotFoundError, PermissionError):
        pass  # File doesn't exist or can't read, try other methods
    
    # Method 2: Check max_user_namespaces
    try:
        with open('/proc/sys/user/max_user_namespaces', 'r') as f:
            max_ns = int(f.read().strip())
            if max_ns == 0:
                return False, "User namespaces disabled (max_user_namespaces=0)"
    except (FileNotFoundError, PermissionError, ValueError):
        pass  # File doesn't exist or can't read, try other methods
    
    # Method 3: Actually try to create a user namespace (definitive test)
    # This is the most reliable way - try to run 'unshare -U true'
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
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return False, f"User namespaces not available: {error_msg}"
    except FileNotFoundError:
        # unshare not available, check if we're in a container/restricted env
        return False, "Cannot test user namespaces (unshare command not found)"
    except subprocess.TimeoutExpired:
        return False, "User namespace test timed out"
    except Exception as e:
        return False, f"User namespace test failed: {e}"


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
            # Note: Mount namespace is automatically created with user namespace
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
            
            # Check for common error messages that indicate sandbox can't be created
            if result.returncode != 0:
                error_output = result.stderr.lower()
                if ('permission denied' in error_output or 
                    'operation not permitted' in error_output or
                    'failed rtm_newaddr' in error_output):
                    # Sandbox can't be created in this environment
                    # This is expected in some CI environments or containers
                    return False, f"Sandbox not supported in this environment: {result.stderr}"
            
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
