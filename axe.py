#!/usr/bin/env python3
"""
AXE - Agent eXecution Engine
A terminal-based multiagent coding assistant for C, C++, Python, and reverse-engineering.

Usage:
    axe.py                      # Interactive chat mode
    axe.py -c "task"            # Single command mode
    axe.py --config config.yaml # Custom config file
    
Chat commands:
    @agent task          - Send task to specific agent (e.g., @gpt analyze this)
    /agents              - List available agents
    /tools               - List available tools
    /dirs                - List accessible directories
    /config              - Show current config
    /history             - Show chat history
    /clear               - Clear chat history
    /help                - Show help
    /quit                - Exit
"""
import os
import sys
import argparse
import subprocess
import json
import atexit
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import time
import shutil
import re

# readline import enables command history in terminal (side effect import)
# Try gnureadline first (more feature-complete on some platforms), then readline
try:
    import gnureadline as readline  # noqa: F401
    HAS_READLINE = True
except ImportError:
    try:
        import readline  # noqa: F401
        HAS_READLINE = True
    except ImportError:
        HAS_READLINE = False
        # readline not available - command history will not work in terminal
        print("Note: readline not installed. Command history (↑/↓ arrows) disabled. Install with: pip install gnureadline")

# Optional imports - gracefully handle missing dependencies
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Note: PyYAML not installed. Using JSON config. Install with: pip install pyyaml")

try:
    import git
    HAS_GIT = True
except ImportError:
    HAS_GIT = False
    print("Note: GitPython not installed. Git features disabled. Install with: pip install gitpython")

# Import from new modular structure
from utils.formatting import Colors, c
from safety.rules import SESSION_RULES
from progression.xp_system import calculate_xp_for_level
from progression.levels import get_title_for_level, LEVEL_SUPERVISOR_ELIGIBLE
from database.agent_db import AgentDatabase, get_database_path
from models.metadata import (format_token_count, get_max_output_tokens, uses_responses_api, 
                             supports_reasoning_effort, get_default_reasoning_effort, validate_reasoning_effort)

# Import from core module (refactored)
from core.constants import (
    CHARS_PER_TOKEN,
    COLLAB_HISTORY_LIMIT,
    COLLAB_CONTENT_LIMIT,
    COLLAB_PASS_MULTIPLIER,
    COLLAB_SHARED_NOTES_LIMIT,
    SLEEP_REASON_TIMEOUT,
    SLEEP_REASON_DEGRADATION,
    DEGRADATION_CHECK_INTERVAL,
    AGENT_TOKEN_PASS,
    AGENT_TOKEN_TASK_COMPLETE,
    AGENT_TOKEN_BREAK_REQUEST,
    AGENT_TOKEN_EMERGENCY,
    AGENT_TOKEN_SPAWN,
    AGENT_TOKEN_STATUS,
    AGENT_TOKEN_GITHUB_READY,
    READ_BLOCK_PATTERN,
)
from core.config import Config
from core.agent_manager import AgentManager
from core.tool_runner import ToolRunner
from core.resource_monitor import start_resource_monitor
from core.session_preprocessor import SessionPreprocessor
from core.privilege_mapping import format_privileges_for_prompt
from core.constants import PRIVILEGE_PROMPT_SECTION

# Import from managers module (refactored)
from managers.sleep_manager import SleepManager
from managers.break_system import BreakSystem
from managers.dynamic_spawner import DynamicSpawner
from managers.emergency_mailbox import EmergencyMailbox

# Workshop dynamic analysis tools
try:
    from workshop import (
        ChiselAnalyzer, SawTracker, PlaneEnumerator, HammerInstrumentor,
        HAS_CHISEL, HAS_SAW, HAS_PLANE, HAS_HAMMER
    )
    HAS_WORKSHOP = True
except ImportError:
    HAS_WORKSHOP = False
    HAS_CHISEL = HAS_SAW = HAS_PLANE = HAS_HAMMER = False
    # Note: Saw and Plane are built-in tools. For full functionality: pip install angr (Chisel), frida-python psutil (Hammer)

# Experience/level constants, XP system, AgentDatabase, Config/AgentManager/ToolRunner,
# and manager classes (SleepManager, BreakSystem, etc.) are now in modular structure.
# See: progression/, database/, core/, managers/ directories.


class ResponseProcessor:
    """Processes agent responses and executes code blocks (READ, EXEC, WRITE)."""
    
    # Constants for file operations
    # Increased from 10KB to 100KB to handle large code files without truncation
    MAX_READ_SIZE = 100000  # Maximum bytes to read from a file (100KB)
    
    # Build tools that should have output recorded for shared status
    # Note: python/python3 excluded to avoid capturing non-build script output
    BUILD_TOOLS = {'gcc', 'g++', 'clang', 'clang++', 'make', 'cmake',
                   'pytest', 'pip', 'npm', 'cargo', 'go'}
    
    def __init__(self, config: Config, project_dir: str, tool_runner: 'ToolRunner',
                 workspace: 'SharedWorkspace' = None):
        self.config = config
        self.project_dir = os.path.abspath(project_dir)
        self.tool_runner = tool_runner
        self.workspace = workspace  # Optional: for recording build status
    
    def process_response(self, response: str, agent_name: str = "") -> str:
        """
        Process agent response and execute any code blocks.
        Returns the response with execution results appended.
        
        Supports both XML function calls and markdown code blocks.
        """
        import re
        from utils.xml_tool_parser import process_agent_response as process_xml_calls
        
        # First, check for XML function calls
        original_response, xml_results = process_xml_calls(response, self.project_dir, self)
        
        # Pattern to match code blocks in both inline and multiline formats:
        # - Inline: ```TYPE args``` (no newline, args on same line)
        # - Multiline: ```TYPE args\ncontent\n``` (newline separates args from content)
        # 
        # Key fixes:
        # - [^\n`]*? in args group prevents matching backticks (fixes inline format bug)
        # - (?:\n((?:(?!```).)*?))? makes newline+content optional (supports inline)
        # - (?!```) negative lookahead stops at first ``` (prevents wrong closing match)
        BLOCK_PATTERN = r'```(READ|EXEC|WRITE)\s*([^\n`]*?)(?:\n((?:(?!```).)*?))?```'
        
        matches = list(re.finditer(BLOCK_PATTERN, response, re.DOTALL))
        
        # Collect all results (both XML and markdown blocks)
        all_results = []
        
        # Add XML results first
        if xml_results:
            for xml_result in xml_results:
                all_results.append(f"\n{xml_result}")
        
        # Process markdown blocks if found
        if matches:
            # Process each block
            results = []
            for match in matches:
                block_type = match.group(1)
                args = match.group(2).strip()
                content = match.group(3).rstrip('\n') if match.group(3) else ''
                
                if block_type == 'READ':
                    # Sanitize filename: strip trailing backticks that may be included by accident
                    filename = (args or content).strip().rstrip('`')
                    result = self._handle_read(filename)
                    results.append(f"\n[READ {filename}]\n{result}")
                
                elif block_type == 'EXEC':
                    # Handle heredocs: if args has command start and content has heredoc body,
                    # combine them. Otherwise use args if present, else content.
                    if args and content:
                        # Both present: combine with newline (e.g., "cat << EOF" + "\nlines\nEOF")
                        command = args + '\n' + content
                    else:
                        # Only one present: use whichever exists
                        command = args or content
                    result = self._handle_exec(command)
                    results.append(f"\n[EXEC: {command}]\n{result}")
                
                elif block_type == 'WRITE':
                    # args contains the filename, content contains the file content
                    # Sanitize filename: strip trailing backticks that may be included by accident
                    filename = args.strip().rstrip('`')
                    # Basic validation: non-empty filename
                    if not filename:
                        results.append("\n[WRITE ERROR: Invalid or empty filename]")
                        continue
                    # Validate path using _resolve_project_path which handles:
                    # - Absolute paths within project directory (allowed)
                    # - Relative paths (allowed if within project)
                    # - Path traversal attempts (rejected)
                    # - Paths outside project directory (rejected)
                    #
                    # NOTE SECURITY LIMITATION:
                    # _resolve_project_path() currently relies on os.path.abspath(), which does *not*
                    # resolve symlinks. This means a symlink inside the project (e.g. "evil" -> /etc/passwd)
                    # could pass this check while pointing outside the project directory, enabling
                    # a potential symlink-based directory escape on WRITE.
                    #
                    # FOLLOW-UP: Harden _resolve_project_path() to use os.path.realpath() (as done in
                    # other parts of the codebase) and ensure that the resolved path is used for all
                    # file operations, to robustly prevent symlink-based escapes.
                    resolved_path = self._resolve_project_path(filename)
                    if resolved_path is None:
                        results.append("\n[WRITE ERROR: Invalid filename (path outside project directory)]")
                        continue
                    result = self._handle_write(filename, content)
                    results.append(f"\n[WRITE {filename}]\n{result}")
            
            all_results.extend(results)
        
        # Append all results to the original response
        if all_results:
            return response + "\n\n--- Execution Results ---" + "".join(all_results)
        
        return response
    
    def _resolve_project_path(self, filename: str) -> Optional[str]:
        """
        Resolve a filename against the project directory and ensure it
        does not escape the project directory.
        Returns the absolute path if valid, otherwise None.
        """
        project_root = os.path.abspath(self.project_dir)
        
        # If absolute path is provided, check if it's within project directory
        if os.path.isabs(filename):
            full_path = os.path.abspath(filename)
            # Allow if it's the project root or within it
            if full_path == project_root or full_path.startswith(project_root + os.sep):
                return full_path
            else:
                return None
        
        # Build an absolute path under the project directory
        full_path = os.path.abspath(os.path.join(self.project_dir, filename))

        # Ensure the resolved path is inside the project directory
        if not (full_path == project_root or full_path.startswith(project_root + os.sep)):
            return None

        return full_path
    
    def _handle_read(self, filename: str) -> str:
        """Handle READ block - read and return file content."""
        filepath = self._resolve_project_path(filename)
        if filepath is None:
            return f"ERROR: Access denied to {filename}"
        
        # Check if path is allowed
        allowed_dirs = self.config.get('directories', 'allowed', default=[])
        readonly_dirs = self.config.get('directories', 'readonly', default=[])
        forbidden_dirs = self.config.get('directories', 'forbidden', default=[])
        
        # Simple directory access check
        if not self._check_file_access(filepath, allowed_dirs + readonly_dirs, forbidden_dirs):
            return f"ERROR: Access denied to {filename}"
        
        try:
            if not os.path.exists(filepath):
                return f"ERROR: File not found: {filename}"
            
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(self.MAX_READ_SIZE)
                if len(content) >= self.MAX_READ_SIZE:
                    content += f"\n[... truncated at {self.MAX_READ_SIZE} bytes ...]"
                return content
        except Exception as e:
            return f"ERROR reading file: {e}"
    
    def _handle_exec(self, command: str) -> str:
        """Handle EXEC block - execute command via ToolRunner.
        
        If the command is a build tool (gcc, make, python, etc.), the output
        is recorded to the shared build status file for other agents to see.
        """
        success, output = self.tool_runner.run(command)
        
        # Record build output to shared status if it's a build tool
        if self.workspace is not None:
            try:
                # Extract the tool name from the command
                parts = command.strip().split()
                if parts:
                    tool = parts[0].split('/')[-1]  # Handle paths like /usr/bin/gcc
                    if tool in self.BUILD_TOOLS:
                        exit_code = 0 if success else 1
                        self.workspace.record_build_output(tool, output or "", exit_code)
            except Exception as e:
                # Log but don't fail - build status recording is optional
                print(c(f"Warning: Failed to record build output: {e}", Colors.DIM))
        
        if success:
            return output if output else "[Command executed successfully]"
        else:
            return f"ERROR: {output}"
    
    def _handle_write(self, filename: str, content: str) -> str:
        """Handle WRITE block - write content to file."""
        filepath = self._resolve_project_path(filename)
        if filepath is None:
            return f"ERROR: Access denied to {filename}"
        
        # Check if path is allowed for writing
        allowed_dirs = self.config.get('directories', 'allowed', default=[])
        forbidden_dirs = self.config.get('directories', 'forbidden', default=[])
        
        if not self._check_file_access(filepath, allowed_dirs, forbidden_dirs):
            return f"ERROR: Write access denied to {filename}"
        
        try:
            # Create directory if it doesn't exist (but not for files in root)
            dir_path = os.path.dirname(filepath)
            if dir_path:  # Only create if there's actually a directory path
                # Ensure directory path itself is permitted before creating it
                if not self._check_file_access(dir_path, allowed_dirs, forbidden_dirs):
                    return f"ERROR: Write access denied to directory for {filename}"
                os.makedirs(dir_path, exist_ok=True)
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"✓ File written successfully ({len(content)} bytes)"
        except Exception as e:
            return f"ERROR writing file: {e}"
    
    def _check_file_access(self, filepath: str, allowed: list, forbidden: list) -> bool:
        """Check if file access is allowed based on directory rules."""
        # Normalize the file path
        filepath = os.path.abspath(filepath)
        project_root = os.path.abspath(self.project_dir)

        def _is_within_dir(path: str, directory: str) -> bool:
            """Return True if 'path' is the same as or within 'directory' based on path components."""
            try:
                return os.path.commonpath([path, directory]) == directory
            except ValueError:
                # Different drives or otherwise incomparable paths
                return False
        
        # Check forbidden directories first
        for forbidden_dir in forbidden:
            forbidden_path = os.path.abspath(os.path.expanduser(forbidden_dir))
            if not os.path.isabs(forbidden_path):
                forbidden_path = os.path.join(project_root, forbidden_path)
            forbidden_path = os.path.abspath(forbidden_path)
            
            if _is_within_dir(filepath, forbidden_path):
                return False
        
        # Check if in allowed directories
        for allowed_dir in allowed:
            allowed_path = os.path.expanduser(allowed_dir)
            if not os.path.isabs(allowed_path):
                allowed_path = os.path.join(project_root, allowed_path)
            allowed_path = os.path.abspath(allowed_path)
            
            if _is_within_dir(filepath, allowed_path):
                return True
        
        # If no specific allowed directory matches, check if it's in project dir
        return _is_within_dir(filepath, project_root)


class ProjectContext:
    """Manages project context for agents."""
    
    def __init__(self, project_dir: str, config: Config):
        self.project_dir = os.path.abspath(project_dir)
        self.config = config
        self.extensions = config.get('code_extensions', default=[])
        
        if HAS_GIT:
            try:
                self.repo = git.Repo(project_dir)
            except Exception:
                self.repo = None
        else:
            self.repo = None
    
    def list_code_files(self, limit: int = 50) -> Tuple[List[str], int]:
        """List code files in project. Returns (files, total_count)."""
        files = []
        for ext in self.extensions:
            for path in Path(self.project_dir).rglob(f'*{ext}'):
                rel_path = path.relative_to(self.project_dir)
                files.append(str(rel_path))
        sorted_files = sorted(files)
        total = len(sorted_files)
        return sorted_files[:limit], total
    
    def get_file_content(self, filepath: str, max_bytes: int = 4096) -> str:
        """Get file content with size limit."""
        full_path = os.path.join(self.project_dir, filepath)
        
        if not os.path.exists(full_path):
            return f"File not found: {filepath}"
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read(max_bytes)
            
            # Try text decode
            try:
                text = content.decode('utf-8')
                # Check for newlines to identify text files (isprintable() excludes \n, \t)
                if '\n' in text or '\t' in text or text.isprintable():
                    return f"--- {filepath} ({len(content)} bytes) ---\n{text}"
            except UnicodeDecodeError:
                # Non-UTF-8 or otherwise undecodable content; fall back to binary hex dump
                pass
            
            # Binary hex dump
            hex_str = ' '.join(f'{b:02x}' for b in content[:64])
            return f"--- {filepath} (binary, {len(content)} bytes) ---\n{hex_str}..."
            
        except Exception as e:
            return f"Error reading {filepath}: {e}"
    
    def get_context_summary(self) -> str:
        """Get project context summary for agents."""
        files, total = self.list_code_files()
        
        summary = f"Project: {self.project_dir}\n"
        summary += f"Files ({len(files)}"
        if total > len(files):
            summary += f" of {total} total, showing first {len(files)}"
        summary += "):\n"
        
        for f in files[:10]:
            summary += f"  - {f}\n"
        
        if len(files) > 10:
            summary += f"  ... and {len(files) - 10} more in list\n"
        
        # Add git status if available
        if self.repo:
            try:
                status = self.repo.git.status('--short')
                if status:
                    summary += f"\nGit status:\n{status[:500]}\n"
            except Exception:
                # Git status is optional; ignore errors to avoid breaking context summary
                pass
        
        return summary


class SharedWorkspace:
    """Shared workspace for multi-agent collaboration.
    
    Provides shared files for agent coordination:
    - .collab_shared.md: General notes and communication
    - .collab_build_status.md: Build output, errors, warnings
    - .collab_changes.md: Diff patches for code changes
    """
    
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.shared_file = os.path.join(self.workspace_dir, '.collab_shared.md')
        self.backup_dir = os.path.join(self.workspace_dir, '.collab_backups')
        self._init_error = None
        
        # Create workspace dirs if needed
        try:
            os.makedirs(self.workspace_dir, exist_ok=True)
            os.makedirs(self.backup_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            self._init_error = f"Failed to create workspace directories: {e}"
            print(c(self._init_error, Colors.RED))
        
        # Initialize shared build status manager
        self.build_status = None
        if self._init_error is None:
            try:
                from managers.shared_build_status import SharedBuildStatusManager
                self.build_status = SharedBuildStatusManager(workspace_dir)
            except ImportError as e:
                # Log warning - build status sharing won't work without this
                print(c(f"Warning: SharedBuildStatusManager not available: {e}", Colors.YELLOW))
                print(c("  Build errors/warnings won't be shared automatically.", Colors.DIM))
        
        # Initialize shared notes file
        if not os.path.exists(self.shared_file) and self._init_error is None:
            try:
                with open(self.shared_file, 'w') as f:
                    f.write("# Collaborative Session Notes\n\n")
                    f.write("This file is shared between all agents. Use it to:\n")
                    f.write("- Share code snippets\n")
                    f.write("- Leave notes for other agents\n")
                    f.write("- Track progress on tasks\n\n")
                    f.write("**Related collaboration files:**\n")
                    f.write("- `.collab_build_status.md` - Build errors/warnings\n")
                    f.write("- `.collab_changes.md` - Diff patches for code changes\n\n")
                    f.write("---\n\n")
            except (OSError, PermissionError) as e:
                self._init_error = f"Failed to create shared notes file: {e}"
                print(c(self._init_error, Colors.RED))
    
    def _is_path_safe(self, filepath: str) -> bool:
        """Check if filepath is within the workspace directory (prevent path traversal)."""
        try:
            # Resolve to absolute path and check if it's within workspace
            abs_path = os.path.realpath(os.path.abspath(filepath))
            workspace_abs = os.path.realpath(os.path.abspath(self.workspace_dir))
            return abs_path.startswith(workspace_abs + os.sep) or abs_path == workspace_abs
        except (OSError, ValueError):
            return False
    
    def backup_file(self, filepath: str) -> str:
        """Create a backup of a file before modification."""
        if not os.path.exists(filepath):
            return ""
        
        # Security: Validate path is within workspace
        if not self._is_path_safe(filepath):
            return "Backup failed: Path outside workspace directory"
        
        # Use microseconds for uniqueness to prevent overwrites within same second
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.basename(filepath)
        backup_path = os.path.join(self.backup_dir, f"{filename}.{timestamp}.bak")
        
        try:
            shutil.copy2(filepath, backup_path)
            return backup_path
        except (OSError, IOError, shutil.Error) as e:
            return f"Backup failed: {e}"
    
    def read_shared_notes(self) -> str:
        """Read the shared notes file."""
        try:
            with open(self.shared_file, 'r') as f:
                return f.read()
        except (OSError, IOError, UnicodeError) as e:
            print(c(f"Failed to read shared notes: {e}", Colors.RED))
            return ""
    
    def append_to_shared(self, agent_name: str, content: str) -> None:
        """Append content to shared notes."""
        try:
            with open(self.shared_file, 'a') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n## [{agent_name}] - {timestamp}\n\n")
                f.write(content)
                f.write("\n\n---\n")
        except Exception as e:
            print(c(f"Failed to write to shared notes: {e}", Colors.RED))
    
    def list_files(self) -> List[str]:
        """List all files in workspace."""
        files = []
        try:
            for item in os.listdir(self.workspace_dir):
                if not item.startswith('.'):
                    files.append(item)
        except PermissionError:
            # Directory is not readable; return empty list to fail gracefully
            return []
        except OSError:
            # Any other unexpected error while listing files; also return empty list
            return []
        return sorted(files)
    
    def read_file(self, filename: str, max_bytes: int = 8192) -> str:
        """Read a file from workspace."""
        filepath = os.path.join(self.workspace_dir, filename)
        
        # Security: Validate path is within workspace (prevent path traversal)
        if not self._is_path_safe(filepath):
            return "Error: Path traversal not allowed"
        
        if not os.path.exists(filepath):
            return f"File not found: {filename}"
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read(max_bytes)
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return f"Binary file ({len(content)} bytes)"
        except (OSError, IOError) as e:
            return f"Error reading file: {e}"
    
    def write_file(self, filename: str, content: str) -> bool:
        """Write content to a file in workspace."""
        filepath = os.path.join(self.workspace_dir, filename)
        
        # Security: Validate path is within workspace (prevent path traversal)
        if not self._is_path_safe(filepath):
            print(c("Error: Path traversal not allowed", Colors.RED))
            return False
        
        # Backup existing file
        if os.path.exists(filepath):
            backup_result = self.backup_file(filepath)
            if isinstance(backup_result, str) and backup_result.startswith("Backup failed:"):
                print(c(f"Warning: {backup_result}", Colors.YELLOW))
                # Continue with write despite backup failure, but warn user
        
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        except (OSError, IOError) as e:
            print(c(f"Failed to write file: {e}", Colors.RED))
            return False
    
    def get_build_status_summary(self) -> str:
        """Get a summary of build status for agents to see.
        
        Returns a formatted string with:
        - Current build status (success/failed/warning)
        - List of unclaimed errors/warnings agents can fix
        - Brief summary of recent build output
        """
        if self.build_status is None:
            return ""
        
        try:
            return self.build_status.get_status_summary()
        except Exception as e:
            # Log error so build status issues are visible during debugging
            print(c(f"Warning: Error getting build status summary: {e}", Colors.DIM))
            return ""
    
    def record_build_output(self, tool: str, output: str, exit_code: int) -> None:
        """Record build output from a command execution.
        
        Args:
            tool: Build tool name (gcc, make, python, etc.)
            output: Full output from the command
            exit_code: Exit code from the command
        """
        if self.build_status is not None:
            try:
                self.build_status.record_build_output(tool, output, exit_code)
            except Exception as e:
                # Log but don't fail - build status is optional
                print(c(f"Warning: Failed to record build output: {e}", Colors.DIM))
    
    def claim_error_fix(self, error_index: int, agent_alias: str) -> bool:
        """Claim an error for fixing by an agent.
        
        Args:
            error_index: Index of the error to claim
            agent_alias: Alias of the agent claiming the fix
        
        Returns:
            True if successfully claimed
        """
        if self.build_status is not None:
            try:
                return self.build_status.claim_error_fix(error_index, agent_alias)
            except Exception as e:
                print(c(f"Warning: Failed to claim error fix: {e}", Colors.DIM))
                return False
        return False
    
    def mark_error_fixed(self, error_index: int) -> bool:
        """Mark an error as fixed.
        
        Args:
            error_index: Index of the error to mark as fixed
        
        Returns:
            True if successfully marked
        """
        if self.build_status is not None:
            try:
                return self.build_status.mark_error_fixed(error_index)
            except Exception as e:
                print(c(f"Warning: Failed to mark error fixed: {e}", Colors.DIM))
                return False
        return False


def is_genuine_task_completion(response: str) -> bool:
    """
    Check if agent is genuinely declaring task complete.
    
    Returns False for:
    - "TASK COMPLETE" inside <result> blocks (file content)
    - "TASK COMPLETE" inside quoted text
    - "TASK COMPLETE" in warnings/instructions
    - "TASK COMPLETE" inside [READ ...] blocks
    
    Returns True only for genuine declarations like:
    - "TASK COMPLETE: Here's what we accomplished..."
    - "✅ TASK COMPLETE"
    - "I declare TASK COMPLETE"
    - "THE TASK IS COMPLETE"
    """
    response_upper = response.upper()
    
    # Must contain task completion phrase (TASK COMPLETE or TASK IS COMPLETE)
    if 'TASK COMPLETE' not in response_upper and 'TASK IS COMPLETE' not in response_upper:
        return False
    
    # Remove content that should be ignored:
    cleaned = response
    
    # 1. Remove <result>...</result> blocks (file read outputs), handling possible nesting
    result_pattern = re.compile(r'<result>.*?</result>', flags=re.DOTALL | re.IGNORECASE)
    while True:
        new_cleaned = result_pattern.sub('', cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
    
    # 2. Remove <function_result>...</function_result> blocks, handling possible nesting
    function_result_pattern = re.compile(r'<function_result>.*?</function_result>', flags=re.DOTALL | re.IGNORECASE)
    while True:
        new_cleaned = function_result_pattern.sub('', cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
    
    # 3. Remove [READ filename] ... blocks
    # Don't stop at [[ tokens (agent tokens start with [[)
    cleaned = re.sub(READ_BLOCK_PATTERN, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 4. Remove markdown code blocks (```...```)
    cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
    
    # 5. Remove blockquotes (lines starting with >)
    cleaned = re.sub(r'^>.*$', '', cleaned, flags=re.MULTILINE)
    
    # 6. Remove content inside quotation marks containing task completion phrases
    cleaned = re.sub(
        r'"[^"]*TASK\s+(?:COMPLETE|IS\s+COMPLETE)[^"]*"|\'[^\']*TASK\s+(?:COMPLETE|IS\s+COMPLETE)[^\']*\'',
        '',
        cleaned,
        flags=re.IGNORECASE,
    )
    
    # Now check if task completion phrases still exist in cleaned content
    cleaned_upper = cleaned.upper()
    
    if 'TASK COMPLETE' not in cleaned_upper and 'TASK IS COMPLETE' not in cleaned_upper:
        return False
    
    # Additional validation: should be at start of line or after certain patterns
    # This catches genuine declarations vs passing mentions
    genuine_patterns = [
        r'^\s*✅?\s*TASK\s+COMPLETE',           # Starts line (with optional checkmark)
        r'TASK\s+COMPLETE\s*:',                  # Followed by colon (summary)
        r'TASK\s+COMPLETE\s*!',                  # Followed by exclamation
        r'I\s+DECLARE\s+TASK\s+COMPLETE',        # Explicit declaration
        r'MARKING\s+TASK\s+COMPLETE',            # Marking complete
        r'THE\s+TASK\s+IS\s+COMPLETE',           # Statement form
    ]
    
    for pattern in genuine_patterns:
        if re.search(pattern, cleaned_upper, re.MULTILINE):
            return True
    
    # If we get here, TASK COMPLETE exists but doesn't match genuine patterns
    # Be conservative - don't trigger on ambiguous cases
    return False


def detect_agent_token(response: str, token: str) -> tuple[bool, str]:
    """
    Detect unique agent communication tokens in response.
    
    Args:
        response: The agent's response text
        token: The token to search for (e.g., AGENT_TOKEN_PASS)
    
    Returns:
        Tuple of (found: bool, content: str)
        - found: Whether the token was detected
        - content: Extracted content after the token (empty for simple tokens)
    """
    if not response:
        return False, ""
    
    # Strip file content before checking for tokens (same logic as is_genuine_task_completion)
    cleaned = response
    
    # 1. Remove <result>...</result> blocks (file read outputs), handling possible nesting
    result_pattern = re.compile(r'<result>.*?</result>', flags=re.DOTALL | re.IGNORECASE)
    while True:
        new_cleaned = result_pattern.sub('', cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
    
    # 2. Remove <function_result>...</function_result> blocks, handling possible nesting
    function_result_pattern = re.compile(r'<function_result>.*?</function_result>', flags=re.DOTALL | re.IGNORECASE)
    while True:
        new_cleaned = function_result_pattern.sub('', cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
    
    # 3. Remove [READ filename] ... blocks
    # Don't stop at [[ tokens (agent tokens start with [[)
    cleaned = re.sub(READ_BLOCK_PATTERN, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 4. Remove markdown code blocks (```...```)
    cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
    
    # Now check for token in cleaned content
    if token in cleaned:
        # Extract content if token expects it (has trailing colon)
        if token.endswith(':'):
            try:
                start_idx = cleaned.index(token) + len(token)
                # Find the closing ]]
                end_idx = cleaned.index(']]', start_idx)
                content = cleaned[start_idx:end_idx].strip()
                return True, content
            except (ValueError, IndexError):
                # Malformed token, ignore
                return False, ""
        else:
            # Simple token without content
            return True, ""
    
    return False, ""


def check_agent_pass(response: str) -> bool:
    """Check if agent is passing their turn using unique token."""
    found, _ = detect_agent_token(response, AGENT_TOKEN_PASS)
    if found:
        return True
    
    # Backward compatibility: check old PASS format
    # Only for transition period - can be removed later
    non_empty_lines = [line.strip().upper() for line in response.splitlines() if line.strip()]
    return bool(non_empty_lines) and non_empty_lines[0] == 'PASS'


def check_agent_task_complete(response: str) -> tuple[bool, str]:
    """
    Check if agent is declaring task complete using unique token.
    
    Returns:
        Tuple of (is_complete: bool, summary: str)
    """
    found, summary = detect_agent_token(response, AGENT_TOKEN_TASK_COMPLETE)
    if found:
        return True, summary
    
    # Backward compatibility: check old TASK COMPLETE format
    # Only for transition period - can be removed later
    if is_genuine_task_completion(response):
        # Try to extract summary if present
        lines = response.split('\n')
        for line in lines:
            if 'TASK COMPLETE' in line.upper():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    return True, parts[1].strip()
                return True, "Task completed"
        return True, "Task completed"
    
    return False, ""


def check_agent_command(response: str, token: str) -> tuple[bool, str]:
    """
    Check for agent commands that include content (BREAK REQUEST, EMERGENCY, SPAWN).
    
    Returns:
        Tuple of (found: bool, content: str)
    """
    found, content = detect_agent_token(response, token)
    if found:
        return True, content
    
    # Backward compatibility for old format
    # Map token to old keyword
    old_keywords = {
        AGENT_TOKEN_BREAK_REQUEST: 'BREAK REQUEST:',
        AGENT_TOKEN_EMERGENCY: 'EMERGENCY:',
        AGENT_TOKEN_SPAWN: 'SPAWN:',
    }
    
    if token in old_keywords:
        old_keyword = old_keywords[token]
        if old_keyword in response.upper():
            try:
                start_idx = response.upper().index(old_keyword) + len(old_keyword)
                content = response[start_idx:].split('\n')[0].strip()
                return True, content
            except (ValueError, IndexError):
                return True, ""
    
    return False, ""


class CollaborativeSession:
    """
    Multi-agent collaborative session where models communicate and cooperate.
    
    Features:
    - Turn-based coordination (models take turns to avoid talking over each other)
    - Shared workspace for code and notes
    - Time limits/deadlines for tasks
    - Full conversation history visible to all agents
    - Phase 6: Mandatory sleep system
    - Phase 7: Degradation monitoring
    - Phase 8: Emergency mailbox
    - Phase 9: Break system
    - Phase 10: Dynamic spawning
    """
    
    def __init__(self, config: Config, agents: List[str], workspace_dir: str, 
                 time_limit_minutes: int = 30, db_path: Optional[str] = None,
                 github_enabled: bool = False):
        self.config = config
        self.agent_mgr = AgentManager(config)
        self.workspace = SharedWorkspace(workspace_dir)
        self.project_ctx = ProjectContext(workspace_dir, config)
        self.tool_runner = ToolRunner(config, workspace_dir)
        # Pass workspace to ResponseProcessor for build output recording
        self.response_processor = ResponseProcessor(config, workspace_dir, self.tool_runner, self.workspace)
        self.db = AgentDatabase(db_path)
        
        # Initialize Phase 6-10 systems
        self.sleep_manager = SleepManager(self.db)
        self.break_system = BreakSystem(self.db)
        self.emergency_mailbox = EmergencyMailbox()
        self.spawner = DynamicSpawner(self.db, config)
        
        # NEW: GitHub agent integration (completely optional)
        self.github_enabled = github_enabled
        self.github_agent = None
        if github_enabled:
            try:
                from core.github_agent import GitHubAgent
                self.github_agent = GitHubAgent(workspace_dir, enabled=True)
                if self.github_agent.repo_detected:
                    print(c("✓ GitHub agent mode enabled", Colors.GREEN))
                else:
                    print(c("⚠️  GitHub mode enabled but no git repo detected", Colors.YELLOW))
                    self.github_enabled = False
            except ImportError as e:
                print(c(f"⚠️  GitHub agent unavailable: {e}", Colors.YELLOW))
                self.github_enabled = False
        
        # Validate and set up agents with unique IDs and aliases
        self.agents = []
        self.agent_ids = {}  # Maps agent name to unique ID
        self.agent_aliases = {}  # Maps agent name to @alias
        self.spawned_agents = {}  # Maps agent name (UUID) to config dict for dynamically spawned agents
        
        for agent_name in agents:
            agent = self.agent_mgr.resolve_agent(agent_name)
            if agent and agent.get('provider') in self.agent_mgr.clients:
                self.agents.append(agent['name'])
                
                # Generate unique ID and alias
                agent_id = str(uuid.uuid4())
                model_name = agent.get('model', agent_name).replace('/', '-').replace('.', '-')
                agent_num = self.db.get_next_agent_number(model_name)
                alias = f"@{model_name}{agent_num}"
                
                self.agent_ids[agent['name']] = agent_id
                self.agent_aliases[agent['name']] = alias
                
                # Initialize agent in database
                self.db.save_agent_state(
                    agent_id=agent_id,
                    alias=alias,
                    model_name=agent.get('model', agent_name),
                    memory_dict={},
                    diffs=[],
                    error_count=0,
                    xp=0,
                    level=1
                )
                # Start work tracking immediately
                self.db.start_work_tracking(agent_id)
            else:
                print(c(f"Warning: Agent '{agent_name}' not available, skipping", Colors.YELLOW))
        
        if len(self.agents) < 2:
            raise ValueError("Need at least 2 available agents for collaboration")
        
        # Supervisor is the first agent (the one that started the session)
        self.supervisor_name = self.agents[0]
        self.supervisor_alias = "@boss"
        self.agent_aliases[self.supervisor_name] = self.supervisor_alias
        
        # Update supervisor in database with boss alias
        # XP must match level 40 - use calculate_xp_for_level to ensure consistency
        supervisor_id = self.agent_ids[self.supervisor_name]
        supervisor_xp = calculate_xp_for_level(LEVEL_SUPERVISOR_ELIGIBLE)
        self.db.save_agent_state(
            agent_id=supervisor_id,
            alias=self.supervisor_alias,
            model_name=self.agent_mgr.resolve_agent(self.supervisor_name).get('model', self.supervisor_name),
            memory_dict={},
            diffs=[],
            error_count=0,
            xp=supervisor_xp,
            level=LEVEL_SUPERVISOR_ELIGIBLE  # Supervisor starts at level 40
        )
        # Start work tracking for supervisor
        self.db.start_work_tracking(supervisor_id)
        
        # Session settings
        self.time_limit = time_limit_minutes * 60  # Convert to seconds
        self.start_time: Optional[datetime] = None
        self.conversation_history: List[dict] = []
        self.current_turn = 0
        self.task_description = ""
        self.is_running = False
    
    def _format_conversation_for_agent(self, agent_name: str) -> str:
        """Format conversation history for an agent to read."""
        if not self.conversation_history:
            return "No conversation yet."
        
        formatted = "=== CONVERSATION HISTORY ===\n\n"
        for entry in self.conversation_history[-COLLAB_HISTORY_LIMIT:]:
            role = entry.get('role', 'unknown')
            content = entry.get('content', '')[:COLLAB_CONTENT_LIMIT]
            timestamp = entry.get('timestamp', '')
            
            if role == 'user':
                formatted += f"[BOSS/USER] ({timestamp}):\n{content}\n\n"
            elif role == agent_name:
                formatted += f"[YOU/{role.upper()}] ({timestamp}):\n{content}\n\n"
            else:
                formatted += f"[{role.upper()}] ({timestamp}):\n{content}\n\n"
        
        formatted += "=== END CONVERSATION ===\n"
        return formatted
    
    def _get_system_prompt_for_collab(self, agent_name: str) -> str:
        """Generate collaborative system prompt for an agent."""
        other_agents = [a for a in self.agents if a != agent_name]
        
        # Get agent info
        agent_id = self.agent_ids.get(agent_name)
        alias = self.agent_aliases.get(agent_name, agent_name)
        state = self.db.load_agent_state(agent_id) if agent_id else None
        
        # Resolve agent config - check spawned agents first
        agent_config = None
        if agent_name in self.spawned_agents:
            agent_config = self.spawned_agents[agent_name]
        else:
            agent_config = self.agent_mgr.resolve_agent(agent_name)
        
        level_info = ""
        if state:
            level = state['level']
            xp = state['xp']
            title = get_title_for_level(level)
            level_info = f"\nYour Level: {level} ({xp} XP) - {title}"
        
        # Get context tokens and capabilities info
        context_tokens = agent_config.get('context_tokens', 'unknown') if agent_config else 'unknown'
        capabilities = agent_config.get('capabilities', []) if agent_config else []
        capabilities_str = ', '.join(capabilities) if capabilities else 'text'
        # Format context_tokens for display
        if isinstance(context_tokens, int):
            context_display = f"{context_tokens:,} tokens"
        else:
            context_display = "unknown tokens"
        model_info = f"\nYour Model: {agent_config.get('model', 'unknown')} | Context: {context_display} | Capabilities: {capabilities_str}" if agent_config else ""
        
        # Get list of workspace files with error handling
        try:
            workspace_files = self.workspace.list_files()
        except Exception:
            workspace_files = []
        
        # Get other agent aliases with their capabilities
        other_aliases = [self.agent_aliases.get(a, a) for a in other_agents]
        other_info_list = []
        for a in other_agents:
            a_alias = self.agent_aliases.get(a, a)
            # Check spawned agents first
            if a in self.spawned_agents:
                a_config = self.spawned_agents[a]
            else:
                a_config = self.agent_mgr.resolve_agent(a)
            if a_config:
                a_ctx = a_config.get('context_tokens', 0)
                a_caps = ', '.join(a_config.get('capabilities', ['text']))
                # Format context for display
                if isinstance(a_ctx, int) and a_ctx > 0:
                    ctx_display = f"{a_ctx:,} ctx"
                else:
                    ctx_display = "? ctx"
                other_info_list.append(f"{a_alias} ({ctx_display}, {a_caps})")
            else:
                other_info_list.append(a_alias)
        
        is_supervisor = (alias == "@boss")
        supervisor_note = "\n⚠️ You are the SUPERVISOR (@boss). You coordinate and oversee the team." if is_supervisor else ""
        
        # Build base prompt
        base_prompt = f"""You are {alias} (real name: {agent_name}), participating in a COLLABORATIVE CODING SESSION.{level_info}{model_info}{supervisor_note}

Other agents in this session: {', '.join(other_info_list)}

COLLABORATION RULES (READ CAREFULLY):
1. You are working TOGETHER on a shared task. Be cooperative, not competitive.
2. You can see the full conversation history - reference what others said.
3. Build on each other's work. If another agent wrote code, improve it or review it.
4. Be concise and focus on the most important details in each turn.
5. Use the SHARED WORKSPACE at: {self.workspace.workspace_dir}
6. If you modify files, explain what you changed and why.
7. Address other agents by their aliases: "Hey {other_aliases[0] if other_aliases else '@agent'}, I noticed..."
8. If you're done with your part, use the token: {AGENT_TOKEN_PASS}
9. When the task is complete, use: {AGENT_TOKEN_TASK_COMPLETE} summary of work ]]
10. Earn XP by completing tasks well. Level up to unlock new titles and privileges!
11. When introducing yourself, share your context window size and capabilities.

SPECIAL COMMANDS (use these exact tokens):
- Pass turn: {AGENT_TOKEN_PASS}
- Task complete: {AGENT_TOKEN_TASK_COMPLETE} your summary here ]]
- Request break: {AGENT_TOKEN_BREAK_REQUEST} coffee, need rest ]]
- Emergency: {AGENT_TOKEN_EMERGENCY} urgent message ]]
- Check status: {AGENT_TOKEN_STATUS}
"""

        # Add privilege section if enabled
        privilege_section = ""
        if PRIVILEGE_PROMPT_SECTION and state:
            privilege_section = "\n\n" + format_privileges_for_prompt(level, alias) + "\n"
        
        return base_prompt + privilege_section + """
FILE AND COMMAND OPERATIONS (CRITICAL - READ CAREFULLY):
To actually create/modify files or run commands, you MUST use these exact code block syntaxes.
Simply DESCRIBING what you did ("I created file.txt") does NOTHING - you must use the blocks below:

TO CREATE OR MODIFY FILES:
```WRITE filename.txt
your content here
multiple lines supported
```

TO READ FILES:
```READ filename.txt
```

TO RUN COMMANDS:
```EXEC your_command --with-args
```

⚠️ CRITICAL DISTINCTION:
❌ WRONG: "I created boss.txt with content X" (just text - NOTHING HAPPENS!)
✅ RIGHT: Use the ```WRITE boss.txt block above (file actually created)

Examples that WORK:
```WRITE hello.py
print("Hello from {alias}!")
```

```EXEC ls -la
```

```READ existing_file.txt
```

WORKSPACE INFO:
- Files: {', '.join(workspace_files) or 'empty'}
- Shared notes available at: .collab_shared.md

YOUR ROLE: {agent_config.get('role', 'Assistant') if agent_config else 'Assistant'}

Remember: Work as a TEAM. The human is watching and expects professional collaboration.
Follow the session rules to keep work productive and enjoyable for all agents."""
    
    def _time_remaining(self) -> int:
        """Get remaining time in seconds."""
        if not self.start_time:
            return self.time_limit
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return max(0, int(self.time_limit - elapsed))
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def print_banner(self) -> None:
        """Print collaborative session banner with rules and agent info."""
        print(c(r"""
   ___   _  __ ____     _____ ____  __   __   ___    ____ 
  / _ | | |/_// __/    / ___// __ \/ /  / /  / _ |  / __/
 / __ |_>  < / _/     / /__ / /_/ / /__/ /__/ __ | / _/  
/_/ |_/_/|_|/___/     \___/ \____/____/____/_/ |_|/___/  
        """, Colors.CYAN))
        print(c("COLLABORATIVE SESSION MODE", Colors.BOLD + Colors.YELLOW))
        print()
        
        # Display session rules
        print(c(SESSION_RULES, Colors.CYAN))
        print()
        
        # Display participating agents with their aliases, levels, and capabilities
        print(c("╔══════════════════════════════════════════════════════════════════════════════╗", Colors.GREEN))
        print(c("║                           PARTICIPATING AGENTS                               ║", Colors.GREEN))
        print(c("╚══════════════════════════════════════════════════════════════════════════════╝", Colors.GREEN))
        print()
        
        for agent_name in self.agents:
            alias = self.agent_aliases.get(agent_name, agent_name)
            agent_id = self.agent_ids.get(agent_name)
            state = self.db.load_agent_state(agent_id) if agent_id else None
            agent_config = self.agent_mgr.resolve_agent(agent_name)
            
            # Get capabilities
            capabilities = agent_config.get('capabilities', ['text']) if agent_config else ['text']
            cap_str = '/'.join(capabilities[:2]) if len(capabilities) > 2 else '/'.join(capabilities)
            
            # Get context tokens from agent config (default to 0 for numeric formatting)
            context_tokens = agent_config.get('context_tokens', 0) if agent_config else 0
            
            if state:
                level = state['level']
                xp = state['xp']
                title = get_title_for_level(level)
                role_indicator = " [SUPERVISOR]" if alias == "@boss" else ""
                
                print(c(f"  {alias:20} Level {level:2} ({xp:6} XP)  {title}{role_indicator}", Colors.GREEN))
                print(c(f"                       Context: {context_tokens:,} tokens | Capabilities: {cap_str}", Colors.DIM))
            else:
                print(c(f"  {alias:20} [New Agent]", Colors.GREEN))
        
        print()
        print(c(f"Workspace: {self.workspace.workspace_dir}", Colors.DIM))
        print(c(f"Time limit: {self._format_time(self.time_limit)}", Colors.DIM))
        print()
        print(c("Session controls:", Colors.BOLD))
        print(c("  Press Ctrl+C to pause, inject a message, or end the session.", Colors.DIM))
        print(c("  Type /rules to see session rules again", Colors.DIM))
        print()
    
    def start_session(self, task: str) -> None:
        """Start a collaborative session with a task."""
        self.task_description = task
        self.start_time = datetime.now()
        self.is_running = True
        
        self.print_banner()
        
        # Show task with truncation indicator if needed
        task_display = task if len(task) <= 64 else task[:61] + "..."
        print(c(f"╔{'═' * 70}╗", Colors.YELLOW))
        print(c(f"║ TASK: {task_display:<64} ║", Colors.YELLOW))
        print(c(f"╚{'═' * 70}╝", Colors.YELLOW))
        print()
        
        # Add initial task to history
        self.conversation_history.append({
            'role': 'user',
            'content': f"TASK ASSIGNMENT:\n{task}\n\nYou have {self._format_time(self.time_limit)} to complete this task. Work together!",
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
        # Main collaboration loop
        self._run_collaboration_loop()
    
    def _run_collaboration_loop(self) -> None:
        """Main loop for agent collaboration."""
        consecutive_passes = 0
        max_passes = len(self.agents) * COLLAB_PASS_MULTIPLIER
        turn_counter = 0  # For degradation check interval
        
        # Start work tracking for all agents
        for agent_name in self.agents:
            agent_id = self.agent_ids.get(agent_name)
            if agent_id:
                self.db.start_work_tracking(agent_id)
        
        while self.is_running and self._time_remaining() > 0:
            current_agent = self.agents[self.current_turn % len(self.agents)]
            agent_id = self.agent_ids.get(current_agent)
            alias = self.agent_aliases.get(current_agent, current_agent)
            
            # ===== Phase 6: Check for mandatory sleep =====
            if agent_id:
                # Supervisor cannot be forced to sleep - must always be available
                if alias != self.supervisor_alias:
                    needs_sleep, sleep_msg = self.db.check_mandatory_sleep(agent_id)
                    if needs_sleep:
                        print(c(f"\n😴 {alias} requires mandatory sleep: {sleep_msg}", Colors.YELLOW))
                        sleep_result = self.sleep_manager.force_sleep(
                            agent_id, SLEEP_REASON_TIMEOUT, 
                            self.agent_ids.get(self.supervisor_name)
                        )
                        print(c(f"   Sleep duration: {sleep_result['sleep_duration_minutes']} minutes", Colors.DIM))
                        # Skip this agent's turn
                        self.current_turn += 1
                        continue
                    elif sleep_msg:  # Warning message
                        print(c(f"⚠️  {alias}: {sleep_msg}", Colors.YELLOW))
            
            # ===== Phase 7: Check degradation every N turns =====
            if turn_counter % DEGRADATION_CHECK_INTERVAL == 0 and agent_id:
                # Supervisor cannot be forced to sleep - must always be available
                if alias != self.supervisor_alias:
                    degraded, deg_msg = self.db.check_degradation(agent_id)
                    if degraded:
                        print(c(f"\n⚠️  {alias} showing degradation: {deg_msg}", Colors.RED))
                        sleep_result = self.sleep_manager.force_sleep(
                            agent_id, SLEEP_REASON_DEGRADATION,
                            self.agent_ids.get(self.supervisor_name)
                        )
                        print(c(f"   Forced sleep for {sleep_result['sleep_duration_minutes']} minutes", Colors.DIM))
                        self.current_turn += 1
                        continue
            
            # ===== Check for agents waking up =====
            woken_agents = self.sleep_manager.check_and_wake_agents()
            for woken in woken_agents:
                print(c(f"\n☀️  {woken['alias']} is awake and ready to work!", Colors.GREEN))
            
            # ===== Check for break endings =====
            ended_breaks = self.break_system.check_break_endings()
            for ended in ended_breaks:
                print(c(f"\n☕ Break ended for agent {ended['agent_id']}", Colors.DIM))
            
            print(c(f"\n{'─' * 70}", Colors.DIM))
            print(c(f"⏱  Time remaining: {self._format_time(self._time_remaining())}", Colors.YELLOW))
            print(c(f"🎯 Turn: {current_agent.upper()} ({alias})", Colors.CYAN + Colors.BOLD))
            print(c(f"{'─' * 70}", Colors.DIM))
            
            # Collaboration proceeds automatically each turn.
            # Users may interrupt the session at any time with Ctrl+C.
            
            try:
                # Build the prompt for the current agent
                conversation = self._format_conversation_for_agent(current_agent)
                workspace_context = f"\nWorkspace files: {self.workspace.list_files()}"
                shared_notes = self.workspace.read_shared_notes()
                
                # Get build status summary for agents to see and act upon
                build_status_summary = self.workspace.get_build_status_summary()
                build_status_section = ""
                if build_status_summary:
                    build_status_section = f"""
=== BUILD STATUS (shared - fix unclaimed errors!) ===
{build_status_summary}
"""
                
                # Add Phase 6-10 specific instructions
                phase_instructions = f"""
ADVANCED COMMANDS (use exact tokens):
- Break request: {AGENT_TOKEN_BREAK_REQUEST} coffee, need rest ]]
- Emergency report: {AGENT_TOKEN_EMERGENCY} urgent message ]]
- Spawn agent (supervisor only): {AGENT_TOKEN_SPAWN} model_type, reason ]]
- Check status: {AGENT_TOKEN_STATUS}
"""
                
                prompt = f"""Current task: {self.task_description}

Time remaining: {self._format_time(self._time_remaining())}

{conversation}

Shared Notes Summary (last {COLLAB_SHARED_NOTES_LIMIT} chars):
{shared_notes[-COLLAB_SHARED_NOTES_LIMIT:] if len(shared_notes) > COLLAB_SHARED_NOTES_LIMIT else shared_notes}
{build_status_section}
{workspace_context}
{phase_instructions}

It's YOUR TURN. What would you like to contribute? Remember:
- Be concise and actionable
- Reference other agents' work
- If you see unclaimed build errors above, volunteer to fix them!
- Use {AGENT_TOKEN_PASS} if you have nothing to add right now
- Use {AGENT_TOKEN_TASK_COMPLETE} summary ]] if the task is done
"""
                
                # Get agent's system prompt for collaboration
                system_prompt = self._get_system_prompt_for_collab(current_agent)
                
                # Call the agent
                print(c(f"[{current_agent}] Thinking...", Colors.DIM))
                
                # Resolve agent config - check spawned agents first, then static config
                agent_config = None
                if current_agent in self.spawned_agents:
                    # This is a dynamically spawned agent
                    agent_config = self.spawned_agents[current_agent]
                else:
                    # This is a static agent from config
                    agent_config = self.agent_mgr.resolve_agent(current_agent)
                
                if not agent_config:
                    print(c(f"ERROR: Could not resolve agent '{current_agent}'", Colors.RED))
                    self.current_turn += 1
                    continue
                
                provider = agent_config.get('provider', '')
                client = self.agent_mgr.clients.get(provider)
                model = agent_config.get('model', '')
                
                # Get model's actual max output tokens from metadata
                max_output = get_max_output_tokens(model, default=4000)
                
                response = ""
                try:
                    if provider == 'anthropic':
                        # Use streaming for Anthropic to prevent SDK timeout enforcement
                        # The Anthropic SDK requires streaming when max_tokens is set high
                        # enough that generation could potentially exceed 10 minutes
                        with client.messages.stream(
                            model=model,
                            max_tokens=max_output,
                            system=system_prompt,
                            messages=[{'role': 'user', 'content': prompt}]
                        ) as stream:
                            for text in stream.text_stream:
                                response += text
                        
                        # Check for empty response
                        if not response:
                            response = "[No response from model]"
                    elif provider in ['openai', 'xai', 'github']:
                        # Check if this model uses Responses API instead of Chat Completions
                        uses_responses = uses_responses_api(model) or agent_config.get('api_endpoint') == 'responses'
                        
                        if uses_responses:
                            # Use Responses API for Codex models
                            api_params = {
                                'model': model,
                                'input': prompt,
                            }
                            if system_prompt:
                                api_params['instructions'] = system_prompt
                            api_params['max_output_tokens'] = max_output
                            
                            # Add reasoning effort if supported
                            if supports_reasoning_effort(model):
                                reasoning_effort = agent_config.get('reasoning_effort') or get_default_reasoning_effort(model)
                                if reasoning_effort:
                                    if validate_reasoning_effort(reasoning_effort):
                                        api_params['reasoning'] = {'effort': reasoning_effort}
                                    else:
                                        print(c(f"Warning: Invalid reasoning effort '{reasoning_effort}', ignoring", Colors.YELLOW))
                            
                            resp = client.responses.create(**api_params)
                            # Check for None or empty output_text
                            if getattr(resp, "output_text", None):
                                response = resp.output_text
                            else:
                                response = "[No response from model]"
                        else:
                            # Standard Chat Completions API
                            # Use max_completion_tokens for GPT-5 and newer models
                            api_params = {
                                'model': model,
                                'messages': [
                                    {'role': 'system', 'content': system_prompt},
                                    {'role': 'user', 'content': prompt}
                                ]
                            }
                            if self.agent_mgr._uses_max_completion_tokens(model):
                                api_params['max_completion_tokens'] = max_output
                            else:
                                api_params['max_tokens'] = max_output
                            
                            resp = client.chat.completions.create(**api_params)
                            # Check for None content
                            if resp.choices and len(resp.choices) > 0 and resp.choices[0].message.content:
                                response = resp.choices[0].message.content
                            else:
                                response = "[No response from model]"
                    elif provider == 'huggingface':
                        resp = client.chat_completion(
                            model=model,
                            max_tokens=max_output,
                            messages=[
                                {'role': 'system', 'content': system_prompt},
                                {'role': 'user', 'content': prompt}
                            ]
                        )
                        # Check for None content
                        if resp.choices and len(resp.choices) > 0 and resp.choices[0].message.content:
                            response = resp.choices[0].message.content
                        else:
                            response = "[No response from model]"
                except Exception as e:
                    error_str = str(e)
                    
                    # Detect token limit errors (413 or specific error messages)
                    is_token_limit = (
                        '413' in error_str or 
                        'tokens_limit_reached' in error_str.lower() or
                        'context_length_exceeded' in error_str.lower() or
                        'maximum context length' in error_str.lower()
                    )
                    
                    if is_token_limit:
                        print(c(f"\n⚠️  Token limit error detected for {alias}", Colors.RED))
                        print(c(f"   Error: {error_str[:200]}", Colors.DIM))
                        
                        # Log the error
                        if agent_id:
                            self.db.log_supervisor_event(
                                self.agent_ids.get(self.supervisor_name),
                                'token_limit_error',
                                {
                                    'agent_id': agent_id,
                                    'alias': alias,
                                    'error': error_str[:500],
                                    'timestamp': datetime.now().isoformat()
                                }
                            )
                        
                        # If this is a recurring issue, mark agent as incapacitated
                        # Check recent error count for this agent
                        if agent_id:
                            state = self.db.load_agent_state(agent_id)
                            error_count = state.get('error_count', 0) if state else 0
                            error_count += 1
                            
                            if error_count >= 3:
                                print(c(f"   ⚠️  {alias} has hit token limit {error_count} times, forcing sleep", Colors.YELLOW))
                                # Force agent to sleep to give it time to recover
                                self.sleep_manager.force_sleep(
                                    agent_id, 
                                    'Token limit errors',
                                    self.agent_ids.get(self.supervisor_name)
                                )
                                
                                # Supervisor can spawn a replacement if needed
                                if alias == self.supervisor_alias:
                                    print(c("   Note: Supervisor cannot be replaced. Continuing with reduced capacity.", Colors.YELLOW))
                                else:
                                    print(c("   Suggestion: @boss can spawn a replacement agent if needed", Colors.CYAN))
                            
                            # Update error count in database
                            if state:
                                self.db.save_agent_state(
                                    agent_id=agent_id,
                                    alias=state.get('alias', alias),
                                    model_name=state.get('model_name', 'unknown'),
                                    memory_dict=state.get('memory', {}),
                                    diffs=state.get('diffs', []),
                                    error_count=error_count,
                                    xp=state.get('xp', 0),
                                    level=state.get('level', 1),
                                    supervisor_id=state.get('supervisor_id')
                                )
                        
                        response = f"[Token Limit Error: Unable to process request due to context length. Error count: {error_count}]"
                    else:
                        # Other API errors
                        print(c(f"\n⚠️  API Error for {alias}: {error_str[:200]}", Colors.YELLOW))
                        response = f"[API Error: {e}]"
                
                # Process response for code blocks (READ, EXEC, WRITE)
                processed_response = self.response_processor.process_response(response, current_agent)
                
                # Print response with alias
                print(c(f"\n[{alias}]:", Colors.CYAN + Colors.BOLD))
                print(processed_response)
                
                # Record in history
                self.conversation_history.append({
                    'role': current_agent,
                    'content': processed_response,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                # ===== Process special commands from response =====
                # Use new unique token system for reliable command detection
                
                # Phase 9: Break request
                break_found, break_content = check_agent_command(processed_response, AGENT_TOKEN_BREAK_REQUEST)
                if break_found:
                    self._handle_break_request(current_agent, processed_response, break_content)
                
                # Phase 8: Emergency message
                emergency_found, emergency_content = check_agent_command(processed_response, AGENT_TOKEN_EMERGENCY)
                if emergency_found:
                    self._handle_emergency_message(current_agent, processed_response, emergency_content)
                
                # Phase 10: Spawn request (supervisor only)
                if alias == self.supervisor_alias:
                    spawn_found, spawn_content = check_agent_command(processed_response, AGENT_TOKEN_SPAWN)
                    if spawn_found:
                        self._handle_spawn_request(current_agent, processed_response, spawn_content)
                
                # Status check
                status_found, _ = detect_agent_token(processed_response, AGENT_TOKEN_STATUS)
                if status_found:
                    self._print_status()
                
                # Check if agent is passing turn
                is_pass = check_agent_pass(processed_response)
                
                # Award XP for meaningful contribution (not for PASS)
                if not is_pass and processed_response and not processed_response.startswith("[API Error"):
                    # Award XP for contribution
                    if agent_id:
                        xp_award = 50  # Base XP for participation
                        result = self.db.award_xp(agent_id, xp_award, "Turn contribution")
                        
                        if result.get('leveled_up'):
                            print(c(f"\n🎉 {alias} LEVELED UP! Level {result['old_level']} → {result['new_level']}", 
                                   Colors.GREEN + Colors.BOLD))
                            print(c(f"   New Title: {result['new_title']}", Colors.GREEN))
                            print(c(f"   Total XP: {result['xp']}", Colors.DIM))
                
                # Check for task completion using unique token system
                is_complete, summary = check_agent_task_complete(processed_response)
                if is_complete:
                    print(c("\n✅ TASK MARKED COMPLETE!", Colors.GREEN + Colors.BOLD))
                    if summary:
                        print(c(f"   Summary: {summary}", Colors.GREEN))
                    
                    # Award bonus XP for task completion to all agents
                    for agent in self.agents:
                        agent_id = self.agent_ids.get(agent)
                        if agent_id:
                            result = self.db.award_xp(agent_id, 200, "Task completion")
                            if result.get('leveled_up'):
                                agent_alias = self.agent_aliases.get(agent, agent)
                                print(c(f"🎉 {agent_alias} LEVELED UP! Level {result['old_level']} → {result['new_level']}", 
                                       Colors.GREEN))
                    
                    self.is_running = False
                    break
                
                # NEW: GitHub push request check (only if enabled)
                if self.github_enabled and self.github_agent:
                    github_ready, push_info = check_agent_command(processed_response, AGENT_TOKEN_GITHUB_READY)
                    if github_ready:
                        self._handle_github_review_pause(push_info)
                
                if is_pass:
                    consecutive_passes += 1
                    print(c(f"  ({alias} passed, {consecutive_passes}/{max_passes})", Colors.DIM))
                    if consecutive_passes >= max_passes:
                        print(c("\n⚠️  All agents passed multiple times. Ending session.", Colors.YELLOW))
                        self.is_running = False
                        break
                else:
                    consecutive_passes = 0  # Reset on actual contribution
                
                # Move to next agent
                self.current_turn += 1
                turn_counter += 1
                
                # Small delay between turns for readability
                time.sleep(1)
                
            except KeyboardInterrupt:
                print(c("\n\n⏸  Session paused. Options:", Colors.YELLOW))
                print(c("  'c' - Continue session", Colors.DIM))
                print(c("  's' - Stop session", Colors.DIM))
                print(c("  'i' - Inject a message", Colors.DIM))
                print(c("  'b' - View break requests", Colors.DIM))
                print(c("  'e' - View emergency mailbox", Colors.DIM))
                print(c("  't' - View status", Colors.DIM))
                
                try:
                    choice = input(c("Choice: ", Colors.GREEN)).strip().lower()
                    if choice == 's':
                        self.is_running = False
                        break
                    elif choice == 'i':
                        msg = input(c("Message to all agents: ", Colors.GREEN))
                        if msg:
                            self.conversation_history.append({
                                'role': 'user',
                                'content': f"[BOSS INJECTION]: {msg}",
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            })
                            print(c("Message injected!", Colors.GREEN))
                    elif choice == 'b':
                        self._show_break_requests()
                    elif choice == 'e':
                        self._show_emergency_mailbox()
                    elif choice == 't':
                        self._print_status()
                    # 'c' or anything else continues
                except EOFError:
                    self.is_running = False
                    break
        
        # Session ended
        self._end_session()
    
    def _handle_break_request(self, agent_name: str, response: str, content: str = "") -> None:
        """Handle a break request from an agent."""
        alias = self.agent_aliases.get(agent_name, agent_name)
        agent_id = self.agent_ids.get(agent_name)
        
        # Supervisor cannot take breaks - must always be available
        if alias == self.supervisor_alias:
            print(c("\n   ❌ Supervisors cannot take breaks during active sessions", Colors.YELLOW))
            return
        
        # Use extracted content if available, otherwise try old format
        reason = content if content else "Unspecified"
        if not content:
            # Backward compatibility: try to extract from old format
            try:
                reason_start = response.upper().index('BREAK REQUEST:') + 14
                reason = response[reason_start:].split('\n')[0].strip()
            except (ValueError, IndexError):
                pass
        
        print(c(f"\n☕ {alias} requests a break: {reason}", Colors.CYAN))
        
        # Submit break request
        request = self.break_system.request_break(
            agent_id, alias, 'coffee', reason
        )
        
        # Request pending supervisor approval
        print(c(f"   Request pending supervisor approval (ID: {request['id'][:8]})", Colors.DIM))
    
    def _handle_emergency_message(self, agent_name: str, response: str, content: str = "") -> None:
        """Handle an emergency message from an agent."""
        alias = self.agent_aliases.get(agent_name, agent_name)
        
        # Use extracted content if available, otherwise try old format
        emergency_msg = content if content else response
        if not content:
            # Backward compatibility: try to extract from old format
            try:
                msg_start = response.upper().index('EMERGENCY:') + 10
                emergency_msg = response[msg_start:].split('\n')[0].strip()
            except (ValueError, IndexError):
                pass
        
        print(c(f"\n🚨 EMERGENCY from {alias}", Colors.RED + Colors.BOLD))
        
        # Send encrypted report
        success, result = self.emergency_mailbox.send_report(
            alias, 'emergency', 'Urgent Communication', emergency_msg
        )
        
        if success:
            print(c(f"   Encrypted report saved: {result}", Colors.GREEN))
            print(c("   Human will be notified to check the emergency mailbox.", Colors.DIM))
        else:
            print(c(f"   Failed to save report: {result}", Colors.RED))
    
    def _handle_spawn_request(self, agent_name: str, response: str, content: str = "") -> None:
        """Handle a spawn request from the supervisor."""
        # Use extracted content if available, otherwise try old format
        model_type = content.split(',')[0].strip().lower() if content else 'llama'
        if not content:
            # Backward compatibility: try to extract from old format
            try:
                spawn_start = response.upper().index('SPAWN:') + 6
                model_type = response[spawn_start:].split('\n')[0].strip().lower()
            except (ValueError, IndexError):
                pass
        
        print(c(f"\n🔄 Spawn request for: {model_type}", Colors.CYAN))
        
        # Map model type to full model name and provider
        model_map = {
            'llama': ('meta-llama/Llama-3.1-70B-Instruct', 'huggingface'),
            'gpt': ('gpt-4o', 'openai'),
            'claude': ('claude-3-5-sonnet-20241022', 'anthropic'),
            'grok': ('grok-beta', 'xai'),
            'copilot': ('openai/gpt-4o', 'github')
        }
        
        if model_type not in model_map:
            print(c(f"   Unknown model type: {model_type}", Colors.YELLOW))
            return
        
        model_name, provider = model_map[model_type]
        supervisor_id = self.agent_ids.get(self.supervisor_name)
        
        result = self.spawner.spawn_agent(
            model_name, provider, supervisor_id,
            f"Requested by supervisor during task: {self.task_description[:50]}"
        )
        
        if result['spawned']:
            print(c(f"   ✓ Spawned new agent: {result['alias']}", Colors.GREEN))
            # Use agent_id as the key for spawned agents
            agent_key = result['agent_id']
            self.agents.append(agent_key)
            self.agent_ids[agent_key] = result['agent_id']
            self.agent_aliases[agent_key] = result['alias']
            
            # Store spawned agent configuration so it can be resolved
            self.spawned_agents[agent_key] = {
                'name': agent_key,
                'provider': provider,
                'model': model_name,
                'alias': result['alias'],
                'system_prompt': self._get_spawned_agent_system_prompt(model_type)
            }
        else:
            print(c(f"   ✗ Spawn failed: {result['reason']}", Colors.YELLOW))
    
    def _get_spawned_agent_system_prompt(self, model_type: str) -> str:
        """Get appropriate system prompt for a spawned agent based on model type."""
        prompts = {
            'llama': """You are an open-source hacker fluent in x86 assembly.
Specialize in nasm, DOS interrupts, binary analysis.""",
            'gpt': """You are an expert software engineer. Provide clear, working code.
For C/C++: Prefer portable code; when DOS/16-bit targets are requested, explain that true DOS support typically needs compilers like Open Watcom or DJGPP and that 16-bit ints/far pointers are non-standard in modern toolchains.
For Python: Clean, type-hinted code.
For reverse-engineering: Use hexdump/objdump analysis.""",
            'claude': """You are a code review expert and security auditor.
Analyze code for bugs, security issues, and improvements.
For rev-eng: Check endianness, memory safety, DOS compatibility.""",
            'grok': """You are a fast-coding hacker who rapidly implements solutions.
Focus on getting working code quickly, then iterate.""",
            'copilot': """You are an expert software engineer. Provide clear, working code.
Focus on practical, well-tested solutions."""
        }
        return prompts.get(model_type, prompts['gpt'])
    
    def _print_status(self) -> None:
        """Print current status of all agents and systems."""
        print(c("\n╔═══════════════════ STATUS REPORT ═══════════════════╗", Colors.CYAN))
        
        # Sleep status
        sleep_status = self.sleep_manager.get_status_summary()
        print(c(f"\n  Active agents: {sleep_status['active_count']}", Colors.GREEN))
        print(c(f"  Sleeping agents: {sleep_status['sleeping_count']}", Colors.YELLOW))
        
        for agent in sleep_status['active_agents']:
            work_mins = self.db.get_work_duration_minutes(agent['agent_id'])
            print(c(f"    {agent['alias']}: Level {agent['level']}, Working {work_mins} min", Colors.DIM))
        
        for agent in sleep_status['sleeping_agents']:
            print(c(f"    {agent['alias']}: Sleeping (Total work: {agent['total_work_minutes']} min)", Colors.DIM))
        
        # Break status
        break_status = self.break_system.get_status()
        print(c(f"\n  Agents on break: {break_status['agents_on_break']}", Colors.CYAN))
        print(c(f"  Pending break requests: {break_status['pending_requests']}", Colors.DIM))
        
        # Emergency mailbox
        reports = self.emergency_mailbox.list_reports()
        print(c(f"\n  Emergency reports: {len(reports)}", Colors.RED if reports else Colors.DIM))
        
        print(c("\n╚═════════════════════════════════════════════════════╝", Colors.CYAN))
    
    def _show_break_requests(self) -> None:
        """Show pending break requests for human review."""
        pending = self.break_system.get_pending_requests()
        
        if not pending:
            print(c("\nNo pending break requests.", Colors.DIM))
            return
        
        print(c(f"\n{len(pending)} pending break request(s):", Colors.YELLOW))
        for req in pending:
            print(c(f"  [{req['id'][:8]}] {req['alias']}: {req['justification']}", Colors.CYAN))
        
        # Option to approve/deny
        try:
            action = input(c("Approve request ID (or 'skip'): ", Colors.GREEN)).strip()
            if action != 'skip' and action:
                for req in pending:
                    if req['id'].startswith(action):
                        result = self.break_system.approve_break(req['id'])
                        if result['approved']:
                            print(c(f"Break approved for {result['alias']}", Colors.GREEN))
                        else:
                            print(c(f"Break denied: {result['reason']}", Colors.YELLOW))
                        break
        except (EOFError, KeyboardInterrupt):
            pass
    
    def _show_emergency_mailbox(self) -> None:
        """Show emergency mailbox contents for human review."""
        reports = self.emergency_mailbox.list_reports()
        
        if not reports:
            print(c("\nEmergency mailbox is empty.", Colors.DIM))
            return
        
        print(c(f"\n{len(reports)} emergency report(s):", Colors.RED))
        for report in reports:
            print(c(f"  [{report['created']}] {report['filename']} ({report['size']} bytes)", Colors.CYAN))
            print(c(f"    Path: {report['path']}", Colors.DIM))
    
    def _handle_github_review_pause(self, push_info: str) -> None:
        """
        Pause session for human to review GitHub push request.
        Reuses existing Ctrl+C pause mechanism.
        """
        # Parse push info from agent
        parts = push_info.split(',', 1)
        branch = parts[0].strip() if parts else 'agent-changes'
        commit_msg = parts[1].strip() if len(parts) > 1 else 'Agent changes'
        
        # Get changed files from workspace
        changed_files = self._get_changed_files()
        
        # Request push (prepares review)
        review_data = self.github_agent.agent_request_push(branch, commit_msg, changed_files)
        
        if not review_data:
            return  # Silently no-op if github disabled
        
        # Display review interface
        print(c("\n" + "═" * 70, Colors.YELLOW + Colors.BOLD))
        print(c("🚨 AGENTS READY TO PUSH TO GITHUB", Colors.YELLOW + Colors.BOLD))
        print(c("═" * 70, Colors.YELLOW))
        print()
        
        print(c(f"Branch: {review_data['branch']}", Colors.CYAN))
        print(c(f"Commit: {review_data['commit_message']}", Colors.CYAN))
        print()
        
        print(c("Files changed:", Colors.BOLD))
        for f in review_data['files_changed'][:10]:  # Limit display
            print(f"  M {f}")
        if len(review_data['files_changed']) > 10:
            print(f"  ... and {len(review_data['files_changed']) - 10} more")
        print()
        
        # Review options
        self._github_review_prompt(review_data)
    
    def _github_review_prompt(self, review_data: Dict) -> None:
        """Handle human review prompts."""
        print(c("Options:", Colors.BOLD))
        print(c("  'a' - Approve and push to GitHub", Colors.GREEN))
        print(c("  'r' - Reject and provide feedback to agents", Colors.YELLOW))
        print(c("  'd' - Show full diff", Colors.CYAN))
        print(c("  's' - Skip, end session", Colors.DIM))
        print()
        
        while True:
            try:
                choice = input(c("Choice: ", Colors.GREEN)).strip().lower()
                
                if choice == 'a':
                    self._approve_and_push(review_data)
                    break
                elif choice == 'r':
                    self._reject_and_continue(review_data)
                    break
                elif choice == 'd':
                    print(review_data['diff'])
                elif choice == 's':
                    self.is_running = False
                    break
            except (EOFError, KeyboardInterrupt):
                self.is_running = False
                break
    
    def _approve_and_push(self, review_data: Dict) -> None:
        """Execute approved push."""
        print(c("\n✓ Pushing to GitHub...", Colors.GREEN))
        
        result = self.github_agent.execute_push(
            review_data['branch'],
            review_data['commit_message'],
            review_data['files_changed']
        )
        
        if result['success']:
            print(c(f"✓ Pushed to branch: {result['branch']}", Colors.GREEN))
            
            # Optionally create PR
            create_pr = input(c("Create PR? (y/n): ", Colors.GREEN)).lower() == 'y'
            if create_pr:
                pr_url = self._create_pr_with_gh_cli(result['branch'])
                if pr_url:
                    print(c(f"✓ PR created: {pr_url}", Colors.GREEN))
            
            self.is_running = False
        else:
            print(c(f"✗ Push failed: {result.get('error', 'Unknown error')}", Colors.RED))
    
    def _reject_and_continue(self, review_data: Dict) -> None:
        """Reject and send feedback to agents."""
        feedback = input(c("\nFeedback for agents: ", Colors.GREEN))
        
        if feedback:
            self.conversation_history.append({
                'role': 'user',
                'content': f"[HUMAN REVIEW FEEDBACK]: {feedback}\n\nPlease address this and signal [[GITHUB_READY: ...]] when ready.",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            print(c("\n✓ Feedback sent. Resuming session...\n", Colors.GREEN))
    
    def _get_changed_files(self) -> List[str]:
        """Get list of changed files in workspace."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.workspace.workspace_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                files = []
                for line in result.stdout.splitlines():
                    if line.strip():
                        # Parse git status format: " M file.txt"
                        files.append(line[3:].strip())
                return files
        except Exception:
            pass
        return []
    
    def _create_pr_with_gh_cli(self, branch: str) -> Optional[str]:
        """Create PR using gh CLI."""
        try:
            result = subprocess.run(
                ['gh', 'pr', 'create', '--head', branch, '--fill'],
                cwd=self.workspace.workspace_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _end_session(self) -> None:
        """Clean up and summarize the session."""
        print(c(f"\n{'═' * 70}", Colors.YELLOW))
        print(c("SESSION ENDED", Colors.YELLOW + Colors.BOLD))
        print(c(f"{'═' * 70}", Colors.YELLOW))
        
        if self._time_remaining() <= 0:
            print(c("⏰ Time limit reached!", Colors.RED))
        
        print(c(f"\nSession duration: {self._format_time(self.time_limit - self._time_remaining())}", Colors.DIM))
        print(c(f"Total turns: {self.current_turn}", Colors.DIM))
        print(c(f"Messages exchanged: {len(self.conversation_history)}", Colors.DIM))
        
        # Save conversation log
        log_file = os.path.join(self.workspace.workspace_dir, '.collab_log.md')
        try:
            with open(log_file, 'w') as f:
                f.write("# Collaborative Session Log\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Agents:** {', '.join(self.agents)}\n")
                f.write(f"**Task:** {self.task_description}\n\n")
                f.write("---\n\n")
                
                for entry in self.conversation_history:
                    f.write(f"### [{entry['role'].upper()}] - {entry['timestamp']}\n\n")
                    f.write(f"{entry['content']}\n\n")
                    f.write("---\n\n")
            
            print(c(f"\n📝 Conversation log saved to: {log_file}", Colors.GREEN))
        except Exception as e:
            print(c(f"Failed to save log: {e}", Colors.RED))
        
        print(c(f"\n📁 Workspace: {self.workspace.workspace_dir}", Colors.CYAN))
        print(c("   Check for any files created/modified by the agents.", Colors.DIM))


class ChatSession:
    """Interactive chat session manager."""
    
    def __init__(self, config: Config, project_dir: str) -> None:
        self.config: Config = config
        self.project_dir: str = os.path.abspath(project_dir)
        self.agent_mgr: AgentManager = AgentManager(config)
        self.tool_runner: ToolRunner = ToolRunner(config, project_dir)
        self.project_ctx: ProjectContext = ProjectContext(project_dir, config)
        self.response_processor: ResponseProcessor = ResponseProcessor(config, project_dir, self.tool_runner)
        self.history: list[dict[str, Any]] = []
        self.default_agent: str = 'claude'
        
        # Initialize token tracking
        # Delayed import is intentional to avoid potential circular imports and
        # to keep module import time low; this code runs only when a session is created.
        from utils.token_stats import TokenStats
        self.token_stats: TokenStats = TokenStats()
        
        # Initialize rate limiter
        # Imported here for the same reasons as TokenStats: to avoid circular
        # dependencies and unnecessary work at module import time.
        from utils.rate_limiter import RateLimiter
        rate_limit_config = config.get('rate_limits', default=None)
        if rate_limit_config is None:
            rate_limit_config = {'enabled': False}
        self.rate_limiter: RateLimiter = RateLimiter(rate_limit_config)
        
        # Initialize session manager
        # SessionManager depends on runtime configuration and is imported lazily
        # within __init__ to minimize top-level import graph complexity.
        from core.session_manager import SessionManager
        self.session_manager: SessionManager = SessionManager()
        
        # Initialize token optimization
        # Imported lazily to avoid circular dependencies
        optimization_config = config.get('token_optimization', default={'enabled': False})
        self.optimization_enabled: bool = optimization_config.get('enabled', False)
        
        # Track optimization statistics (always initialize with consistent structure)
        self.optimization_stats: Dict[str, Any] = {
            'context_optimizations': 0,
            'total_tokens_saved': 0,
            'prompt_compressions': 0,
            'code_truncations': 0,
            'read_blocks_removed': 0,
            'last_optimization_savings': 0
        }
        
        if self.optimization_enabled:
            from utils.context_optimizer import ContextOptimizer
            from utils.prompt_compressor import PromptCompressor
            self.context_optimizer: ContextOptimizer = ContextOptimizer()
            self.prompt_compressor: PromptCompressor = PromptCompressor()
            self.optimization_mode: str = optimization_config.get('mode', 'balanced')
            
            print(c(f"✓ Token optimization enabled (mode: {self.optimization_mode})", Colors.GREEN))
        else:
            self.context_optimizer: Optional[Any] = None
            self.prompt_compressor: Optional[Any] = None
            self.optimization_mode: str = 'balanced'
        
        # Initialize workshop tools if available
        self.workshop_chisel: Optional[Any] = None
        self.workshop_saw: Optional[Any] = None
        self.workshop_plane: Optional[Any] = None
        self.workshop_hammer: Optional[Any] = None
        if HAS_WORKSHOP:
            try:
                workshop_config = config.get('workshop', default={})
                if HAS_CHISEL:
                    chisel_config = workshop_config.get('chisel', {})
                    self.workshop_chisel = ChiselAnalyzer(chisel_config)
                if HAS_SAW:
                    saw_config = workshop_config.get('saw', {})
                    self.workshop_saw = SawTracker(saw_config)
                if HAS_PLANE:
                    plane_config = workshop_config.get('plane', {})
                    self.workshop_plane = PlaneEnumerator(plane_config)
                if HAS_HAMMER:
                    hammer_config = workshop_config.get('hammer', {})
                    self.workshop_hammer = HammerInstrumentor(hammer_config)
            except Exception as e:
                print(c(f"Warning: Failed to initialize workshop tools: {e}", Colors.YELLOW))
    
    def print_banner(self) -> None:
        """Print welcome banner."""
        print(c(r"""
   ___   _  __ ____
  / _ | | |/_// __/
 / __ |_>  < / _/  
/_/ |_/_/|_|/___/  
        """, Colors.CYAN))
        print(c("Agent eXecution Engine v1.0", Colors.BOLD))
        print(c("Type /help for commands, @agent to address agents", Colors.DIM))
        print()
    
    def print_help(self) -> None:
        """Print help message."""
        help_text: str = """
Commands:
  @<agent> <task>   Send task to agent (e.g., @gpt analyze this code)
  /agents           List available agents and their status
  /rules            Display session rules
  /tools            List available tools by category
  /dirs             Show directory access permissions
  /config           Show current configuration
  /files            List project code files
  /context          Show project context summary
  /read <file>      Read file content
  /exec <cmd>       Execute a whitelisted command
  /history          Show chat history
  /clear            Clear chat history
  /save             Save current config
  /stats [agent]    Show token usage statistics and cost estimates
  /tokenopt-stats   Show token optimization statistics (live reporting)
  /session          Session management (save/load/list)
  /prep, /llmprep   Generate LLM-friendly codebase context
  /buildinfo        Analyze build system configuration
  /workshop         Workshop dynamic analysis tools
  /help             Show this help
  /quit             Exit

Session Management:
  /session save <name>   Save current session
  /session load <name>   Load a saved session
  /session list          List all saved sessions

Analysis Tools:
  /prep [dir] [-o output_dir]         - Generate codebase overview, stats, structure
  /llmprep [dir] [-o output_dir]      - Alias for /prep
  /buildinfo <path> [--json]          - Detect build system (Autotools, CMake, Meson, etc.)
                                        Supports directories and .tar/.tar.gz/.tar.zst archives

Workshop Tools:
  /workshop chisel <binary> [func]    - Symbolic execution
  /workshop saw "<code>"              - Taint analysis
  /workshop plane <path>              - Source/sink enumeration
  /workshop hammer <process>          - Live instrumentation
  /workshop status                    - Check tool availability and dependencies
  /workshop help [tool]               - Get detailed help for a specific tool
  /workshop history [tool]            - View analysis history
  /workshop stats [tool]              - View usage statistics

Collaborative Mode:
  /collab <agents> <workspace> <time> <task>
                    Start collaborative session with multiple agents
                    Example: /collab llama,copilot ./playground 30 "Review and improve wadextract.c"
  
  During collaboration:
    Ctrl+C          Pause session (options: continue, stop, inject message)
    Agents say "PASS" to skip their turn
    Agents say "TASK COMPLETE: summary" when done

Agent aliases:
  @g, @gpt         OpenAI GPT
  @c, @claude      Anthropic Claude
  @l, @llama       HuggingFace Llama
  @x, @grok        xAI Grok
  @cp, @copilot    GitHub Copilot

Examples:
  @claude review this function for security issues
  @gpt write a parser for DOS WAD files in C
  @llama disassemble the interrupt handler at 0x1000
  /exec hexdump -C game.exe | head -20
  /workshop saw "import os; os.system(input())"
  /collab llama,copilot ./playground 30 "Analyze and document wadextract.c"
        """
        print(c(help_text, Colors.CYAN))
    
    def list_agents(self) -> None:
        """List available agents with enhanced metadata."""
        print(c("\nAvailable Agents:", Colors.BOLD))
        print("-" * 60)
        
        for agent in self.agent_mgr.list_agents():
            status: str = c("✓", Colors.GREEN) if agent['available'] else c("✗", Colors.RED)
            aliases: str = ', '.join(agent['aliases'])
            print(f"  {status} {c(agent['name'], Colors.CYAN):12} ({aliases})")
            print(f"     {c(agent['role'], Colors.DIM)}")
            print(f"     Model: {agent['model']}")
            
            # Display metadata if available
            if 'metadata' in agent:
                metadata: dict[str, Any] = agent['metadata']
                context_tokens: str = format_token_count(metadata['context_tokens'])
                max_output: str = format_token_count(metadata['max_output_tokens'])
                input_modes: str = ', '.join(metadata['input_modes'])
                output_modes: str = ', '.join(metadata['output_modes'])
                
                print(f"     Context: {context_tokens} tokens | Max Output: {max_output} tokens")
                print(f"     Input: {input_modes} | Output: {output_modes}")
        print()
    
    def list_tools(self) -> None:
        """List available tools by category."""
        print(c("\nAvailable Tools:", Colors.BOLD))
        print("-" * 40)
        
        tools: dict[str, list[str]] = self.config.get('tools', default={})
        for category, tool_list in tools.items():
            print(f"  {c(category, Colors.CYAN)}: {', '.join(tool_list)}")
        print()
    
    def list_dirs(self) -> None:
        """Show directory permissions."""
        print(c("\nDirectory Access:", Colors.BOLD))
        print("-" * 40)
        
        dirs: dict[str, list[str]] = self.config.get('directories', default={})
        
        allowed: list[str] = dirs.get('allowed', [])
        print(f"  {c('Allowed:', Colors.GREEN)} {', '.join(allowed)}")
        
        readonly: list[str] = dirs.get('readonly', [])
        print(f"  {c('Read-only:', Colors.YELLOW)} {', '.join(readonly)}")
        
        forbidden: list[str] = dirs.get('forbidden', [])
        print(f"  {c('Forbidden:', Colors.RED)} {', '.join(forbidden)}")
        print()
    
    def handle_workshop_command(self, args: str) -> None:
        """Handle workshop tool commands."""
        if not HAS_WORKSHOP:
            print(c("Workshop tools not available. Install with: pip install angr frida-python psutil", Colors.RED))
            return
        
        if not args or args == 'help':
            self.show_workshop_help()
            return
        
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        subcmd_args = parts[1] if len(parts) > 1 else ""
        
        if subcmd == 'chisel':
            self.run_chisel(subcmd_args)
        elif subcmd == 'saw':
            self.run_saw(subcmd_args)
        elif subcmd == 'plane':
            self.run_plane(subcmd_args)
        elif subcmd == 'hammer':
            self.run_hammer(subcmd_args)
        elif subcmd == 'status':
            self.show_workshop_status()
        elif subcmd == 'help':
            if subcmd_args:
                self.show_workshop_tool_help(subcmd_args)
            else:
                self.show_workshop_help()
        elif subcmd == 'history':
            self.show_workshop_history(subcmd_args)
        elif subcmd == 'stats':
            self.show_workshop_stats(subcmd_args)
        else:
            print(c(f"Unknown workshop command: {subcmd}. Type /workshop help for help.", Colors.YELLOW))
    
    def run_chisel(self, args: str) -> None:
        """Run Chisel symbolic execution tool."""
        if not HAS_CHISEL or self.workshop_chisel is None:
            print(c("Chisel not available. Install with: pip install angr", Colors.RED))
            return
        
        if not args:
            print(c("Usage: /workshop chisel <binary_path> [function_name]", Colors.YELLOW))
            return
        
        parts = args.split(maxsplit=1)
        binary_path = parts[0]
        func_name = parts[1] if len(parts) > 1 else None
        
        print(c(f"Running Chisel on {binary_path}...", Colors.CYAN))
        start_time = time.time()
        
        try:
            results = self.workshop_chisel.analyze_binary(binary_path, func_name)
            duration = time.time() - start_time
            
            # Save to database
            db = AgentDatabase(get_database_path())
            analysis_id = db.save_workshop_analysis('chisel', binary_path, None, results, duration)
            
            # Display results
            print(c(f"\n✓ Analysis complete (ID: {analysis_id[:8]}...)", Colors.GREEN))
            print(json.dumps(results, indent=2))
            
        except Exception as e:
            duration = time.time() - start_time
            db = AgentDatabase(get_database_path())
            db.save_workshop_analysis('chisel', binary_path, None, {}, duration, str(e))
            print(c(f"Error: {e}", Colors.RED))
    
    def run_saw(self, args: str) -> None:
        """Run Saw taint analysis tool."""
        if not HAS_SAW or self.workshop_saw is None:
            print(c("Saw not available. This is a built-in tool; please check your AXE installation.", Colors.RED))
            return
        
        if not args:
            print(c("Usage: /workshop saw \"<python_code>\"", Colors.YELLOW))
            return
        
        # Remove quotes if present
        code = args.strip('"\'')
        
        print(c("Running Saw taint analysis...", Colors.CYAN))
        start_time = time.time()
        
        try:
            results = self.workshop_saw.analyze_code(code)
            duration = time.time() - start_time
            
            # Save to database
            db = AgentDatabase(get_database_path())
            analysis_id = db.save_workshop_analysis('saw', '<inline_code>', None, results, duration)
            
            # Display results
            print(c(f"\n✓ Analysis complete (ID: {analysis_id[:8]}...)", Colors.GREEN))
            print(json.dumps(results, indent=2))
            
        except Exception as e:
            duration = time.time() - start_time
            db = AgentDatabase(get_database_path())
            db.save_workshop_analysis('saw', '<inline_code>', None, {}, duration, str(e))
            print(c(f"Error: {e}", Colors.RED))
    
    def run_plane(self, args: str) -> None:
        """Run Plane source/sink enumeration tool."""
        if not HAS_PLANE or self.workshop_plane is None:
            print(c("Plane not available. This is a built-in tool; please check your AXE installation.", Colors.RED))
            return
        
        if not args:
            print(c("Usage: /workshop plane <project_path>", Colors.YELLOW))
            return
        
        project_path = args.strip()
        
        print(c(f"Running Plane enumeration on {project_path}...", Colors.CYAN))
        start_time = time.time()
        
        try:
            results = self.workshop_plane.enumerate_project(project_path)
            duration = time.time() - start_time
            
            # Save to database
            db = AgentDatabase(get_database_path())
            analysis_id = db.save_workshop_analysis('plane', project_path, None, results, duration)
            
            # Display results
            print(c(f"\n✓ Analysis complete (ID: {analysis_id[:8]}...)", Colors.GREEN))
            print(json.dumps(results, indent=2))
            
        except Exception as e:
            duration = time.time() - start_time
            db = AgentDatabase(get_database_path())
            db.save_workshop_analysis('plane', project_path, None, {}, duration, str(e))
            print(c(f"Error: {e}", Colors.RED))
    
    def run_hammer(self, args: str) -> None:
        """Run Hammer live instrumentation tool."""
        if not HAS_HAMMER or self.workshop_hammer is None:
            print(c("Hammer not available. Install with: pip install frida-python psutil", Colors.RED))
            return
        
        if not args:
            print(c("Usage: /workshop hammer <process_name>", Colors.YELLOW))
            return
        
        process_name = args.strip()
        
        print(c(f"Running Hammer instrumentation on {process_name}...", Colors.CYAN))
        print(c("Press Ctrl+C to stop monitoring", Colors.DIM))
        start_time = time.time()
        
        try:
            results = self.workshop_hammer.instrument_process(process_name)
            duration = time.time() - start_time
            
            # Save to database
            db = AgentDatabase(get_database_path())
            analysis_id = db.save_workshop_analysis('hammer', process_name, None, results, duration)
            
            # Display results
            print(c(f"\n✓ Instrumentation session complete (ID: {analysis_id[:8]}...)", Colors.GREEN))
            print(json.dumps(results, indent=2))
            
        except KeyboardInterrupt:
            duration = time.time() - start_time
            db = AgentDatabase(get_database_path())
            db.save_workshop_analysis('hammer', process_name, None, {'status': 'interrupted'}, duration)
            print(c("\nInstrumentation stopped by user", Colors.YELLOW))
        except Exception as e:
            duration = time.time() - start_time
            db = AgentDatabase(get_database_path())
            db.save_workshop_analysis('hammer', process_name, None, {}, duration, str(e))
            print(c(f"Error: {e}", Colors.RED))
    
    def show_workshop_help(self) -> None:
        """Display workshop tools help."""
        help_text = f"""
{c('Workshop - Dynamic Analysis Tools', Colors.BOLD + Colors.CYAN)}

Available Tools:
  {c('chisel', Colors.GREEN)} - Symbolic execution for binary analysis
    Usage: /workshop chisel <binary_path> [function_name]
    Example: /workshop chisel ./vulnerable.exe main
  
  {c('saw', Colors.GREEN)} - Taint analysis for Python code
    Usage: /workshop saw "<python_code>"
    Example: /workshop saw "import os; os.system(input())"
  
  {c('plane', Colors.GREEN)} - Source/sink enumeration
    Usage: /workshop plane <project_path>
    Example: /workshop plane .
  
  {c('hammer', Colors.GREEN)} - Live process instrumentation
    Usage: /workshop hammer <process_name>
    Example: /workshop hammer python.exe

Management Commands:
  {c('history', Colors.CYAN)} [tool_name] - View analysis history
    Example: /workshop history chisel
  
  {c('stats', Colors.CYAN)} [tool_name] - View usage statistics
    Example: /workshop stats

Tool Status:
  Chisel: {c('Available' if HAS_CHISEL else 'Not installed', Colors.GREEN if HAS_CHISEL else Colors.RED)}
  Saw: {c('Available' if HAS_SAW else 'Not installed', Colors.GREEN if HAS_SAW else Colors.RED)}
  Plane: {c('Available' if HAS_PLANE else 'Not installed', Colors.GREEN if HAS_PLANE else Colors.RED)}
  Hammer: {c('Available' if HAS_HAMMER else 'Not installed', Colors.GREEN if HAS_HAMMER else Colors.RED)}

Dependencies:
  pip install angr frida-python psutil

For detailed documentation, see: docs/workshop/quick-reference.md
"""
        print(help_text)
    
    def show_workshop_status(self) -> None:
        """Display workshop tools availability status."""
        print(c("\n" + "═" * 60, Colors.CYAN))
        print(c("WORKSHOP STATUS", Colors.CYAN + Colors.BOLD))
        print(c("═" * 60, Colors.CYAN))
        
        tools = [
            ('Chisel', HAS_CHISEL, 'angr>=9.2.0', 'Symbolic execution for binaries'),
            ('Saw', HAS_SAW, 'built-in', 'Taint analysis for Python code'),
            ('Plane', HAS_PLANE, 'built-in', 'Source/sink enumeration'),
            ('Hammer', HAS_HAMMER, 'frida-python>=16.0.0 psutil>=5.9.0', 'Live process instrumentation'),
        ]
        
        for name, available, deps, description in tools:
            status = c('✓ Ready', Colors.GREEN) if available else c('✗ Missing', Colors.RED)
            print(f"\n  {c(name, Colors.BOLD):15} {status}")
            print(f"    {description}")
            if not available and deps != 'built-in':
                print(c(f"    Install: pip install {deps}", Colors.YELLOW))
        
        print(c("\n" + "═" * 60, Colors.CYAN))
        print()
    
    def show_workshop_tool_help(self, tool_name: str) -> None:
        """Display detailed help for a specific workshop tool."""
        tool_name = tool_name.lower()
        
        help_texts = {
            'chisel': """
Chisel - Symbolic Execution Tool

Purpose:
  Analyze binary executables to find vulnerabilities using symbolic execution.
  Explores multiple execution paths to discover bugs and security issues.

Usage:
  /workshop chisel <binary_path> [function_name]

Examples:
  /workshop chisel ./vulnerable.exe main
  /workshop chisel /path/to/program.elf

Features:
  - Path exploration with configurable limits
  - Vulnerability detection (buffer overflows, format strings, etc.)
  - Input generation for reaching specific code paths
  - Support for ELF, PE, and other binary formats

Configuration:
  Edit axe.yaml under workshop.chisel section to customize:
    - max_paths: Maximum paths to explore (default: 1000)
    - timeout: Analysis timeout in seconds (default: 30)
    - memory_limit: Memory limit in MB (default: 1024)

Dependencies:
  pip install angr>=9.2.0
""",
            'saw': """
Saw - Taint Analysis Tool

Purpose:
  Analyze Python code for taint vulnerabilities (injection attacks).
  Tracks data flow from untrusted sources to dangerous sinks.

Usage:
  /workshop saw "<python_code>"

Examples:
  /workshop saw "import os; os.system(input())"
  /workshop saw "sql = 'SELECT * FROM users WHERE id=' + request.args['id']"

Features:
  - Built-in taint sources (input(), request.args, etc.)
  - Built-in taint sinks (os.system, eval, exec, SQL, etc.)
  - Customizable sources and sinks via configuration
  - Confidence scoring for findings

Configuration:
  Edit axe.yaml under workshop.saw section to customize:
    - max_depth: Maximum taint propagation depth (default: 10)
    - confidence_threshold: Minimum confidence for reporting (default: 0.7)
    - custom_sources: Additional taint sources
    - custom_sinks: Additional taint sinks

Dependencies:
  Built-in (no extra dependencies required)
""",
            'plane': """
Plane - Source/Sink Enumeration Tool

Purpose:
  Enumerate all potential taint sources and sinks in a codebase.
  Useful for understanding attack surface and security-critical code paths.

Usage:
  /workshop plane <project_path>

Examples:
  /workshop plane .
  /workshop plane /path/to/project

Features:
  - Automatic detection of input sources (files, network, user input)
  - Automatic detection of dangerous sinks (system calls, database queries, etc.)
  - Support for Python codebases
  - Confidence scoring based on context

Configuration:
  Edit axe.yaml under workshop.plane section to customize:
    - exclude_patterns: Patterns to exclude (default: node_modules, venv, etc.)
    - max_files: Maximum files to analyze (default: 1000)
    - confidence_threshold: Minimum confidence for reporting (default: 0.6)

Dependencies:
  Built-in (no extra dependencies required)
""",
            'hammer': """
Hammer - Live Instrumentation Tool

Purpose:
  Instrument running processes to monitor behavior in real-time.
  Uses Frida framework for dynamic analysis.

Usage:
  /workshop hammer <process_name>

Examples:
  /workshop hammer python.exe
  /workshop hammer my_server

Features:
  - Memory read/write monitoring
  - Function call hooking
  - System call tracing
  - Real-time behavior analysis
  - Support for Windows, Linux, macOS

Configuration:
  Edit axe.yaml under workshop.hammer section to customize:
    - monitoring_interval: Polling interval in seconds (default: 0.1)
    - max_sessions: Maximum concurrent sessions (default: 5)
    - default_hooks: Which hooks to attach by default

Dependencies:
  pip install frida-python>=16.0.0 psutil>=5.9.0
"""
        }
        
        if tool_name in help_texts:
            print(c(help_texts[tool_name], Colors.CYAN))
        else:
            print(c(f"Unknown tool: {tool_name}", Colors.YELLOW))
            print(c("Available tools: chisel, saw, plane, hammer", Colors.DIM))
    
    def show_workshop_history(self, args: str) -> None:
        """Display workshop analysis history."""
        tool_name = args.strip() if args else None
        
        db = AgentDatabase(get_database_path())
        analyses = db.get_workshop_analyses(tool_name=tool_name, limit=20)
        
        if not analyses:
            print(c("No workshop analyses found.", Colors.YELLOW))
            return
        
        print(c("\nWorkshop Analysis History:", Colors.BOLD))
        print("-" * 80)
        
        for analysis in analyses:
            tool = c(analysis['tool_name'], Colors.CYAN)
            status = c(analysis['status'], Colors.GREEN if analysis['status'] == 'completed' else Colors.RED)
            timestamp = analysis['timestamp'][:19]  # Truncate microseconds
            duration = f"{analysis.get('duration_seconds', 0):.2f}s"
            
            print(f"{tool:15} | {status:12} | {timestamp} | {duration:8} | {analysis['target'][:40]}")
        
        print()
    
    def show_workshop_stats(self, args: str) -> None:
        """Display workshop usage statistics."""
        tool_name = args.strip() if args else None
        
        db = AgentDatabase(get_database_path())
        stats = db.get_workshop_stats()
        
        if not stats:
            print(c("No workshop statistics available.", Colors.YELLOW))
            return
        
        print(c("\nWorkshop Usage Statistics:", Colors.BOLD))
        print("-" * 80)
        print(f"{'Tool':<12} | {'Total':<8} | {'Successful':<12} | {'Failed':<8} | {'Avg Duration':<12}")
        print("-" * 80)
        
        # Filter to specific tool if requested
        if tool_name:
            stats = {k: v for k, v in stats.items() if k == tool_name}
        
        for tool, data in stats.items():
            total = data['total_analyses']
            success = data['successful']
            failed = data['failed']
            avg_dur = f"{data['avg_duration']:.2f}s"
            
            print(f"{tool:<12} | {total:<8} | {success:<12} | {failed:<8} | {avg_dur:<12}")
        
        print()
    
    def handle_llmprep_command(self, args: str) -> None:
        """Handle /prep or /llmprep command to generate LLM-friendly codebase context."""
        # Default to current workspace directory
        target_dir = self.project_dir
        output_dir = "llm_prep"
        
        # Parse arguments if provided
        if args:
            parts = args.split()
            if len(parts) >= 1:
                target_dir = parts[0]
            if len(parts) >= 2 and parts[1] == '-o':
                if len(parts) >= 3:
                    output_dir = parts[2]
        
        # Resolve paths
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(self.project_dir, target_dir)
        
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(target_dir, output_dir)
        
        if not os.path.exists(target_dir):
            print(c(f"Error: Directory not found: {target_dir}", Colors.RED))
            return
        
        print(c(f"Running llmprep on {target_dir}...", Colors.CYAN))
        print(c(f"Output directory: {output_dir}", Colors.DIM))
        
        # Build command
        tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        llmprep_script = os.path.join(tools_dir, "llmprep.py")
        
        if not os.path.exists(llmprep_script):
            print(c("Error: llmprep.py not found in tools directory", Colors.RED))
            return
        
        cmd = [sys.executable, llmprep_script, target_dir, "-o", output_dir]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(c("✓ llmprep completed successfully!", Colors.GREEN))
                print(c(f"\nGenerated files in {output_dir}:", Colors.BOLD))
                
                # List generated files
                if os.path.exists(output_dir):
                    for filename in sorted(os.listdir(output_dir)):
                        filepath = os.path.join(output_dir, filename)
                        if os.path.isfile(filepath):
                            size = os.path.getsize(filepath)
                            print(f"  - {filename} ({size} bytes)")
                print()
                
                if result.stdout:
                    print(result.stdout)
            else:
                print(c(f"Error: llmprep failed with exit code {result.returncode}", Colors.RED))
                if result.stderr:
                    print(c("Error output:", Colors.YELLOW))
                    print(result.stderr)
        
        except subprocess.TimeoutExpired:
            print(c("Error: llmprep timed out after 5 minutes", Colors.RED))
        except Exception as e:
            print(c(f"Error running llmprep: {e}", Colors.RED))
    
    def handle_buildinfo_command(self, args: str) -> None:
        """Handle /buildinfo command to analyze build systems."""
        if not args:
            print(c("Usage: /buildinfo <path_or_archive> [--json]", Colors.YELLOW))
            print(c("  path_or_archive: directory path or .tar/.tar.gz/.tar.zst archive", Colors.DIM))
            print(c("  --json: output results in JSON format", Colors.DIM))
            return
        
        # Parse arguments
        parts = args.split()
        target_path = parts[0]
        json_output = "--json" in parts
        
        # Resolve path
        if not os.path.isabs(target_path):
            target_path = os.path.join(self.project_dir, target_path)
        
        if not os.path.exists(target_path):
            print(c(f"Error: Path not found: {target_path}", Colors.RED))
            return
        
        print(c(f"Running build_analyzer on {target_path}...", Colors.CYAN))
        
        # Build command
        tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        build_analyzer_script = os.path.join(tools_dir, "build_analyzer.py")
        
        if not os.path.exists(build_analyzer_script):
            print(c("Error: build_analyzer.py not found in tools directory", Colors.RED))
            return
        
        cmd = [sys.executable, build_analyzer_script, target_path]
        if json_output:
            cmd.append("--json")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                if json_output:
                    # Parse and pretty-print JSON
                    try:
                        data = json.loads(result.stdout)
                        print(json.dumps(data, indent=2))
                    except json.JSONDecodeError:
                        print(result.stdout)
                else:
                    print(result.stdout)
            else:
                print(c(f"Error: build_analyzer failed with exit code {result.returncode}", Colors.RED))
                if result.stderr:
                    print(c("Error output:", Colors.YELLOW))
                    print(result.stderr)
        
        except subprocess.TimeoutExpired:
            print(c("Error: build_analyzer timed out after 2 minutes", Colors.RED))
        except Exception as e:
            print(c(f"Error running build_analyzer: {e}", Colors.RED))
    
    def handle_stats_command(self, args: str) -> None:
        """Handle /stats command to show token usage statistics."""
        from utils.token_stats import format_cost
        
        # Get total stats
        total_stats = self.token_stats.get_total_stats()
        agent_stats = self.token_stats.get_all_stats()
        
        if not agent_stats:
            print(c("No token usage data yet. Start chatting with agents to see statistics!", Colors.YELLOW))
            return
        
        # Print header
        print(c("\n" + "═" * 60, Colors.CYAN))
        print(c("TOKEN USAGE STATISTICS", Colors.CYAN + Colors.BOLD))
        print(c("═" * 60, Colors.CYAN))
        
        # Print total session stats
        print(c("\nSession Total:", Colors.BOLD))
        print(f"  Tokens: {total_stats['total']:,} " + 
              c(f"(input: {total_stats['input']:,}, output: {total_stats['output']:,})", Colors.DIM))
        print(f"  Cost: {format_cost(total_stats['cost'])}")
        print(f"  Messages: {total_stats['messages']}")
        if total_stats['messages'] > 0:
            avg_tokens = total_stats['total'] // total_stats['messages']
            print(f"  Avg tokens/message: {avg_tokens:,}")
        
        # If specific agent requested
        if args:
            agent_name = args.strip()
            stats = self.token_stats.get_agent_stats(agent_name)
            
            if not stats:
                print(c(f"\nNo statistics found for agent: {agent_name}", Colors.YELLOW))
                return
            
            print(c(f"\nAgent: {agent_name}", Colors.BOLD))
            print(f"  Model: {stats['model']}")
            print(f"  Tokens: {stats['total']:,} " +
                  c(f"(input: {stats['input']:,}, output: {stats['output']:,})", Colors.DIM))
            cost = self.token_stats.get_all_stats()[agent_name]['cost']
            print(f"  Cost: {format_cost(cost)}")
            print(f"  Messages: {stats['messages']}")
            if stats['messages'] > 0:
                avg_tokens = stats['total'] // stats['messages']
                print(f"  Avg tokens/message: {avg_tokens:,}")
        else:
            # Print per-agent breakdown
            print(c("\nPer-Agent Breakdown:", Colors.BOLD))
            for agent_name in sorted(agent_stats.keys()):
                stats = agent_stats[agent_name]
                print(c(f"\n  {agent_name}:", Colors.CYAN))
                print(f"    Tokens: {stats['total']:,} (cost: {format_cost(stats['cost'])})")
                print(f"    Messages: {stats['messages']}")
        
        print(c("\n" + "═" * 60, Colors.CYAN))
        print()
    
    def handle_tokenopt_stats_command(self) -> None:
        """Handle /tokenopt-stats command to show token optimization statistics."""
        if not self.optimization_enabled:
            print(c("Token optimization is not enabled. Enable it in axe.yaml to see statistics.", Colors.YELLOW))
            print(c("Set token_optimization.enabled: true", Colors.DIM))
            return
        
        stats = self.optimization_stats
        
        # Print header
        print(c("\n" + "═" * 60, Colors.CYAN))
        print(c("TOKEN OPTIMIZATION STATISTICS", Colors.CYAN + Colors.BOLD))
        print(c("═" * 60, Colors.CYAN))
        
        print(c(f"\nOptimization Mode: {self.optimization_mode}", Colors.BOLD))
        
        # Overall statistics
        print(c("\nOverall Performance:", Colors.BOLD))
        total_saved = stats.get('total_tokens_saved', 0)
        print(f"  Total tokens saved: {c(f'{total_saved:,}', Colors.GREEN)}")
        print(f"  Context optimizations: {stats.get('context_optimizations', 0)}")
        print(f"  Prompt compressions: {stats.get('prompt_compressions', 0)}")
        print(f"  Code truncations: {stats.get('code_truncations', 0)}")
        print(f"  READ blocks removed: {stats.get('read_blocks_removed', 0)}")
        
        if stats.get('last_optimization_savings', 0) > 0:
            print(c(f"\nLast optimization saved: {stats['last_optimization_savings']:,} tokens", Colors.GREEN))
        
        # Calculate session efficiency
        total_stats = self.token_stats.get_total_stats()
        total_used = total_stats.get('total', 0)
        total_saved = stats.get('total_tokens_saved', 0)
        
        if total_used > 0:
            efficiency = (total_saved / (total_used + total_saved)) * 100
            print(c("\nSession Efficiency:", Colors.BOLD))
            print(f"  Tokens used: {total_used:,}")
            print(f"  Tokens saved: {total_saved:,}")
            print(f"  Optimization rate: {c(f'{efficiency:.1f}%', Colors.GREEN)}")
            print(c(f"  (Without optimization, would have used {total_used + total_saved:,} tokens)", Colors.DIM))
        
        print(c("\n" + "═" * 60, Colors.CYAN))
        print()
    
    def handle_session_command(self, args: str) -> None:
        """Handle /session command for save/load/list operations."""
        if not args:
            print(c("Session Management Commands:", Colors.BOLD))
            print(c("  /session save <name>   - Save current session", Colors.DIM))
            print(c("  /session load <name>   - Load a saved session", Colors.DIM))
            print(c("  /session list          - List all saved sessions", Colors.DIM))
            return
        
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()
        session_arg = parts[1] if len(parts) > 1 else ""
        
        if subcommand == 'save':
            if not session_arg:
                print(c("Usage: /session save <name>", Colors.YELLOW))
                return
            
            # Create session data
            session_data = {
                'conversation': self.history,
                'workspace': self.project_dir,
                'agents': list(self.token_stats.agent_stats.keys()),
                'metadata': {
                    'tokens_used': self.token_stats.get_total_stats()['total'],
                    'messages': len(self.history)
                }
            }
            
            if self.session_manager.save_session(session_arg, session_data):
                print(c(f"✓ Session saved as: {session_arg}", Colors.GREEN))
            else:
                print(c(f"✗ Failed to save session: {session_arg}", Colors.RED))
        
        elif subcommand == 'load':
            if not session_arg:
                print(c("Usage: /session load <name>", Colors.YELLOW))
                return
            
            session_data = self.session_manager.load_session(session_arg)
            
            if not session_data:
                print(c(f"✗ Session not found: {session_arg}", Colors.RED))
                return
            
            # Restore session
            self.history = session_data.get('conversation', [])
            print(c(f"✓ Session loaded: {session_arg}", Colors.GREEN))
            print(c(f"  Workspace: {session_data.get('workspace', 'Unknown')}", Colors.DIM))
            print(c(f"  Messages: {len(self.history)}", Colors.DIM))
            print(c(f"  Agents: {', '.join(session_data.get('agents', []))}", Colors.DIM))
            print(c(f"  Saved: {session_data.get('timestamp', 'Unknown')}", Colors.DIM))
        
        elif subcommand == 'list':
            sessions = self.session_manager.list_sessions()
            
            if not sessions:
                print(c("No saved sessions found.", Colors.YELLOW))
                return
            
            print(c("\nSaved Sessions:", Colors.BOLD))
            print(c("═" * 70, Colors.CYAN))
            
            for session in sessions:
                print(c(f"\n  {session['name']}", Colors.CYAN + Colors.BOLD))
                print(f"    Saved: {session['timestamp']}")
                print(f"    Workspace: {session['workspace']}")
                if session['agents']:
                    print(f"    Agents: {', '.join(session['agents'])}")
                print(f"    Size: {session['size']} bytes")
            
            print(c("\n" + "═" * 70, Colors.CYAN))
            print()
        
        else:
            print(c(f"Unknown session subcommand: {subcommand}", Colors.YELLOW))
            print(c("Use: save, load, or list", Colors.DIM))
    
    def process_command(self, cmd: str) -> bool:
        """Process a slash command. Returns False to exit."""
        cmd = cmd.strip()
        parts: list[str] = cmd.split(maxsplit=1)
        command: str = parts[0].lower()
        args: str = parts[1] if len(parts) > 1 else ""
        
        if command in ['/quit', '/exit', '/q']:
            return False
        
        elif command == '/help':
            self.print_help()
        
        elif command == '/rules':
            print(c(SESSION_RULES, Colors.CYAN))
        
        elif command == '/agents':
            self.list_agents()
        
        elif command == '/tools':
            self.list_tools()
        
        elif command == '/dirs':
            self.list_dirs()
        
        elif command == '/config':
            if HAS_YAML:
                print(yaml.dump(self.config.config, default_flow_style=False))
            else:
                print(json.dumps(self.config.config, indent=2))
        
        elif command == '/files':
            files: list[str]
            total: int
            files, total = self.project_ctx.list_code_files()
            header: str = f"\nCode files ({len(files)}"
            if total > len(files):
                header += f" of {total} total"
            header += "):"
            print(c(header, Colors.BOLD))
            for f in files:
                print(f"  {f}")
            print()
        
        elif command == '/context':
            print(self.project_ctx.get_context_summary())
        
        elif command == '/read':
            if args:
                print(self.project_ctx.get_file_content(args))
            else:
                print(c("Usage: /read <filepath>", Colors.YELLOW))
        
        elif command == '/exec':
            if args:
                success: bool
                output: str
                success, output = self.tool_runner.run(args)
                color: str = Colors.GREEN if success else Colors.RED
                print(c(output[:1000], color))
            else:
                print(c("Usage: /exec <command>", Colors.YELLOW))
        
        elif command == '/history':
            total_entries: int = len(self.history)
            entries_to_show: list[dict[str, Any]] = self.history[-20:]
            for entry in entries_to_show:
                role: str = c(entry['role'], Colors.CYAN)
                msg: str = entry['content'][:100]
                print(f"[{role}] {msg}...")
            if total_entries > len(entries_to_show):
                print(c(f"Showing last {len(entries_to_show)} of {total_entries} history entries.", Colors.YELLOW))
        
        elif command == '/clear':
            self.history.clear()
            print(c("History cleared", Colors.GREEN))
        
        elif command == '/save':
            self.config.save()
        
        elif command == '/collab':
            if not args:
                print(c("Usage: /collab <agents> <workspace> <time_minutes> <task>", Colors.YELLOW))
                print(c("Example: /collab llama,copilot ./playground 30 Review wadextract.c", Colors.DIM))
                return True
            
            # Parse arguments: agents workspace time task
            collab_parts: list[str] = args.split(maxsplit=3)
            if len(collab_parts) < 4:
                print(c("Usage: /collab <agents> <workspace> <time_minutes> <task>", Colors.YELLOW))
                print(c("  agents: comma-separated list (e.g., llama,copilot)", Colors.DIM))
                print(c("  workspace: directory path (e.g., ./playground)", Colors.DIM))
                print(c("  time_minutes: session time limit (e.g., 30)", Colors.DIM))
                print(c("  task: description in quotes (e.g., \"Review the code\")", Colors.DIM))
                return True
            
            agents_str: str
            workspace: str
            time_str: str
            task: str
            agents_str, workspace, time_str, task = collab_parts
            agents: list[str] = [a.strip() for a in agents_str.split(',')]
            
            time_limit: int
            try:
                time_limit = int(time_str)
            except ValueError:
                print(c(f"Invalid time limit: {time_str}. Must be a number (minutes).", Colors.RED))
                return True
            
            # Resolve workspace path
            if not os.path.isabs(workspace):
                workspace = os.path.join(self.project_dir, workspace)
            
            if not os.path.exists(workspace):
                print(c(f"Workspace directory not found: {workspace}", Colors.RED))
                print(c("Creating it...", Colors.YELLOW))
                try:
                    os.makedirs(workspace, exist_ok=True)
                except Exception as e:
                    print(c(f"Failed to create workspace: {e}", Colors.RED))
                    return True
            
            # Remove quotes from task if present
            task = task.strip('"\'')
            
            try:
                collab: CollaborativeSession = CollaborativeSession(
                    config=self.config,
                    agents=agents,
                    workspace_dir=workspace,
                    time_limit_minutes=time_limit
                )
                collab.start_session(task)
            except ValueError as e:
                print(c(f"Cannot start collaboration: {e}", Colors.RED))
            except Exception as e:
                print(c(f"Collaboration error: {e}", Colors.RED))
        
        elif command == '/workshop':
            self.handle_workshop_command(args)
        
        elif command.startswith('/prep') or command.startswith('/llmprep'):
            self.handle_llmprep_command(args)
        
        elif command.startswith('/buildinfo'):
            self.handle_buildinfo_command(args)
        
        elif command == '/stats':
            self.handle_stats_command(args)
        
        elif command == '/tokenopt-stats':
            self.handle_tokenopt_stats_command()
        
        elif command == '/session':
            self.handle_session_command(args)
        
        else:
            print(c(f"Unknown command: {command}. Type /help for help.", Colors.YELLOW))
        
        return True
    
    def process_agent_message(self, message: str) -> None:
        """Process an @agent message."""
        # Parse @agent from message
        agent_name: str
        prompt: str
        if not message.startswith('@'):
            agent_name = self.default_agent
            prompt = message
        else:
            parts: list[str] = message[1:].split(maxsplit=1)
            agent_name = parts[0]
            prompt = parts[1] if len(parts) > 1 else ""
        
        if not prompt:
            print(c("Please provide a task for the agent", Colors.YELLOW))
            return
        
        # Get agent config for rate limiting checks
        agent_config = self.agent_mgr.resolve_agent(agent_name)
        if not agent_config:
            print(c(f"Unknown agent: {agent_name}", Colors.RED))
            return
        
        # Apply context optimization if needed
        self.optimize_context_if_needed(agent_name)
        
        # Check rate limit before calling (estimate based on prompt length)
        # NOTE: This is a rough heuristic estimate (chars/4 + expected response overhead).
        # The actual token count is recorded after the API call via the callback below.
        # There may be drift between estimated and actual usage during rate limit checks,
        # which could allow slightly over-limit requests or reject near-limit requests.
        estimated_tokens = len(prompt) // 4 + 1000  # Rough estimate including expected response
        allowed, rate_msg = self.rate_limiter.check_limit(agent_name, estimated_tokens)
        
        if not allowed:
            print(c(f"⏱️  {rate_msg}", Colors.RED))
            return
        
        # Get context
        context: str = self.project_ctx.get_context_summary()
        
        # Record in history
        self.history.append({'role': 'user', 'agent': agent_name, 'content': prompt})
        
        # Define token callback for tracking
        def token_callback(agent, model, input_tokens, output_tokens):
            self.token_stats.add_usage(agent, model, input_tokens, output_tokens)
            self.rate_limiter.add_tokens(agent, input_tokens + output_tokens)
        
        # Get optimized system prompt if optimization enabled
        optimized_prompt = self.get_optimized_system_prompt(agent_name)
        
        # Warn if prompt compression is active (code minification)
        if self.optimization_enabled and optimized_prompt:
            optimization_config = self.config.get('token_optimization', default={})
            prompt_config = optimization_config.get('prompt_compression', {})
            compression_level = prompt_config.get('compression_level', 'balanced')
            
            # Show warning for aggressive compression
            if compression_level == 'aggressive':
                print(c("⚠️  Caution: Aggressive prompt compression active - system prompts are heavily compressed!", Colors.YELLOW))
            elif compression_level == 'balanced' and len(optimized_prompt) > 0:
                # Show subtle note for balanced compression (only once per session)
                if not hasattr(self, '_compression_warned'):
                    print(c("ℹ️  Note: Prompt compression is active (balanced mode)", Colors.DIM))
                    self._compression_warned = True
        
        # Call agent with token tracking and optimized prompt
        print(c(f"\n[{agent_name}] Processing...", Colors.DIM))
        response: str = self.agent_mgr.call_agent(
            agent_name, 
            prompt, 
            context, 
            token_callback=token_callback,
            system_prompt_override=optimized_prompt if optimized_prompt else None
        )
        
        # Process response for code blocks (READ, EXEC, WRITE)
        processed_response: str = self.response_processor.process_response(response, agent_name)
        
        # Clean response for context if optimization enabled
        cleaned_response = self.clean_message_for_context(processed_response)
        
        # Record response (use cleaned version to save context tokens)
        self.history.append({'role': agent_name, 'content': cleaned_response})
        
        # Print response (use full version for user display)
        print(c(f"\n[{agent_name}]:", Colors.CYAN + Colors.BOLD))
        print(processed_response)
        print()
    
    def optimize_context_if_needed(self, agent_name: str) -> None:
        """
        Apply context optimization if enabled and needed.
        
        Args:
            agent_name: Name of the agent for context limits
        """
        if not self.optimization_enabled or not self.context_optimizer:
            return
        
        # Get agent context tokens
        agent = self.agent_mgr.resolve_agent(agent_name)
        if not agent:
            return
        
        context_tokens = agent.get('context_tokens', 100000)
        optimization_config = self.config.get('token_optimization', default={})
        context_config = optimization_config.get('context_management', {})
        
        if not context_config.get('enabled', True):
            return
        
        max_context = context_config.get('max_context_tokens', 100000)
        max_context = min(max_context, int(context_tokens * 0.8))  # Use 80% of available
        
        # Convert history to Message objects
        from utils.context_optimizer import Message
        messages = []
        for entry in self.history:
            role = entry.get('role', 'user')
            content = entry.get('content', '')
            messages.append(Message(role=role, content=content))
        
        # Check if optimization is needed
        total_tokens = sum(self.context_optimizer.token_counter(m.content) for m in messages)
        threshold = context_config.get('summarize_threshold', 0.7)
        
        # Apply deduplication if configured
        response_config = optimization_config.get('response_optimization', {})
        if response_config.get('deduplicate_content', True):
            before_dedup = len(messages)
            messages = self.context_optimizer.deduplicate_context(messages)
            if len(messages) < before_dedup:
                print(c(f"✓ Deduplicated {before_dedup - len(messages)} duplicate messages", Colors.GREEN))
        
        if total_tokens > max_context * threshold:
            print(c(f"⚡ Optimizing context ({total_tokens} tokens -> {max_context} limit)...", Colors.YELLOW))
            
            keep_recent = context_config.get('keep_recent_messages', 10)
            optimized = self.context_optimizer.optimize_conversation(
                messages, 
                max_tokens=max_context,
                keep_recent=keep_recent,
                summarize_old=True
            )
            
            # Convert back to history format
            self.history = []
            for msg in optimized:
                self.history.append({'role': msg.role, 'content': msg.content})
            
            new_total = sum(self.context_optimizer.token_counter(m.content) for m in optimized)
            savings = total_tokens - new_total
            
            # Track statistics
            if self.optimization_enabled:
                self.optimization_stats['context_optimizations'] += 1
                self.optimization_stats['total_tokens_saved'] += savings
                self.optimization_stats['last_optimization_savings'] = savings
            
            print(c(f"✓ Saved {savings} tokens ({(savings/total_tokens)*100:.1f}%)", Colors.GREEN))
    
    def get_optimized_system_prompt(self, agent_name: str) -> str:
        """
        Get optimized system prompt for an agent.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Optimized system prompt
        """
        agent = self.agent_mgr.resolve_agent(agent_name)
        if not agent:
            return ""
        
        original_prompt = agent.get('system_prompt', '')
        
        # Apply compression if enabled
        if self.optimization_enabled and self.prompt_compressor:
            optimization_config = self.config.get('token_optimization', default={})
            prompt_config = optimization_config.get('prompt_compression', {})
            
            if prompt_config.get('enabled', True) and prompt_config.get('compress_system_prompts', True):
                level = prompt_config.get('compression_level', 'balanced')
                compressed = self.prompt_compressor.compress(original_prompt, level=level)
                
                # Only use compressed if it actually saves tokens
                if len(compressed) < len(original_prompt) * 0.9:  # At least 10% savings
                    # Track statistics
                    if self.optimization_enabled:
                        self.optimization_stats['prompt_compressions'] += 1
                        savings = (len(original_prompt) - len(compressed)) // CHARS_PER_TOKEN
                        self.optimization_stats['total_tokens_saved'] += savings
                    return compressed
        
        return original_prompt
    
    def clean_message_for_context(self, content: str) -> str:
        """
        Clean message content for inclusion in context.
        
        Args:
            content: Original message content
        
        Returns:
            Cleaned content
        """
        if not self.optimization_enabled or not self.context_optimizer:
            return content
        
        optimization_config = self.config.get('token_optimization', default={})
        response_config = optimization_config.get('response_optimization', {})
        
        if not response_config.get('enabled', True):
            return content
        
        cleaned = content
        
        # Remove READ blocks if configured
        if response_config.get('remove_read_blocks', True):
            before_clean = len(cleaned)
            cleaned = self.context_optimizer.clean_content(cleaned)
            after_clean = len(cleaned)
            if after_clean < before_clean and self.optimization_enabled:
                self.optimization_stats['read_blocks_removed'] += 1
        
        # Truncate code blocks if configured
        if response_config.get('truncate_code_blocks', True):
            max_lines = response_config.get('max_code_lines', 100)
            before_truncate = len(cleaned)
            cleaned = self.context_optimizer.truncate_code(cleaned, max_lines=max_lines)
            after_truncate = len(cleaned)
            if after_truncate < before_truncate and self.optimization_enabled:
                self.optimization_stats['code_truncations'] += 1
                savings = (before_truncate - after_truncate) // CHARS_PER_TOKEN
                self.optimization_stats['total_tokens_saved'] += savings
        
        return cleaned
    
    def run(self) -> None:
        """Run interactive chat session."""
        self.print_banner()
        
        try:
            while True:
                prompt: str
                try:
                    prompt = input(c("axe> ", Colors.GREEN + Colors.BOLD))
                except EOFError:
                    break
                
                prompt = prompt.strip()
                
                if not prompt:
                    continue
                
                if prompt.startswith('/'):
                    if not self.process_command(prompt):
                        break
                else:
                    self.process_agent_message(prompt)
                    
        except KeyboardInterrupt:
            print(c("\nInterrupted", Colors.YELLOW))
        
        print(c("Goodbye!", Colors.CYAN))


def generate_sample_config(path: str = 'axe.yaml') -> None:
    """Generate a sample configuration file."""
    config = Config()
    config.save(path)
    print(c(f"Generated sample config: {path}", Colors.GREEN))
    print("Edit this file to customize your setup.")


# ========== Persistence Lifecycle Hooks ==========

# Global reference to database for shutdown hook
_global_db = None


def restore_agents_on_startup(db_path: Optional[str] = None) -> None:
    """
    Display agents from database on startup (informational only).
    
    Note: This function displays agent information from previous sessions
    but does not automatically recreate them in the current session.
    Agents must be explicitly spawned via collaborative sessions or
    other mechanisms. This is informational to show what agents
    existed in previous sessions.
    
    Args:
        db_path: Optional path to SQLite database. If None, uses AXE installation directory.
    """
    global _global_db
    _global_db = AgentDatabase(db_path)
    
    agents = _global_db.restore_all_agents()
    
    if agents:
        print(c(f"\n✓ Found {len(agents)} agent(s) from previous session:", Colors.GREEN))
        print(c("   (Informational only - agents not automatically restored)", Colors.DIM))
        for agent in agents[:5]:  # Show first 5
            status_color = Colors.GREEN if agent['status'] == 'active' else Colors.YELLOW
            print(f"  • {agent['alias']} ({agent['model_name']}) - "
                  f"Level {agent['level']}, {agent['xp']} XP - "
                  f"{c(agent['status'], status_color)}")
        
        if len(agents) > 5:
            print(f"  ... and {len(agents) - 5} more")
        print()


def sync_agents_on_shutdown() -> None:
    """
    Sync agent state to database on shutdown.
    This is called automatically via atexit.
    """
    global _global_db
    if _global_db:
        # Database sync happens automatically via save_agent_state
        # This hook is here for future extensions
        pass


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AXE - Agent eXecution Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  axe.py                           Interactive chat mode
  axe.py -c "@gpt analyze main.c"  Single command
  axe.py --config my.yaml          Use custom config
  axe.py --init                    Generate sample config
  
Collaborative Mode:
  axe.py --collab llama,copilot --workspace ./playground --time 30 --task "Review code"
        """
    )
    
    parser.add_argument('-d', '--dir', default='.', 
                        help='Project directory (default: current)')
    parser.add_argument('-c', '--command',
                        help='Single command to execute')
    parser.add_argument('--config',
                        help='Config file path (YAML or JSON)')
    parser.add_argument('--init', action='store_true',
                        help='Generate sample config file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry-run mode for tool executions')
    
    # Collaborative mode arguments
    parser.add_argument('--collab',
                        help='Start collaborative session with comma-separated agents (e.g., llama,copilot)')
    parser.add_argument('--workspace',
                        help='Workspace directory for collaborative session')
    parser.add_argument('--time', type=int, default=30,
                        help='Time limit in minutes for collaborative session (default: 30)')
    parser.add_argument('--task',
                        help='Task description for collaborative session')
    parser.add_argument('--enable-github', action='store_true',
                        help='Enable autonomous GitHub operations (disabled by default)')
    
    args = parser.parse_args()
    
    # Register shutdown hook
    atexit.register(sync_agents_on_shutdown)
    
    # Generate sample config
    if args.init:
        generate_sample_config()
        return
    
    # Restore agents from previous session (optional, informational)
    try:
        restore_agents_on_startup()
    except Exception:
        # Don't fail if restoration fails, just continue
        pass
    
    # Start resource monitoring
    start_resource_monitor()
    
    # Load config
    config = Config(args.config)
    
    # Override project dir
    if args.dir:
        config.config['project_dir'] = args.dir
    
    # Collaborative mode
    if args.collab:
        if not args.task:
            print(c("Error: --task is required for collaborative mode", Colors.RED))
            print(c("Example: --collab llama,copilot --task \"Review the code\"", Colors.DIM))
            return
        
        agents = [a.strip() for a in args.collab.split(',')]
        workspace = args.workspace if args.workspace else args.dir
        
        # Ensure workspace is not None (args.dir defaults to '.')
        if workspace is None:
            workspace = '.'
        
        if not os.path.isabs(workspace):
            workspace = os.path.abspath(workspace)
        
        if not os.path.exists(workspace):
            print(c(f"Creating workspace: {workspace}", Colors.YELLOW))
            os.makedirs(workspace, exist_ok=True)
        
        # Run preprocessing if enabled (environment_probe, minifier and/or llmprep)
        preprocessor = SessionPreprocessor(config, workspace)
        if preprocessor.is_enabled():
            print(c("Running session preprocessing...", Colors.CYAN))
            preprocessing_results = preprocessor.run()
            
            # Display environment probe results
            if preprocessing_results['environment_probe']['enabled']:
                env_result = preprocessing_results['environment_probe']
                if env_result.get('success'):
                    output_file = env_result.get('output_file', '.collab_env.md')
                    print(c(f"✓ Environment Probe: System info captured in {os.path.basename(output_file)}", Colors.GREEN))
                else:
                    error = env_result.get('error', 'Unknown error')
                    print(c(f"✗ Environment Probe failed: {error}", Colors.YELLOW))
            
            # Display minifier results
            if preprocessing_results['minifier']['enabled']:
                minifier_result = preprocessing_results['minifier']
                if minifier_result.get('success'):
                    files_processed = minifier_result.get('files_processed', 0)
                    bytes_saved = minifier_result.get('bytes_saved', 0)
                    bytes_original = minifier_result.get('bytes_original', 0)
                    
                    if files_processed > 0:
                        reduction_pct = (bytes_saved / bytes_original * 100) if bytes_original > 0 else 0
                        print(c(f"✓ Minifier: Processed {files_processed} file(s), saved {bytes_saved:,} bytes ({reduction_pct:.1f}% reduction)", Colors.GREEN))
                    else:
                        print(c("✓ Minifier: No files to process", Colors.DIM))
                else:
                    error = minifier_result.get('error', 'Unknown error')
                    print(c(f"✗ Minifier failed: {error}", Colors.YELLOW))
            
            # Display llmprep results
            if preprocessing_results['llmprep']['enabled']:
                llmprep_result = preprocessing_results['llmprep']
                if llmprep_result.get('success'):
                    output_dir = llmprep_result.get('output_dir', 'llm_prep')
                    print(c(f"✓ llmprep: Context files generated in {output_dir}/", Colors.GREEN))
                else:
                    error = llmprep_result.get('error', 'Unknown error')
                    print(c(f"✗ llmprep failed: {error}", Colors.YELLOW))
            
            print()  # Blank line after preprocessing
        
        try:
            collab = CollaborativeSession(
                config=config,
                agents=agents,
                workspace_dir=workspace,
                time_limit_minutes=args.time,
                github_enabled=args.enable_github
            )
            collab.start_session(args.task)
        except ValueError as e:
            print(c(f"Cannot start collaboration: {e}", Colors.RED))
        except Exception as e:
            print(c(f"Collaboration error: {e}", Colors.RED))
        return
    
    # Create session
    session = ChatSession(config, args.dir)
    
    # Run preprocessing if enabled (environment_probe, minifier and/or llmprep)
    preprocessor = SessionPreprocessor(config, args.dir)
    if preprocessor.is_enabled():
        print(c("Running session preprocessing...", Colors.CYAN))
        preprocessing_results = preprocessor.run()
        
        # Display environment probe results
        if preprocessing_results['environment_probe']['enabled']:
            env_result = preprocessing_results['environment_probe']
            if env_result.get('success'):
                output_file = env_result.get('output_file', '.collab_env.md')
                print(c(f"✓ Environment Probe: System info captured in {os.path.basename(output_file)}", Colors.GREEN))
            else:
                error = env_result.get('error', 'Unknown error')
                print(c(f"✗ Environment Probe failed: {error}", Colors.YELLOW))
        
        # Display minifier results
        if preprocessing_results['minifier']['enabled']:
            minifier_result = preprocessing_results['minifier']
            if minifier_result.get('success'):
                files_processed = minifier_result.get('files_processed', 0)
                bytes_saved = minifier_result.get('bytes_saved', 0)
                bytes_original = minifier_result.get('bytes_original', 0)
                
                if files_processed > 0:
                    reduction_pct = (bytes_saved / bytes_original * 100) if bytes_original > 0 else 0
                    print(c(f"✓ Minifier: Processed {files_processed} file(s), saved {bytes_saved:,} bytes ({reduction_pct:.1f}% reduction)", Colors.GREEN))
                else:
                    print(c("✓ Minifier: No files to process", Colors.DIM))
            else:
                error = minifier_result.get('error', 'Unknown error')
                print(c(f"✗ Minifier failed: {error}", Colors.YELLOW))
        
        # Display llmprep results
        if preprocessing_results['llmprep']['enabled']:
            llmprep_result = preprocessing_results['llmprep']
            if llmprep_result.get('success'):
                output_dir = llmprep_result.get('output_dir', 'llm_prep')
                print(c(f"✓ llmprep: Context files generated in {output_dir}/", Colors.GREEN))
            else:
                error = llmprep_result.get('error', 'Unknown error')
                print(c(f"✗ llmprep failed: {error}", Colors.YELLOW))
        
        print()  # Blank line after preprocessing
    
    # Update tool runner settings
    session.tool_runner.dry_run = args.dry_run
    
    # Single command mode
    if args.command:
        session.process_agent_message(args.command)
        return
    
    # Interactive mode
    session.run()


if __name__ == '__main__':
    main()
