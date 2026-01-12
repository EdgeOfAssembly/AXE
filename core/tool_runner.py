"""
Tool Runner for AXE.

Manages tool execution with safety checks including:
- Whitelist-based command validation
- Forbidden path checking
- Support for shell operators (pipes, redirects, logical operators)
- Heredoc content parsing
- Automatic detection of shell vs direct execution
"""

import os
import re
import shlex
import subprocess
from typing import List, Tuple, Optional, TYPE_CHECKING

from utils.formatting import Colors, c

if TYPE_CHECKING:
    from .config import Config


class ToolRunner:
    """
    Manages tool execution with safety checks.

    This class provides secure command execution with:
    - Whitelist-based command validation
    - Forbidden path checking
    - Support for shell operators (pipes, redirects, logical operators)
    - Heredoc content parsing
    - Automatic detection of shell vs direct execution

    Key Features:
    - Validates commands against a whitelist before execution
    - Handles complex shell syntax (pipes, redirects, subshells, heredocs)
    - Prevents access to forbidden directories
    - Logs all command execution attempts
    - Supports dry-run mode for testing
    """

    # Shell operators that connect commands in a pipeline or sequence
    SHELL_OPERATORS = {'|', '&&', '||', ';'}

    # Redirect operators for I/O redirection
    REDIRECT_OPERATORS = {'>', '>>', '<', '2>', '2>>', '&>', '2>&1'}

    def __init__(self, config: 'Config', project_dir: str):
        """
        Initialize the ToolRunner.

        Args:
            config: Configuration object containing tool whitelist and forbidden paths
            project_dir: Base directory for command execution
        """
        self.config = config
        self.project_dir = os.path.abspath(project_dir)
        self.exec_log = os.path.join(project_dir, 'axe_exec.log')
        self.dry_run = False
        
        # Initialize sandbox manager if enabled
        self.sandbox_manager = None
        if config.get('sandbox', 'enabled', default=False):
            try:
                from .sandbox import SandboxManager
                self.sandbox_manager = SandboxManager(config, project_dir)
                if not self.sandbox_manager.is_available():
                    print(c("Warning: bubblewrap not available, falling back to whitelist mode", Colors.YELLOW))
                    self.sandbox_manager = None
            except ImportError as e:
                print(c(f"Warning: Failed to import sandbox module: {e}", Colors.YELLOW))
                self.sandbox_manager = None
        
        # Legacy whitelist mode (used when sandbox is disabled or unavailable)
        self.whitelist = config.get_tool_whitelist()

    def _strip_heredoc_content(self, cmd: str) -> str:
        """
        Remove heredoc content from command string to prevent content from being parsed as commands.

        ⚠️  CRITICAL: This function is for VALIDATION ONLY!
        The returned string should ONLY be used for command name extraction and operator parsing.
        """
        heredoc_start = re.compile(
            r'<<-?\s*([\'"]?)(\w+)\1',
            re.MULTILINE
        )

        result = cmd
        matches = list(heredoc_start.finditer(cmd))
        for match in reversed(matches):
            delimiter = match.group(2)

            line_end = cmd.find('\n', match.end())
            if line_end == -1:
                continue

            heredoc_content_start = line_end + 1

            close_pattern = re.compile(
                rf'^[ \t]*{re.escape(delimiter)}[ \t]*$',
                re.MULTILINE
            )
            close_match = close_pattern.search(cmd, heredoc_content_start)

            if close_match:
                heredoc_content_end = close_match.end()
                result = result[:heredoc_content_start] + result[heredoc_content_end:]

        result = re.sub(r'<<<\s*([\'"])[^\1]*?\1', '<<< ""', result)
        result = re.sub(r'<<<\s+\S+', '<<< ""', result)

        return result

    def _extract_commands_from_shell(self, cmd: str) -> List[str]:
        """
        Extract actual command names from a shell command string.
        Handles pipes, logical operators, redirects, heredocs, subshells, etc.
        """
        cleaned_cmd = self._strip_heredoc_content(cmd)
        pattern = r'\s*(\|\||&&|[|;])\s*'
        parts = re.split(pattern, cleaned_cmd)

        commands = []

        for part in parts:
            if part in self.SHELL_OPERATORS:
                continue

            part = part.strip()
            if not part:
                continue

            try:
                tokens = shlex.split(part)
            except ValueError:
                tokens = part.split()

            if not tokens:
                continue

            for token in tokens:
                token = token.strip('()')
                if not token:
                    continue

                if '<' in token or '>' in token:
                    redirect_pos = len(token)
                    redirect_ops_sorted = sorted(self.REDIRECT_OPERATORS, key=len, reverse=True)
                    for redirect_op in redirect_ops_sorted:
                        pos = token.find(redirect_op)
                        if pos != -1 and pos < redirect_pos:
                            redirect_pos = pos
                    if redirect_pos < len(token):
                        token = token[:redirect_pos]
                    if not token:
                        continue

                if '=' in token and not token.startswith(('>', '<', '2')):
                    eq_pos = token.index('=')
                    if eq_pos > 0 and token[:eq_pos].replace('_', '').isalnum():
                        continue

                if token in self.REDIRECT_OPERATORS:
                    continue

                if token.startswith('<<'):
                    continue

                cmd_name = os.path.basename(token)
                commands.append(cmd_name)
                break

        return commands

    def _needs_shell(self, cmd: str) -> bool:
        """Check if a command requires shell execution."""
        cleaned_cmd = self._strip_heredoc_content(cmd)

        for op in self.SHELL_OPERATORS:
            if op in cleaned_cmd:
                return True

        for op in self.REDIRECT_OPERATORS:
            if op in cleaned_cmd:
                return True

        if '<<' in cmd:
            return True

        if '$(' in cmd or '`' in cmd:
            return True

        if '{' in cmd and '}' in cmd:
            return True

        if '*' in cmd or '?' in cmd or '[' in cmd:
            return True

        return False

    def _check_forbidden_paths(self, cmd: str) -> Tuple[bool, str]:
        """Check if command accesses forbidden paths."""
        forbidden = self.config.get('directories', 'forbidden', default=[])

        for path in forbidden:
            expanded_path = os.path.expanduser(path)
            if expanded_path in cmd or path in cmd:
                return False, f"Command accesses forbidden path: {path}"

        return True, ""

    def is_tool_allowed(self, cmd: str) -> Tuple[bool, str]:
        """
        Check if a command (including pipelines) is allowed.

        This method validates commands against the whitelist and security rules.
        It uses _extract_commands_from_shell() which internally strips heredoc
        content for validation purposes only. The input `cmd` parameter is never
        modified and should be passed unchanged to run() for execution.

        Args:
            cmd: The complete shell command string to validate

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not cmd or not cmd.strip():
            return False, "Empty command"
        
        # Sandbox mode: check blacklist only
        if self.sandbox_manager:
            try:
                commands = self._extract_commands_from_shell(cmd)
            except Exception as e:
                return False, f"Failed to parse command: {e}"
            
            if not commands:
                return False, "No commands found in input"
            
            # Check each command against blacklist
            for command in commands:
                base_cmd = os.path.basename(command)
                if self.sandbox_manager.is_tool_blacklisted(base_cmd):
                    return False, f"Tool '{base_cmd}' is blacklisted"
            
            return True, "OK (sandbox mode)"
        
        # Legacy whitelist mode
        if '*' in self.whitelist:
            return True, "OK (wildcard allowed)"

        # Extract all command names from the shell string
        # NOTE: This uses _strip_heredoc_content() internally for parsing only
        # The original `cmd` remains unchanged and should be used for execution
        try:
            commands = self._extract_commands_from_shell(cmd)
        except Exception as e:
            return False, f"Failed to parse command: {e}"

        if not commands:
            return False, "No commands found in input"

        # Check each command against whitelist
        for command in commands:
            # Get base command name (handle paths like /usr/bin/grep)
            base_cmd = os.path.basename(command)

            if base_cmd not in self.whitelist:
                return False, f"Tool '{base_cmd}' not in whitelist"

        # Check for forbidden paths in the entire command
        forbidden = self.config.get('directories', 'forbidden', default=[])

        # Resolve forbidden directories to real absolute paths
        resolved_forbidden = []
        for forbidden_path in forbidden:
            expanded_forbidden = os.path.expanduser(forbidden_path)
            if not os.path.isabs(expanded_forbidden):
                expanded_forbidden = os.path.join(self.project_dir, expanded_forbidden)
            resolved_forbidden.append(os.path.realpath(os.path.abspath(expanded_forbidden)))

        # Parse all tokens from the command to check for forbidden paths
        try:
            # Split the command to get all parts for path checking
            all_parts = cmd.split()
            for part in all_parts:
                # Skip operators and redirects
                if part in self.SHELL_OPERATORS or part in self.REDIRECT_OPERATORS:
                    continue
                if part.startswith(('>', '<', '2>', '|', '&')):
                    continue

                # Simple prefix check for non-path-like arguments
                for forbidden_path in forbidden:
                    expanded = os.path.expanduser(forbidden_path)
                    if part.startswith(expanded) or part.startswith(forbidden_path):
                        return False, f"Access to '{forbidden_path}' forbidden"

                # Robust path-based check for arguments that look like paths
                if (os.path.sep in part or
                    (os.path.altsep and os.path.altsep in part) or
                    part.startswith(("~", "."))):
                    expanded_part = os.path.expanduser(part)
                    if not os.path.isabs(expanded_part):
                        expanded_part = os.path.join(self.project_dir, expanded_part)
                    resolved_part = os.path.realpath(os.path.abspath(expanded_part))
                    for forbidden_real in resolved_forbidden:
                        # Match the forbidden directory itself or any path under it
                        if (resolved_part == forbidden_real or
                            resolved_part.startswith(forbidden_real + os.path.sep)):
                            return False, f"Access to '{forbidden_real}' forbidden"
        except Exception:
            # If parsing fails, continue with basic validation
            pass

        return True, "OK"

    def _log_execution(self, cmd: str, success: bool, output: str) -> None:
        """Log command execution to file."""
        from datetime import datetime
        try:
            with open(self.exec_log, 'a') as f:
                timestamp = datetime.now().isoformat()
                status = "OK" if success else "FAIL"
                f.write(f"[{timestamp}] [{status}] {cmd}\n")
                if not success and output:
                    f.write(f"  Error: {output[:200]}\n")
        except Exception as e:
            # Logging failures should not interrupt tool execution; report and continue.
            try:
                print(c(f"Warning: failed to write to execution log: {e}", Colors.YELLOW))
            except Exception:
                # As a last resort, ignore any errors while reporting the logging failure.
                pass

    def run(self, cmd: str, dry_run: Optional[bool] = None) -> Tuple[bool, str]:
        """
        Run a command after validation.

        Args:
            cmd: Command to execute
            dry_run: Optional per-call override for dry-run behavior.
                If None, falls back to the instance's dry_run setting.

        Returns:
            Tuple of (success, output)
        """
        # Determine effective flags, allowing per-call overrides
        effective_dry_run = self.dry_run if dry_run is None else dry_run

        # Validate command using is_tool_allowed
        allowed, reason = self.is_tool_allowed(cmd)
        if not allowed:
            return False, f"Command validation failed: {reason}"

        # Dry run mode
        if effective_dry_run:
            return True, f"[DRY RUN] Would execute: {cmd}"

        # Execute command
        # If sandbox is enabled, delegate to sandbox manager
        if self.sandbox_manager:
            try:
                success, output = self.sandbox_manager.run(cmd, timeout=300)
                self._log_execution(cmd, success, output)
                return success, output
            except Exception as e:
                self._log_execution(cmd, False, str(e))
                return False, f"Sandbox execution error: {e}"
        
        # Legacy direct execution (whitelist mode)
        try:
            use_shell = self._needs_shell(cmd)

            if use_shell:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                try:
                    args = shlex.split(cmd)
                except ValueError:
                    args = cmd.split()

                result = subprocess.run(
                    args,
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"

            success = result.returncode == 0
            self._log_execution(cmd, success, output)

            return success, output

        except subprocess.TimeoutExpired:
            self._log_execution(cmd, False, "Timeout after 5 minutes")
            return False, "Command timed out after 5 minutes"
        except Exception as e:
            self._log_execution(cmd, False, str(e))
            return False, f"Execution error: {e}"
