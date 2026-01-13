"""
Shared Build Status System for AXE Multi-Agent Collaboration.

Provides a file-based system where all agents can:
1. See current build status (gcc, make, python output)
2. Track errors and warnings from build tools
3. Volunteer to fix issues when idle
4. Share diff patches instead of full code

This reduces token usage by:
- Using unified diffs instead of full file contents
- Centralizing build output so agents don't repeat commands
- Allowing agents to claim and coordinate error fixes
"""

import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class BuildStatus(Enum):
    """Build status states."""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    RUNNING = "running"
    UNKNOWN = "unknown"


@dataclass
class BuildError:
    """Represents a build error or warning."""
    file: str
    line: int
    column: int
    severity: str  # 'error', 'warning', 'note'
    message: str
    tool: str  # 'gcc', 'make', 'python', etc.
    claimed_by: Optional[str] = None  # Agent alias that claimed this fix
    fixed: bool = False


@dataclass
class DiffPatch:
    """Represents a unified diff patch."""
    file: str
    author: str  # Agent alias
    timestamp: str
    diff_content: str
    description: str


class SharedBuildStatusManager:
    """
    Manages shared build status file for multi-agent collaboration.
    
    Creates and maintains `.collab_build_status.md` in the workspace.
    """
    
    # Patterns for parsing build output
    GCC_ERROR_PATTERN = re.compile(
        r'^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s*(?P<severity>error|warning|note):\s*(?P<msg>.+)$',
        re.MULTILINE
    )
    PYTHON_ERROR_PATTERN = re.compile(
        r'^(?P<file>[^:]+):(?P<line>\d+):\s*(?P<msg>.+)$',
        re.MULTILINE
    )
    MAKE_ERROR_PATTERN = re.compile(
        r'^make(?:\[\d+\])?: \*\*\* \[(?P<target>[^\]]+)\] Error (?P<code>\d+)',
        re.MULTILINE
    )
    
    def __init__(self, workspace_dir: str):
        """
        Initialize the shared build status manager.
        
        Args:
            workspace_dir: Path to the workspace directory
        """
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.status_file = os.path.join(self.workspace_dir, '.collab_build_status.md')
        self.changes_file = os.path.join(self.workspace_dir, '.collab_changes.md')
        self._errors: List[BuildError] = []
        self._patches: List[DiffPatch] = []
        self._last_status = BuildStatus.UNKNOWN
        self._last_output = ""
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self) -> None:
        """Initialize the shared status and changes files."""
        if not os.path.exists(self.status_file):
            self._write_status_file()
        
        if not os.path.exists(self.changes_file):
            self._write_changes_file()
    
    def _write_status_file(self) -> None:
        """Write the build status file."""
        try:
            with open(self.status_file, 'w') as f:
                f.write("# Shared Build Status\n\n")
                f.write("This file is automatically updated with build output.\n")
                f.write("Agents can monitor this for errors/warnings and claim fixes.\n\n")
                f.write("---\n\n")
                f.write(f"## Last Build: {self._last_status.value.upper()}\n\n")
                f.write(f"**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if self._errors:
                    f.write("## Errors & Warnings\n\n")
                    f.write("| File | Line | Severity | Message | Claimed By | Fixed |\n")
                    f.write("|------|------|----------|---------|------------|-------|\n")
                    for err in self._errors:
                        claimed = err.claimed_by or "-"
                        fixed = "✓" if err.fixed else "-"
                        # Truncate long messages for table display
                        msg = err.message[:50] + "..." if len(err.message) > 50 else err.message
                        f.write(f"| {err.file} | {err.line} | {err.severity} | {msg} | {claimed} | {fixed} |\n")
                    f.write("\n")
                else:
                    f.write("## Errors & Warnings\n\nNo errors or warnings.\n\n")
                
                if self._last_output:
                    f.write("## Last Build Output\n\n")
                    f.write("```\n")
                    # Show last 500 lines max (increased from 100 for bigger shared view)
                    lines = self._last_output.split('\n')
                    if len(lines) > 500:
                        f.write(f"... ({len(lines) - 500} lines omitted)\n")
                        f.write('\n'.join(lines[-500:]))
                    else:
                        f.write(self._last_output)
                    f.write("\n```\n")
        except (OSError, IOError) as e:
            print(f"Warning: Could not write build status file: {e}")
    
    def _write_changes_file(self) -> None:
        """Write the changes/diff file."""
        try:
            with open(self.changes_file, 'w') as f:
                f.write("# Shared Code Changes (Diff Patches)\n\n")
                f.write("This file tracks code changes via unified diffs.\n")
                f.write("Using diffs instead of full files saves tokens.\n\n")
                f.write("---\n\n")
                
                if self._patches:
                    for patch in self._patches:
                        f.write(f"## [{patch.author}] {patch.file} - {patch.timestamp}\n\n")
                        f.write(f"**Description:** {patch.description}\n\n")
                        f.write("```diff\n")
                        f.write(patch.diff_content)
                        f.write("\n```\n\n")
                        f.write("---\n\n")
                else:
                    f.write("No changes recorded yet.\n\n")
                    f.write("**How to add changes:**\n")
                    f.write("1. Use `diff -u original.file modified.file` to generate a patch\n")
                    f.write("2. Call `add_diff_patch()` with the diff content\n")
                    f.write("3. Other agents can apply patches with `patch -p0 < patch.diff`\n")
        except (OSError, IOError) as e:
            print(f"Warning: Could not write changes file: {e}")
    
    def record_build_output(self, tool: str, output: str, exit_code: int) -> BuildStatus:
        """
        Record build output and extract errors/warnings.
        
        Args:
            tool: Build tool name ('gcc', 'make', 'python', etc.)
            output: Full output from the build command
            exit_code: Exit code from the build command
        
        Returns:
            BuildStatus indicating success/failure
        """
        self._last_output = output
        
        # Determine status based on exit code
        if exit_code == 0:
            # Check for warnings even in successful builds
            if 'warning' in output.lower():
                self._last_status = BuildStatus.WARNING
            else:
                self._last_status = BuildStatus.SUCCESS
        else:
            self._last_status = BuildStatus.FAILED
        
        # Parse errors and warnings
        self._errors = []
        
        if tool in ['gcc', 'g++', 'clang', 'clang++']:
            self._parse_gcc_output(output, tool)
        elif tool == 'make':
            self._parse_make_output(output, tool)
        elif tool in ['python', 'python3', 'pytest']:
            self._parse_python_output(output, tool)
        
        # Update the status file
        self._write_status_file()
        
        return self._last_status
    
    def _parse_gcc_output(self, output: str, tool: str) -> None:
        """Parse GCC/Clang output for errors and warnings."""
        for match in self.GCC_ERROR_PATTERN.finditer(output):
            error = BuildError(
                file=match.group('file'),
                line=int(match.group('line')),
                column=int(match.group('col')),
                severity=match.group('severity'),
                message=match.group('msg'),
                tool=tool
            )
            self._errors.append(error)
    
    def _parse_make_output(self, output: str, tool: str) -> None:
        """Parse Make output for errors."""
        # First parse any GCC errors in the output
        self._parse_gcc_output(output, 'gcc')
        
        # Then add make-specific errors
        for match in self.MAKE_ERROR_PATTERN.finditer(output):
            error = BuildError(
                file=match.group('target'),
                line=0,
                column=0,
                severity='error',
                message=f"Make target failed with code {match.group('code')}",
                tool=tool
            )
            self._errors.append(error)
    
    def _parse_python_output(self, output: str, tool: str) -> None:
        """Parse Python/pytest output for errors."""
        # Look for traceback patterns
        in_traceback = False
        current_file = ""
        current_line = 0
        
        for line in output.split('\n'):
            if 'Traceback' in line:
                in_traceback = True
            elif in_traceback:
                file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                if file_match:
                    current_file = file_match.group(1)
                    current_line = int(file_match.group(2))
                elif line.strip() and not line.startswith(' '):
                    # This is likely the error message
                    if current_file:
                        error = BuildError(
                            file=current_file,
                            line=current_line,
                            column=0,
                            severity='error',
                            message=line.strip(),
                            tool=tool
                        )
                        self._errors.append(error)
                    in_traceback = False
                    current_file = ""
                    current_line = 0
        
        # Also check for pytest-style failures
        for match in re.finditer(r'FAILED\s+(\S+)::(\S+)', output):
            error = BuildError(
                file=match.group(1),
                line=0,
                column=0,
                severity='error',
                message=f"Test {match.group(2)} failed",
                tool=tool
            )
            self._errors.append(error)
    
    def get_unclaimed_errors(self) -> List[BuildError]:
        """
        Get list of errors/warnings not yet claimed by any agent.
        
        Returns:
            List of unclaimed BuildError objects
        """
        return [e for e in self._errors if not e.claimed_by and not e.fixed]
    
    def claim_error_fix(self, error_index: int, agent_alias: str) -> bool:
        """
        Claim an error for fixing by an agent.
        
        Args:
            error_index: Index of the error in the errors list
            agent_alias: Alias of the agent claiming the fix
        
        Returns:
            True if successfully claimed, False otherwise
        """
        if 0 <= error_index < len(self._errors):
            if not self._errors[error_index].claimed_by:
                self._errors[error_index].claimed_by = agent_alias
                self._write_status_file()
                return True
        return False
    
    def mark_error_fixed(self, error_index: int) -> bool:
        """
        Mark an error as fixed.
        
        Args:
            error_index: Index of the error in the errors list
        
        Returns:
            True if successfully marked, False otherwise
        """
        if 0 <= error_index < len(self._errors):
            self._errors[error_index].fixed = True
            self._write_status_file()
            return True
        return False
    
    def add_diff_patch(self, file: str, author: str, diff_content: str, 
                       description: str) -> None:
        """
        Add a diff patch to the shared changes file.
        
        Args:
            file: File that was changed
            author: Agent alias that made the change
            diff_content: Unified diff content
            description: Brief description of the change
        """
        patch = DiffPatch(
            file=file,
            author=author,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            diff_content=diff_content,
            description=description
        )
        self._patches.append(patch)
        
        # Keep only last 50 patches (increased from 20 for bigger shared view)
        if len(self._patches) > 50:
            self._patches = self._patches[-50:]
        
        self._write_changes_file()
    
    def get_recent_patches(self, limit: int = 10) -> List[DiffPatch]:
        """
        Get recent diff patches.
        
        Args:
            limit: Maximum number of patches to return
        
        Returns:
            List of recent DiffPatch objects
        """
        return self._patches[-limit:]
    
    def generate_diff(self, original_content: str, modified_content: str, 
                      filename: str) -> str:
        """
        Generate a unified diff between two versions of content.
        
        Args:
            original_content: Original file content
            modified_content: Modified file content
            filename: Name of the file for the diff header
        
        Returns:
            Unified diff string
        """
        import difflib
        
        original_lines = original_content.splitlines(keepends=True)
        modified_lines = modified_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f'a/{filename}',
            tofile=f'b/{filename}',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def get_status_summary(self) -> str:
        """
        Get a brief summary of build status for agents.
        
        Returns:
            Summary string for inclusion in agent prompts
        """
        unclaimed = self.get_unclaimed_errors()
        
        summary = f"Build Status: {self._last_status.value.upper()}\n"
        summary += f"Total Errors/Warnings: {len(self._errors)}\n"
        summary += f"Unclaimed Issues: {len(unclaimed)}\n"
        
        if unclaimed:
            summary += "\nUnclaimed issues available for fixing:\n"
            for i, err in enumerate(unclaimed[:5]):  # Show first 5
                summary += f"  [{i}] {err.file}:{err.line} - {err.severity}: {err.message[:60]}\n"
            if len(unclaimed) > 5:
                summary += f"  ... and {len(unclaimed) - 5} more\n"
        
        return summary
    
    def read_status_file(self) -> str:
        """Read the current build status file content."""
        try:
            with open(self.status_file, 'r') as f:
                return f.read()
        except (OSError, IOError):
            return ""
    
    def read_changes_file(self) -> str:
        """Read the current changes file content."""
        try:
            with open(self.changes_file, 'r') as f:
                return f.read()
        except (OSError, IOError):
            return ""


def run_build_command(command: str, workspace_dir: str, 
                      build_manager: SharedBuildStatusManager) -> Tuple[bool, str]:
    """
    Run a build command and record its output to the shared status.
    
    Args:
        command: Build command to run
        workspace_dir: Directory to run command in
        build_manager: SharedBuildStatusManager instance
    
    Returns:
        Tuple of (success, output)
    """
    # Determine tool from command
    parts = command.split()
    if not parts:
        return False, "Empty command"
    
    tool = parts[0]
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = result.stdout + result.stderr
        exit_code = result.returncode
        
        # Record to shared status
        build_manager.record_build_output(tool, output, exit_code)
        
        return exit_code == 0, output
    except subprocess.TimeoutExpired:
        build_manager.record_build_output(tool, "Command timed out", 1)
        return False, "Command timed out after 5 minutes"
    except Exception as e:
        error_msg = f"Error running command: {e}"
        build_manager.record_build_output(tool, error_msg, 1)
        return False, error_msg
