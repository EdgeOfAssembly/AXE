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
import shlex
import json
import sqlite3
import uuid
import threading
import base64
import hashlib
import atexit
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any
import time
import shutil

# readline import enables command history in terminal (side effect import)
try:
    import readline  # noqa: F401
except ImportError:
    pass  # readline not available on all platforms

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

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from huggingface_hub import InferenceClient
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False

# Import from new modular structure
from utils.formatting import Colors, colorize, c
from safety.rules import SESSION_RULES
from progression.xp_system import calculate_xp_for_level
from progression.levels import (
    get_title_for_level,
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER,
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE
)
from database.agent_db import AgentDatabase
from models.metadata import get_model_info, format_token_count

# Models that require max_completion_tokens instead of max_tokens
# GPT-5 and future models use the new parameter name
USE_MAX_COMPLETION_TOKENS = {
    "gpt-5",
    "gpt-5-0806", 
    "gpt-5.2-2025-12-11",
    "gpt-5.2",
    "o1-preview",
    "o1-mini",
    "o1",
    "o3-mini"
}

# Collaborative session constants
COLLAB_HISTORY_LIMIT = 20      # Max messages to show in conversation history
COLLAB_CONTENT_LIMIT = 2000    # Max chars per message in history
COLLAB_PASS_MULTIPLIER = 2     # Times agents can pass before session ends
COLLAB_SHARED_NOTES_LIMIT = 500  # Max chars of shared notes to show

# Experience and level constants (now imported from progression module)
# XP_PER_LEVEL_LINEAR = 100       # Imported from progression.xp_system
# LEVEL_SENIOR_WORKER = 10        # Imported from progression.levels
# LEVEL_TEAM_LEADER = 20          # Imported from progression.levels
# LEVEL_DEPUTY_SUPERVISOR = 30    # Imported from progression.levels
# LEVEL_SUPERVISOR_ELIGIBLE = 40  # Imported from progression.levels

# Resource monitoring constants
RESOURCE_UPDATE_INTERVAL = 60   # Seconds between resource snapshots
RESOURCE_FILE = "/tmp/axe_resources.txt"

# Phase 6: Mandatory sleep system constants
MAX_WORK_HOURS = 6              # Maximum continuous work hours before mandatory sleep
MIN_SLEEP_MINUTES = 30          # Minimum sleep duration in minutes
WORK_TIME_WARNING_HOURS = 5     # Warn when agent approaches work limit
SLEEP_REASON_TIMEOUT = "work_time_limit"
SLEEP_REASON_DEGRADATION = "error_threshold"
SLEEP_REASON_MANUAL = "manual_request"
SLEEP_REASON_BREAK = "break_request"

# Phase 7: Degradation monitoring constants
ERROR_THRESHOLD_PERCENT = 20    # Force sleep if error rate exceeds this
DIFF_HISTORY_LIMIT = 20         # Number of recent diffs to track for error analysis
DEGRADATION_CHECK_INTERVAL = 5  # Check degradation every N turns

# Phase 8: Emergency mailbox constants
EMERGENCY_MAILBOX_DIR = "/tmp/axe_emergency_mailbox"
GPG_PUBLIC_KEY_FILE = "/tmp/axe_emergency_mailbox/human_public.key"

# Phase 9: Break system constants
MAX_BREAK_MINUTES = 15          # Maximum break duration
MAX_BREAKS_PER_HOUR = 2         # Maximum breaks per hour
MIN_WORKLOAD_FOR_BREAK = 0.3    # Break only allowed if workload < 30%
MAX_WORKFORCE_ON_BREAK = 0.4    # Never more than 40% of agents on break

# Phase 10: Dynamic spawning constants
MIN_ACTIVE_AGENTS = 2           # Minimum agents that must be active
MAX_TOTAL_AGENTS = 10           # Maximum total agents allowed
SPAWN_COOLDOWN_SECONDS = 60     # Minimum time between spawns

# Session rules displayed at startup (now imported from safety.rules module)
# SESSION_RULES = """..."""  # Commented out - imported from safety.rules

# Default configuration
DEFAULT_CONFIG = {
    'version': '1.0',
    'project_dir': '.',
    
    # API providers configuration
    'providers': {
        'anthropic': {
            'enabled': True,
            'env_key': 'ANTHROPIC_API_KEY',
            'models': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-5-sonnet-20240620']
        },
        'openai': {
            'enabled': True,
            'env_key': 'OPENAI_API_KEY',
            'models': ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo']
        },
        'huggingface': {
            'enabled': True,
            'env_key': 'HUGGINGFACE_API_KEY',
            'models': ['meta-llama/Llama-3.1-70B-Instruct', 'meta-llama/Llama-3.1-8B-Instruct']
        },
        'xai': {
            'enabled': True,
            'env_key': 'XAI_API_KEY',
            'base_url': 'https://api.x.ai/v1',
            'models': ['grok-beta', 'grok-2']
        },
        'github': {
            'enabled': True,
            'env_key': 'GITHUB_TOKEN',
            'base_url': 'https://models.github.ai/inference',
            'models': ['openai/gpt-4o', 'openai/gpt-4o-mini']
        }
    },
    
    # Agent definitions with short aliases
    'agents': {
        'gpt': {
            'alias': ['g', 'openai'],
            'provider': 'openai',
            'model': 'gpt-4o',
            'role': 'General-purpose coder and architect',
            'context_window': 128000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are an expert software engineer. Provide clear, working code.
For C/C++: Prefer portable code; when DOS/16-bit targets are requested, explain that true DOS support typically needs compilers like Open Watcom or DJGPP and that 16-bit ints/far pointers are non-standard in modern toolchains.
For Python: Clean, type-hinted code.
For reverse-engineering: Use hexdump/objdump analysis."""
        },
        'claude': {
            'alias': ['c', 'anthropic'],
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022',
            'role': 'Code reviewer and security auditor',
            'context_window': 200000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are a code review expert and security auditor.
Analyze code for bugs, security issues, and improvements.
For rev-eng: Check endianness, memory safety, DOS compatibility."""
        },
        'llama': {
            'alias': ['l', 'hf'],
            'provider': 'huggingface',
            'model': 'meta-llama/Llama-3.1-70B-Instruct',
            'role': 'Open-source hacker and asm expert',
            'context_window': 128000,
            'capabilities': ['text'],
            'system_prompt': """You are an open-source hacker fluent in x86 assembly.
Specialize in nasm, DOS interrupts, binary analysis.
Use hexdump, objdump, ndisasm for reverse engineering."""
        },
        'grok': {
            'alias': ['x', 'xai'],
            'provider': 'xai',
            'model': 'grok-beta',
            'role': 'Creative problem solver',
            'context_window': 131072,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are a creative coding assistant.
Think outside the box for novel solutions.
Good at brainstorming and unconventional approaches."""
        },
        'copilot': {
            'alias': ['cp', 'gh'],
            'provider': 'github',
            'model': 'openai/gpt-4o',
            'role': 'GitHub-integrated assistant',
            'context_window': 128000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are a GitHub Copilot-style assistant.
Help with code completion, documentation, and testing.
Focus on practical, working solutions."""
        }
    },
    
    # Tool whitelist with categories
    'tools': {
        'download': ['curl', 'wget', 'wget2'],
        'emulation': ['xvfb-run', 'dosbox-x', 'dosbox'],
        'vcs': ['git', 'diff', 'patch'],
        'disasm': ['ndisasm', 'objdump', 'hexdump', 'readelf', 'nm', 'strings'],
        'assembly': ['nasm', 'as', 'gas'],
        'debug': ['gdb', 'lldb', 'strace', 'ltrace', 'valgrind'],
        'build': ['make', 'cmake', 'gcc', 'g++', 'clang', 'clang++', 'ld'],
        'python': ['python', 'python3', 'pip', 'pytest', 'pylint', 'mypy'],
        'analysis': ['cppcheck', 'clang-format', 'clang-tidy']
    },
    
    # Directory access control
    'directories': {
        'allowed': ['.', './src', './include', './tests', './tools'],
        'readonly': ['./vendor', './deps'],
        'forbidden': ['/etc', '/root', '~/.ssh']
    },
    
    # File extensions for code detection
    'code_extensions': ['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx',
                        '.py', '.pyx', '.pyi',
                        '.asm', '.s', '.inc',
                        '.exe', '.com', '.wad', '.bin']
}


# XP and title functions now imported from progression module
# def calculate_xp_for_level(level: int) -> int: ...  # See progression/xp_system.py
# def get_title_for_level(level: int) -> str: ...     # See progression/levels.py


# AgentDatabase class now imported from database module
# The original AgentDatabase class (lines 291-764) has been moved to database/agent_db.py
# All methods including award_xp, save_agent_state, load_agent_state, sleep management,
# degradation monitoring, and break system are now in the modular structure.


def collect_resources() -> str:
    """Collect system resource information."""
    timestamp = datetime.now(timezone.utc).isoformat()
    output = [f"--- Resource Snapshot @ {timestamp} ---"]
    
    try:
        # Disk usage
        output.append("\nDisk Usage (df -h):")
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
        output.append(result.stdout.strip())
        
        # Memory
        output.append("\nMemory (free -h):")
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        output.append(result.stdout.strip())
        
        # Load average
        output.append("\nLoad Average (uptime):")
        result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        output.append(result.stdout.strip())
        
    except Exception as e:
        output.append(f"\nError collecting resources: {e}")
    
    return "\n".join(output)


def resource_monitor_thread():
    """Background thread that updates the resource file periodically."""
    while True:
        try:
            resources = collect_resources()
            with open(RESOURCE_FILE, 'w') as f:
                f.write(resources)
        except Exception as e:
            # Log error but don't crash the thread
            try:
                with open(RESOURCE_FILE, 'a') as f:
                    f.write(f"\n\nError in resource monitor: {e}\n")
            except:
                pass
        
        time.sleep(RESOURCE_UPDATE_INTERVAL)


def start_resource_monitor():
    """Start the background resource monitoring thread."""
    # Clean old file if it exists
    if os.path.exists(RESOURCE_FILE):
        try:
            os.remove(RESOURCE_FILE)
        except:
            pass
    
    thread = threading.Thread(target=resource_monitor_thread, daemon=True)
    thread.start()
    print(c(f"Resource monitoring started → {RESOURCE_FILE}", Colors.DIM))


# ========== Phase 8: Emergency Mailbox ==========

class EmergencyMailbox:
    """
    GPG-encrypted emergency communication channel for workers to report issues
    directly to humans, bypassing the supervisor.
    
    Workers can write encrypted reports about supervisor abuse, safety violations,
    or other critical issues that the supervisor cannot read.
    """
    
    def __init__(self, mailbox_dir: str = EMERGENCY_MAILBOX_DIR):
        self.mailbox_dir = mailbox_dir
        self.public_key_file = os.path.join(mailbox_dir, "human_public.key")
        self._init_mailbox()
    
    def _init_mailbox(self) -> None:
        """Initialize the mailbox directory with secure permissions."""
        try:
            os.makedirs(self.mailbox_dir, exist_ok=True)
            # Set permissions: owner rwx, group rx, others nothing (750)
            os.chmod(self.mailbox_dir, 0o750)
        except (OSError, PermissionError) as e:
            print(c(f"Warning: Could not initialize emergency mailbox: {e}", Colors.YELLOW))
    
    def set_human_public_key(self, public_key: str) -> bool:
        """Set the human's public key for encryption."""
        try:
            with open(self.public_key_file, 'w') as f:
                f.write(public_key)
            os.chmod(self.public_key_file, 0o644)  # Readable by all
            return True
        except (OSError, IOError) as e:
            print(c(f"Error setting public key: {e}", Colors.RED))
            return False
    
    def _encrypt_message(self, message: str) -> str:
        """
        Encrypt a message using simple base64 encoding as a fallback.
        
        ⚠️ WARNING: This is a DEMONSTRATION ONLY encryption.
        NOT SECURE for production use. For real security, implement
        proper GPG encryption with the human's public key:
            gpg --encrypt --armor --recipient <human_key_id>
        """
        # DEMO ONLY: base64 + simple obfuscation
        # Production should use proper GPG encryption
        timestamp = datetime.now(timezone.utc).isoformat()
        full_message = f"TIMESTAMP: {timestamp}\n\n{message}"
        
        # Simple encryption: base64 + XOR with timestamp-based key
        key = hashlib.sha256(timestamp.encode()).digest()
        encrypted_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(full_message.encode())])
        encoded = base64.b64encode(encrypted_bytes).decode()
        
        return f"-----BEGIN ENCRYPTED MESSAGE-----\n{encoded}\n-----END ENCRYPTED MESSAGE-----"
    
    def send_report(self, agent_alias: str, report_type: str, 
                   subject: str, details: str) -> Tuple[bool, str]:
        """
        Send an encrypted report to the emergency mailbox.
        
        Args:
            agent_alias: The alias of the reporting agent (@llama1, etc.)
            report_type: Type of report (supervisor_abuse, safety_violation, etc.)
            subject: Brief subject line
            details: Full details of the report
        
        Returns:
            Tuple of (success, message/filename)
        """
        timestamp = datetime.now(timezone.utc)
        filename = f"emergency_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}_{agent_alias.replace('@', '')}.gpg"
        filepath = os.path.join(self.mailbox_dir, filename)
        
        # Build the report
        report = f"""EMERGENCY REPORT
================
From: {agent_alias}
Type: {report_type}
Subject: {subject}
Timestamp: {timestamp.isoformat()}

DETAILS:
{details}

---
This message was encrypted by the agent and can only be read by the human operator.
"""
        
        try:
            encrypted = self._encrypt_message(report)
            with open(filepath, 'w') as f:
                f.write(encrypted)
            
            # Set file permissions: owner rw only (600)
            os.chmod(filepath, 0o600)
            
            return True, filename
        except (OSError, IOError) as e:
            return False, f"Error writing report: {e}"
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List all unread reports in the mailbox (for human viewing)."""
        reports = []
        try:
            for filename in os.listdir(self.mailbox_dir):
                if filename.endswith('.gpg'):
                    filepath = os.path.join(self.mailbox_dir, filename)
                    stat = os.stat(filepath)
                    reports.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'path': filepath
                    })
        except (OSError, PermissionError):
            pass
        
        return sorted(reports, key=lambda x: x['created'], reverse=True)
    
    def decrypt_report(self, filename: str, private_key: str = None) -> Optional[str]:
        """
        Decrypt a report (for human use only).
        In production, this would use GPG with the human's private key.
        """
        filepath = os.path.join(self.mailbox_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Extract encrypted content
            start = content.find('-----BEGIN ENCRYPTED MESSAGE-----') + 34
            end = content.find('-----END ENCRYPTED MESSAGE-----')
            encoded = content[start:end].strip()
            
            # Decode (simple fallback - in production use GPG)
            encrypted_bytes = base64.b64decode(encoded)
            
            # Extract timestamp from first line to regenerate key
            # This is simplified - real implementation would use GPG
            return f"[ENCRYPTED CONTENT - Requires GPG decryption]\n\nFile: {filename}"
            
        except Exception as e:
            return f"Error decrypting: {e}"


# ========== Phase 6: Sleep Manager ==========

class SleepManager:
    """
    Manages mandatory sleep system for agents.
    
    Features:
    - Track continuous work time (6-8 hour limit)
    - Force sleep when degradation detected
    - Graceful handover before sleep
    - Resume from last state after rest
    """
    
    def __init__(self, db: AgentDatabase):
        self.db = db
        self.sleep_queue: Dict[str, datetime] = {}  # agent_id -> wake_time
    
    def check_all_agents(self) -> List[Dict[str, Any]]:
        """Check all active agents for mandatory sleep requirements."""
        alerts = []
        active_agents = self.db.get_active_agents()
        
        for agent in active_agents:
            agent_id = agent['agent_id']
            
            # Check work time limit
            needs_sleep, msg = self.db.check_mandatory_sleep(agent_id)
            if needs_sleep:
                alerts.append({
                    'agent_id': agent_id,
                    'alias': agent['alias'],
                    'reason': SLEEP_REASON_TIMEOUT,
                    'message': msg
                })
                continue
            
            # Check degradation
            degraded, deg_msg = self.db.check_degradation(agent_id)
            if degraded:
                alerts.append({
                    'agent_id': agent_id,
                    'alias': agent['alias'],
                    'reason': SLEEP_REASON_DEGRADATION,
                    'message': deg_msg
                })
        
        return alerts
    
    def force_sleep(self, agent_id: str, reason: str, 
                   supervisor_id: str = None) -> Dict[str, Any]:
        """Force an agent to sleep."""
        result = self.db.put_agent_to_sleep(agent_id, reason)
        
        # Log the event
        if supervisor_id:
            self.db.log_supervisor_event(supervisor_id, 'force_sleep', {
                'agent_id': agent_id,
                'agent_alias': result['alias'],
                'reason': reason,
                'sleep_duration': result['sleep_duration_minutes']
            })
        
        # Track wake time
        wake_time = datetime.now(timezone.utc) + timedelta(minutes=result['sleep_duration_minutes'])
        self.sleep_queue[agent_id] = wake_time
        
        return result
    
    def check_and_wake_agents(self) -> List[Dict[str, Any]]:
        """Check for agents ready to wake up."""
        woken = []
        now = datetime.now(timezone.utc)
        
        to_remove = []
        for agent_id, wake_time in self.sleep_queue.items():
            if now >= wake_time:
                result = self.db.wake_agent(agent_id)
                woken.append(result)
                to_remove.append(agent_id)
        
        for agent_id in to_remove:
            del self.sleep_queue[agent_id]
        
        return woken
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all agent sleep statuses."""
        active = self.db.get_active_agents()
        sleeping = self.db.get_sleeping_agents()
        
        return {
            'active_count': len(active),
            'sleeping_count': len(sleeping),
            'active_agents': active,
            'sleeping_agents': sleeping,
            'pending_wakes': len(self.sleep_queue)
        }


# ========== Phase 9: Break System ==========

class BreakSystem:
    """
    Manages coffee/play breaks for agents.
    
    Rules:
    - Only when workload is low (<30% utilization)
    - Max 10-15 min per break
    - Max 2 breaks per hour
    - Never more than 40% of workforce on break
    """
    
    def __init__(self, db: AgentDatabase):
        self.db = db
        self.break_queue: Dict[str, datetime] = {}  # agent_id -> break_end_time
        self.pending_requests: List[Dict[str, Any]] = []
    
    def request_break(self, agent_id: str, alias: str, 
                     break_type: str, justification: str) -> Dict[str, Any]:
        """
        Request a break for an agent.
        
        Args:
            agent_id: Unique agent identifier
            alias: Agent's display alias
            break_type: 'coffee' or 'play'
            justification: Why the agent needs a break
        
        Returns:
            Request status and details
        """
        request = {
            'id': str(uuid.uuid4()),
            'agent_id': agent_id,
            'alias': alias,
            'break_type': break_type,
            'justification': justification,
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'status': 'pending'
        }
        
        self.pending_requests.append(request)
        
        return request
    
    def approve_break(self, request_id: str, duration_minutes: int = 10,
                     supervisor_alias: str = "@boss") -> Dict[str, Any]:
        """Approve a pending break request."""
        # Find the request
        request = None
        for req in self.pending_requests:
            if req['id'] == request_id:
                request = req
                break
        
        if not request:
            return {'approved': False, 'reason': 'Request not found'}
        
        agent_id = request['agent_id']
        
        # Check if break is allowed
        total_agents = len(self.db.get_active_agents()) + len(self.break_queue)
        agents_on_break = len(self.break_queue)
        
        can_break, reason = self.db.can_take_break(agent_id, total_agents, agents_on_break)
        
        if not can_break:
            request['status'] = 'denied'
            request['deny_reason'] = reason
            return {'approved': False, 'reason': reason}
        
        # Cap duration
        duration_minutes = min(duration_minutes, MAX_BREAK_MINUTES)
        
        # Record the break
        self.db.record_break(agent_id, request['break_type'], duration_minutes)
        
        # Set break end time
        end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self.break_queue[agent_id] = end_time
        
        # Update request status
        request['status'] = 'approved'
        request['approved_by'] = supervisor_alias
        request['duration_minutes'] = duration_minutes
        request['ends_at'] = end_time.isoformat()
        
        return {
            'approved': True,
            'agent_id': agent_id,
            'alias': request['alias'],
            'break_type': request['break_type'],
            'duration_minutes': duration_minutes,
            'ends_at': end_time.isoformat()
        }
    
    def deny_break(self, request_id: str, reason: str) -> Dict[str, Any]:
        """Deny a pending break request."""
        for request in self.pending_requests:
            if request['id'] == request_id:
                request['status'] = 'denied'
                request['deny_reason'] = reason
                return {'denied': True, 'request_id': request_id, 'reason': reason}
        
        return {'denied': False, 'reason': 'Request not found'}
    
    def check_break_endings(self) -> List[Dict[str, Any]]:
        """Check for breaks that have ended."""
        ended = []
        now = datetime.now(timezone.utc)
        
        to_remove = []
        for agent_id, end_time in self.break_queue.items():
            if now >= end_time:
                ended.append({
                    'agent_id': agent_id,
                    'break_ended': now.isoformat()
                })
                to_remove.append(agent_id)
        
        for agent_id in to_remove:
            del self.break_queue[agent_id]
        
        return ended
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending break requests."""
        return [r for r in self.pending_requests if r['status'] == 'pending']
    
    def get_status(self) -> Dict[str, Any]:
        """Get current break system status."""
        return {
            'agents_on_break': len(self.break_queue),
            'pending_requests': len(self.get_pending_requests()),
            'on_break': list(self.break_queue.keys())
        }


# ========== Phase 10: Dynamic Spawning ==========

class DynamicSpawner:
    """
    Manages dynamic spawning of agents based on workload and resources.
    
    Features:
    - Spawn new agent instances on demand
    - Resource-based spawning decisions
    - Auto-scaling based on task complexity
    - Spawn cooldown to prevent rapid creation
    """
    
    def __init__(self, db: AgentDatabase, config: 'Config'):
        self.db = db
        self.config = config
        self.last_spawn_time: Optional[datetime] = None
        self.spawn_history: List[Dict[str, Any]] = []
    
    def can_spawn(self) -> Tuple[bool, str]:
        """Check if a new agent can be spawned."""
        # Check cooldown
        if self.last_spawn_time:
            elapsed = (datetime.now(timezone.utc) - self.last_spawn_time).total_seconds()
            if elapsed < SPAWN_COOLDOWN_SECONDS:
                remaining = SPAWN_COOLDOWN_SECONDS - elapsed
                return False, f"Spawn cooldown: {remaining:.0f}s remaining"
        
        # Check total agent limit
        active = self.db.get_active_agents()
        sleeping = self.db.get_sleeping_agents()
        total = len(active) + len(sleeping)
        
        if total >= MAX_TOTAL_AGENTS:
            return False, f"Maximum agent limit ({MAX_TOTAL_AGENTS}) reached"
        
        return True, "Spawn allowed"
    
    def spawn_agent(self, model_name: str, provider: str,
                   supervisor_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Spawn a new agent instance.
        
        Args:
            model_name: The model to use for the new agent
            provider: API provider (openai, anthropic, etc.)
            supervisor_id: ID of the supervisor requesting spawn
            reason: Why the agent is being spawned
        
        Returns:
            New agent info or error
        """
        can, msg = self.can_spawn()
        if not can:
            return {'spawned': False, 'reason': msg}
        
        # Generate unique ID and alias
        agent_id = str(uuid.uuid4())
        clean_model = model_name.replace('/', '-').replace('.', '-')
        agent_num = self.db.get_next_agent_number(clean_model)
        alias = f"@{clean_model}{agent_num}"
        
        # Create agent in database
        self.db.save_agent_state(
            agent_id=agent_id,
            alias=alias,
            model_name=model_name,
            memory_dict={'spawned_by': supervisor_id, 'spawn_reason': reason},
            diffs=[],
            error_count=0,
            xp=0,
            level=1,
            supervisor_id=supervisor_id
        )
        
        # Start work tracking
        self.db.start_work_tracking(agent_id)
        
        # Record spawn
        self.last_spawn_time = datetime.now(timezone.utc)
        spawn_record = {
            'agent_id': agent_id,
            'alias': alias,
            'model_name': model_name,
            'provider': provider,
            'spawned_at': self.last_spawn_time.isoformat(),
            'spawned_by': supervisor_id,
            'reason': reason
        }
        self.spawn_history.append(spawn_record)
        
        # Log event
        self.db.log_supervisor_event(supervisor_id, 'spawn_agent', spawn_record)
        
        return {
            'spawned': True,
            'agent_id': agent_id,
            'alias': alias,
            'model_name': model_name,
            'provider': provider
        }
    
    def should_auto_spawn(self, task_complexity: float = 0.5) -> Tuple[bool, str]:
        """
        Determine if auto-spawning is needed based on workload.
        
        Args:
            task_complexity: 0.0-1.0 scale of task complexity
        
        Returns:
            Tuple of (should_spawn, reason)
        """
        active = self.db.get_active_agents()
        
        # Check for recent failed spawn attempts to prevent infinite loops
        recent_failures = sum(1 for s in self.spawn_history[-5:] if not s.get('spawned', True))
        if recent_failures >= 3:
            return False, "Too many recent spawn failures, pausing auto-spawn"
        
        # Ensure minimum active agents
        if len(active) < MIN_ACTIVE_AGENTS:
            return True, f"Below minimum active agents ({len(active)} < {MIN_ACTIVE_AGENTS})"
        
        # High complexity tasks may benefit from more agents
        if task_complexity > 0.7 and len(active) < 5:
            return True, f"High complexity task ({task_complexity:.0%}) may benefit from more agents"
        
        return False, "No auto-spawn needed"
    
    def get_spawn_history(self) -> List[Dict[str, Any]]:
        """Get recent spawn history."""
        return self.spawn_history[-20:]  # Last 20 spawns


class Config:
    """Configuration manager supporting YAML and JSON."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = DEFAULT_CONFIG.copy()
        self.config_path = config_path
        
        if config_path and os.path.exists(config_path):
            self.load(config_path)
        else:
            # Try default locations
            for path in ['axe.yaml', 'axe.yml', 'axe.json', '.axe.yaml', '.axe.json']:
                if os.path.exists(path):
                    self.load(path)
                    break
    
    def load(self, path: str) -> None:
        """Load config from YAML or JSON file."""
        try:
            with open(path, 'r') as f:
                if path.endswith(('.yaml', '.yml')) and HAS_YAML:
                    loaded = yaml.safe_load(f)
                else:
                    loaded = json.load(f)
                
                # Deep merge with defaults
                self._deep_merge(self.config, loaded)
                print(c(f"Loaded config: {path}", Colors.DIM))
        except Exception as e:
            print(c(f"Config load error: {e}", Colors.RED))
    
    def save(self, path: Optional[str] = None) -> None:
        """Save current config to file."""
        path = path or self.config_path or 'axe.yaml'
        try:
            with open(path, 'w') as f:
                if path.endswith(('.yaml', '.yml')) and HAS_YAML:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                else:
                    json.dump(self.config, f, indent=2)
            print(c(f"Config saved: {path}", Colors.GREEN))
        except Exception as e:
            print(c(f"Config save error: {e}", Colors.RED))
    
    def _deep_merge(self, base: dict, update: dict) -> None:
        """Deep merge update into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys, default=None):
        """Get nested config value."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_tool_whitelist(self) -> set:
        """Get flat set of all allowed tools."""
        tools = set()
        for category_tools in self.config.get('tools', {}).values():
            tools.update(category_tools)
        return tools


class AgentManager:
    """Manages agent connections and API calls."""
    
    def __init__(self, config: Config):
        self.config = config
        self.clients = {}
        self._init_clients()
    
    def _uses_max_completion_tokens(self, model: str) -> bool:
        """Check if a model requires max_completion_tokens parameter."""
        # Check if model name or prefix matches models that need max_completion_tokens
        for model_prefix in USE_MAX_COMPLETION_TOKENS:
            if model.startswith(model_prefix):
                return True
        return False
    
    def _init_clients(self) -> None:
        """Initialize API clients for enabled providers."""
        providers = self.config.get('providers', default={})
        
        for name, prov_config in providers.items():
            if not prov_config.get('enabled', True):
                continue
            
            env_key = prov_config.get('env_key', '')
            api_key = os.getenv(env_key)
            
            if not api_key:
                continue
            
            try:
                if name == 'anthropic' and HAS_ANTHROPIC:
                    self.clients[name] = Anthropic(api_key=api_key)
                elif name == 'openai' and HAS_OPENAI:
                    self.clients[name] = OpenAI(api_key=api_key)
                elif name == 'huggingface' and HAS_HUGGINGFACE:
                    self.clients[name] = InferenceClient(token=api_key)
                elif name == 'xai' and HAS_OPENAI:
                    # xAI uses OpenAI-compatible API
                    self.clients[name] = OpenAI(
                        api_key=api_key,
                        base_url=prov_config.get('base_url', 'https://api.x.ai/v1')
                    )
                elif name == 'github' and HAS_OPENAI:
                    # GitHub Copilot uses OpenAI-compatible API
                    self.clients[name] = OpenAI(
                        api_key=api_key,
                        base_url=prov_config.get('base_url', 'https://models.inference.ai.azure.com')
                    )
            except Exception as e:
                print(c(f"Failed to init {name}: {e}", Colors.YELLOW))
    
    def resolve_agent(self, name: str) -> Optional[dict]:
        """Resolve agent name or alias to agent config."""
        agents = self.config.get('agents', default={})
        
        # Direct match
        if name in agents:
            return {**agents[name], 'name': name}
        
        # Alias match
        for agent_name, agent_config in agents.items():
            aliases = agent_config.get('alias', [])
            if name in aliases:
                return {**agent_config, 'name': agent_name}
        
        return None
    
    def list_agents(self) -> List[dict]:
        """List all available agents with status and metadata."""
        result = []
        agents = self.config.get('agents', default={})
        
        for name, agent_config in agents.items():
            provider = agent_config.get('provider', '')
            model = agent_config.get('model', '')
            available = provider in self.clients
            
            # Get model metadata
            model_info = get_model_info(model)
            
            result.append({
                'name': name,
                'aliases': agent_config.get('alias', []),
                'role': agent_config.get('role', ''),
                'provider': provider,
                'model': model,
                'available': available,
                'metadata': model_info
            })
        
        return result
    
    def call_agent(self, agent_name: str, prompt: str, context: str = "") -> str:
        """Call an agent with a prompt."""
        agent = self.resolve_agent(agent_name)
        if not agent:
            return f"Unknown agent: {agent_name}"
        
        provider = agent.get('provider', '')
        if provider not in self.clients:
            return f"Provider '{provider}' not available (missing API key or library)"
        
        client = self.clients[provider]
        model = agent.get('model', '')
        system_prompt = agent.get('system_prompt', '')
        
        full_prompt = f"{prompt}\n\nContext:\n{context}" if context else prompt
        
        try:
            if provider == 'anthropic':
                resp = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{'role': 'user', 'content': full_prompt}]
                )
                return resp.content[0].text
            
            elif provider in ['openai', 'xai', 'github']:
                # Use max_completion_tokens for GPT-5 and newer models
                api_params = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': full_prompt}
                    ]
                }
                if self._uses_max_completion_tokens(model):
                    api_params['max_completion_tokens'] = 4096
                else:
                    api_params['max_tokens'] = 4096
                
                resp = client.chat.completions.create(**api_params)
                return resp.choices[0].message.content
            
            elif provider == 'huggingface':
                resp = client.chat_completion(
                    model=model,
                    max_tokens=4096,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': full_prompt}
                    ]
                )
                return resp.choices[0].message.content
            
        except Exception as e:
            return f"API error ({provider}): {e}"
        
        return "No response"


class ToolRunner:
    """Manages tool execution with safety checks."""
    
    def __init__(self, config: Config, project_dir: str):
        self.config = config
        self.project_dir = os.path.abspath(project_dir)
        self.whitelist = config.get_tool_whitelist()
        self.exec_log = os.path.join(project_dir, 'axe_exec.log')
        self.auto_approve = False
        self.dry_run = False
    
    def is_tool_allowed(self, cmd: str) -> Tuple[bool, str]:
        """Check if a command is allowed."""
        parts = cmd.split()
        if not parts:
            return False, "Empty command"
        
        tool = parts[0]
        if tool not in self.whitelist:
            return False, f"Tool '{tool}' not in whitelist"
        
        # Check for forbidden paths with directory traversal protection
        forbidden = self.config.get('directories', 'forbidden', default=[])
        
        # Resolve forbidden directories to real absolute paths
        resolved_forbidden = []
        for forbidden_path in forbidden:
            expanded_forbidden = os.path.expanduser(forbidden_path)
            if not os.path.isabs(expanded_forbidden):
                expanded_forbidden = os.path.join(self.project_dir, expanded_forbidden)
            resolved_forbidden.append(os.path.realpath(os.path.abspath(expanded_forbidden)))
        
        for part in parts[1:]:
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
        
        return True, "OK"
    
    def run(self, cmd: str, auto_approve: Optional[bool] = None, dry_run: Optional[bool] = None) -> Tuple[bool, str]:
        """Run a command with safety checks."""
        # Use instance defaults if not specified
        if auto_approve is None:
            auto_approve = self.auto_approve
        if dry_run is None:
            dry_run = self.dry_run
        
        allowed, reason = self.is_tool_allowed(cmd)
        
        if not allowed:
            self._log(f"BLOCKED: {cmd} ({reason})")
            return False, reason
        
        if dry_run:
            self._log(f"DRY-RUN: {cmd}")
            return True, f"[DRY-RUN] Would execute: {cmd}"
        
        if not auto_approve:
            print(colorize(f"Execute: {cmd}", Colors.YELLOW))
            response = input("Approve? (y/n): ").strip().lower()
            if response != 'y':
                self._log(f"SKIPPED: {cmd}")
                return False, "Skipped by user"
        
        try:
            os.chdir(self.project_dir)
            # Use shlex.split for safe argument parsing to prevent shell injection
            cmd_args = shlex.split(cmd)
            result = subprocess.run(
                cmd_args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stdout + result.stderr
            self._log(f"EXEC: {cmd}\nOUTPUT: {output[:1000]}")
            
            if result.returncode == 0:
                return True, output
            else:
                return False, f"Exit code {result.returncode}: {output}"
                
        except subprocess.TimeoutExpired:
            self._log(f"TIMEOUT: {cmd}")
            return False, "Command timed out (120s)"
        except Exception as e:
            self._log(f"ERROR: {cmd} - {e}")
            return False, str(e)
    
    def _log(self, message: str) -> None:
        """Log execution to file."""
        try:
            with open(self.exec_log, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            # Report logging errors to stderr instead of failing silently
            try:
                sys.stderr.write(f"AXE ToolRunner log error: {e}\n")
            except Exception:
                pass  # Last resort: ignore all errors in logging


class ResponseProcessor:
    """Processes agent responses and executes code blocks (READ, EXEC, WRITE)."""
    
    def __init__(self, config: Config, project_dir: str, tool_runner: 'ToolRunner'):
        self.config = config
        self.project_dir = os.path.abspath(project_dir)
        self.tool_runner = tool_runner
    
    def process_response(self, response: str, agent_name: str = "") -> str:
        """
        Process agent response and execute any code blocks.
        Returns the response with execution results appended.
        """
        import re
        
        # Pattern to match code blocks: ```TYPE [args]\ncontent\n```
        # Matches READ, EXEC, WRITE blocks
        pattern = r'```(READ|EXEC|WRITE)\s*([^\n]*)\n(.*?)```'
        
        matches = list(re.finditer(pattern, response, re.DOTALL))
        
        if not matches:
            return response
        
        # Process each block
        results = []
        for match in matches:
            block_type = match.group(1)
            args = match.group(2).strip()
            content = match.group(3).rstrip('\n')
            
            if block_type == 'READ':
                result = self._handle_read(args or content)
                results.append(f"\n[READ {args or content}]\n{result}")
            
            elif block_type == 'EXEC':
                command = args or content
                result = self._handle_exec(command)
                results.append(f"\n[EXEC: {command}]\n{result}")
            
            elif block_type == 'WRITE':
                # args contains the filename, content contains the file content
                filename = args
                if not filename:
                    results.append(f"\n[WRITE ERROR: No filename specified]")
                    continue
                result = self._handle_write(filename, content)
                results.append(f"\n[WRITE {filename}]\n{result}")
        
        # Append all results to the original response
        if results:
            return response + "\n\n--- Execution Results ---" + "".join(results)
        
        return response
    
    def _handle_read(self, filename: str) -> str:
        """Handle READ block - read and return file content."""
        filepath = os.path.join(self.project_dir, filename)
        
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
                content = f.read(10000)  # Limit to 10KB
                if len(content) >= 10000:
                    content += "\n[... truncated at 10KB ...]"
                return content
        except Exception as e:
            return f"ERROR reading file: {e}"
    
    def _handle_exec(self, command: str) -> str:
        """Handle EXEC block - execute command via ToolRunner."""
        success, output = self.tool_runner.run(command)
        if success:
            return output if output else "[Command executed successfully]"
        else:
            return f"ERROR: {output}"
    
    def _handle_write(self, filename: str, content: str) -> str:
        """Handle WRITE block - write content to file."""
        filepath = os.path.join(self.project_dir, filename)
        
        # Check if path is allowed for writing
        allowed_dirs = self.config.get('directories', 'allowed', default=[])
        forbidden_dirs = self.config.get('directories', 'forbidden', default=[])
        
        if not self._check_file_access(filepath, allowed_dirs, forbidden_dirs):
            return f"ERROR: Write access denied to {filename}"
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
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
        
        # Check forbidden directories first
        for forbidden_dir in forbidden:
            forbidden_path = os.path.abspath(os.path.expanduser(forbidden_dir))
            if not os.path.isabs(forbidden_path):
                forbidden_path = os.path.join(self.project_dir, forbidden_path)
            forbidden_path = os.path.abspath(forbidden_path)
            
            if filepath.startswith(forbidden_path):
                return False
        
        # Check if in allowed directories
        for allowed_dir in allowed:
            allowed_path = os.path.expanduser(allowed_dir)
            if not os.path.isabs(allowed_path):
                allowed_path = os.path.join(self.project_dir, allowed_path)
            allowed_path = os.path.abspath(allowed_path)
            
            if filepath.startswith(allowed_path):
                return True
        
        # If no specific allowed directory matches, check if it's in project dir
        return filepath.startswith(self.project_dir)


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
    """Shared workspace for multi-agent collaboration."""
    
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
        
        # Initialize shared notes file
        if not os.path.exists(self.shared_file) and self._init_error is None:
            try:
                with open(self.shared_file, 'w') as f:
                    f.write("# Collaborative Session Notes\n\n")
                    f.write("This file is shared between all agents. Use it to:\n")
                    f.write("- Share code snippets\n")
                    f.write("- Leave notes for other agents\n")
                    f.write("- Track progress on tasks\n\n")
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
                 time_limit_minutes: int = 30, db_path: str = "axe_agents.db"):
        self.config = config
        self.agent_mgr = AgentManager(config)
        self.workspace = SharedWorkspace(workspace_dir)
        self.project_ctx = ProjectContext(workspace_dir, config)
        self.tool_runner = ToolRunner(config, workspace_dir)
        self.response_processor = ResponseProcessor(config, workspace_dir, self.tool_runner)
        self.db = AgentDatabase(db_path)
        
        # Initialize Phase 6-10 systems
        self.sleep_manager = SleepManager(self.db)
        self.break_system = BreakSystem(self.db)
        self.emergency_mailbox = EmergencyMailbox()
        self.spawner = DynamicSpawner(self.db, config)
        
        # Validate and set up agents with unique IDs and aliases
        self.agents = []
        self.agent_ids = {}  # Maps agent name to unique ID
        self.agent_aliases = {}  # Maps agent name to @alias
        
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
        agent_config = self.agent_mgr.resolve_agent(agent_name)
        
        level_info = ""
        if state:
            level = state['level']
            xp = state['xp']
            title = get_title_for_level(level)
            level_info = f"\nYour Level: {level} ({xp} XP) - {title}"
        
        # Get context window and capabilities info
        context_window = agent_config.get('context_window', 'unknown') if agent_config else 'unknown'
        capabilities = agent_config.get('capabilities', []) if agent_config else []
        capabilities_str = ', '.join(capabilities) if capabilities else 'text'
        model_info = f"\nYour Model: {agent_config.get('model', 'unknown')} | Context Window: {context_window:,} tokens | Capabilities: {capabilities_str}" if agent_config else ""
        
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
            a_config = self.agent_mgr.resolve_agent(a)
            if a_config:
                a_ctx = a_config.get('context_window', '?')
                a_caps = ', '.join(a_config.get('capabilities', ['text']))
                other_info_list.append(f"{a_alias} ({a_ctx:,} ctx, {a_caps})")
            else:
                other_info_list.append(a_alias)
        
        is_supervisor = (alias == "@boss")
        supervisor_note = "\n⚠️ You are the SUPERVISOR (@boss). You coordinate and oversee the team." if is_supervisor else ""
        
        return f"""You are {alias} (real name: {agent_name}), participating in a COLLABORATIVE CODING SESSION.{level_info}{model_info}{supervisor_note}

Other agents in this session: {', '.join(other_info_list)}

COLLABORATION RULES (READ CAREFULLY):
1. You are working TOGETHER on a shared task. Be cooperative, not competitive.
2. You can see the full conversation history - reference what others said.
3. Build on each other's work. If another agent wrote code, improve it or review it.
4. Be concise and focus on the most important details in each turn.
5. Use the SHARED WORKSPACE at: {self.workspace.workspace_dir}
6. If you modify files, explain what you changed and why.
7. Address other agents by their aliases: "Hey {other_aliases[0] if other_aliases else '@agent'}, I noticed..."
8. If you're done with your part, say "PASS" to give others a turn.
9. When the task is complete, any agent can say "TASK COMPLETE" with a summary.
10. Earn XP by completing tasks well. Level up to unlock new titles and privileges!
11. When introducing yourself, share your context window size and capabilities.

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
            
            # Get context window and capabilities
            ctx_window = agent_config.get('context_window', 0) if agent_config else 0
            capabilities = agent_config.get('capabilities', ['text']) if agent_config else ['text']
            cap_str = '/'.join(capabilities[:2]) if len(capabilities) > 2 else '/'.join(capabilities)
            
            if state:
                level = state['level']
                xp = state['xp']
                title = get_title_for_level(level)
                role_indicator = " [SUPERVISOR]" if alias == "@boss" else ""
                
                print(c(f"  {alias:20} Level {level:2} ({xp:6} XP)  {title}{role_indicator}", Colors.GREEN))
                print(c(f"                       Context: {ctx_window:,} tokens | Capabilities: {cap_str}", Colors.DIM))
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
                
                # Add Phase 6-10 specific instructions
                phase_instructions = """
ADVANCED COMMANDS (Phase 6-10):
- Say "BREAK REQUEST: [reason]" to request a coffee/play break
- Say "EMERGENCY: [message]" to send encrypted report to human
- Say "SPAWN: [model_type]" to request spawning a new agent (supervisor only)
- Say "STATUS" to check sleep/break status of all agents
"""
                
                prompt = f"""Current task: {self.task_description}

Time remaining: {self._format_time(self._time_remaining())}

{conversation}

Shared Notes Summary (last {COLLAB_SHARED_NOTES_LIMIT} chars):
{shared_notes[-COLLAB_SHARED_NOTES_LIMIT:] if len(shared_notes) > COLLAB_SHARED_NOTES_LIMIT else shared_notes}

{workspace_context}
{phase_instructions}

It's YOUR TURN. What would you like to contribute? Remember:
- Be concise and actionable
- Reference other agents' work
- Say "PASS" if you have nothing to add right now
- Say "TASK COMPLETE: [summary]" if the task is done
"""
                
                # Get agent's system prompt for collaboration
                system_prompt = self._get_system_prompt_for_collab(current_agent)
                
                # Call the agent
                print(c(f"[{current_agent}] Thinking...", Colors.DIM))
                
                agent_config = self.agent_mgr.resolve_agent(current_agent)
                provider = agent_config.get('provider', '')
                client = self.agent_mgr.clients.get(provider)
                model = agent_config.get('model', '')
                
                response = ""
                try:
                    if provider == 'anthropic':
                        resp = client.messages.create(
                            model=model,
                            max_tokens=2048,
                            system=system_prompt,
                            messages=[{'role': 'user', 'content': prompt}]
                        )
                        # Check for None content
                        if resp.content and len(resp.content) > 0 and resp.content[0].text:
                            response = resp.content[0].text
                        else:
                            response = "[No response from model]"
                    elif provider in ['openai', 'xai', 'github']:
                        # Use max_completion_tokens for GPT-5 and newer models
                        api_params = {
                            'model': model,
                            'messages': [
                                {'role': 'system', 'content': system_prompt},
                                {'role': 'user', 'content': prompt}
                            ]
                        }
                        if self.agent_mgr._uses_max_completion_tokens(model):
                            api_params['max_completion_tokens'] = 2048
                        else:
                            api_params['max_tokens'] = 2048
                        
                        resp = client.chat.completions.create(**api_params)
                        # Check for None content
                        if resp.choices and len(resp.choices) > 0 and resp.choices[0].message.content:
                            response = resp.choices[0].message.content
                        else:
                            response = "[No response from model]"
                    elif provider == 'huggingface':
                        resp = client.chat_completion(
                            model=model,
                            max_tokens=2048,
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
                response_upper = processed_response.upper() if processed_response else ""
                
                # Phase 9: Break request
                if 'BREAK REQUEST:' in response_upper:
                    self._handle_break_request(current_agent, response)
                
                # Phase 8: Emergency message
                if 'EMERGENCY:' in response_upper:
                    self._handle_emergency_message(current_agent, response)
                
                # Phase 10: Spawn request (supervisor only)
                if 'SPAWN:' in response_upper and alias == self.supervisor_alias:
                    self._handle_spawn_request(current_agent, response)
                
                # Status check
                if 'STATUS' in response_upper:
                    self._print_status()
                
                # Award XP for meaningful contribution (not for PASS)
                non_empty_lines = [line.strip().upper() for line in processed_response.splitlines() if line.strip()]
                is_pass = bool(non_empty_lines) and non_empty_lines[0] == 'PASS'
                
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
                
                # Check for special responses
                if 'TASK COMPLETE' in response_upper:
                    print(c("\n✅ TASK MARKED COMPLETE!", Colors.GREEN + Colors.BOLD))
                    
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
    
    def _handle_break_request(self, agent_name: str, response: str) -> None:
        """Handle a break request from an agent."""
        alias = self.agent_aliases.get(agent_name, agent_name)
        agent_id = self.agent_ids.get(agent_name)
        
        # Extract reason from response
        try:
            reason_start = response.upper().index('BREAK REQUEST:') + 14
            reason = response[reason_start:].split('\n')[0].strip()
        except (ValueError, IndexError):
            reason = "Unspecified"
        
        print(c(f"\n☕ {alias} requests a break: {reason}", Colors.CYAN))
        
        # Submit break request
        request = self.break_system.request_break(
            agent_id, alias, 'coffee', reason
        )
        
        # Auto-approve if supervisor or if conditions are met
        if alias == self.supervisor_alias:
            result = self.break_system.approve_break(request['id'])
            if result['approved']:
                print(c(f"   Break approved ({result['duration_minutes']} min)", Colors.GREEN))
            else:
                print(c(f"   Break denied: {result['reason']}", Colors.YELLOW))
        else:
            print(c(f"   Request pending supervisor approval (ID: {request['id'][:8]})", Colors.DIM))
    
    def _handle_emergency_message(self, agent_name: str, response: str) -> None:
        """Handle an emergency message from an agent."""
        alias = self.agent_aliases.get(agent_name, agent_name)
        
        # Extract message from response
        try:
            msg_start = response.upper().index('EMERGENCY:') + 10
            emergency_msg = response[msg_start:].split('\n')[0].strip()
        except (ValueError, IndexError):
            emergency_msg = response
        
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
    
    def _handle_spawn_request(self, agent_name: str, response: str) -> None:
        """Handle a spawn request from the supervisor."""
        # Extract model type from response
        try:
            spawn_start = response.upper().index('SPAWN:') + 6
            model_type = response[spawn_start:].split('\n')[0].strip().lower()
        except (ValueError, IndexError):
            model_type = 'llama'  # Default
        
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
            # Add to session using unique agent_id as key to prevent conflicts
            unique_key = result['agent_id']
            self.agents.append(unique_key)
            self.agent_ids[unique_key] = result['agent_id']
            self.agent_aliases[unique_key] = result['alias']
        else:
            print(c(f"   ✗ Spawn failed: {result['reason']}", Colors.YELLOW))
    
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
                f.write(f"# Collaborative Session Log\n\n")
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
    
    def __init__(self, config: Config, project_dir: str):
        self.config = config
        self.project_dir = os.path.abspath(project_dir)
        self.agent_mgr = AgentManager(config)
        self.tool_runner = ToolRunner(config, project_dir)
        self.project_ctx = ProjectContext(project_dir, config)
        self.response_processor = ResponseProcessor(config, project_dir, self.tool_runner)
        self.history: List[dict] = []
        self.default_agent = 'claude'
    
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
        help_text = """
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
  /help             Show this help
  /quit             Exit

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
  /collab llama,copilot ./playground 30 "Analyze and document wadextract.c"
        """
        print(c(help_text, Colors.CYAN))
    
    def list_agents(self) -> None:
        """List available agents with enhanced metadata."""
        print(c("\nAvailable Agents:", Colors.BOLD))
        print("-" * 60)
        
        for agent in self.agent_mgr.list_agents():
            status = c("✓", Colors.GREEN) if agent['available'] else c("✗", Colors.RED)
            aliases = ', '.join(agent['aliases'])
            print(f"  {status} {c(agent['name'], Colors.CYAN):12} ({aliases})")
            print(f"     {c(agent['role'], Colors.DIM)}")
            print(f"     Model: {agent['model']}")
            
            # Display metadata if available
            if 'metadata' in agent:
                metadata = agent['metadata']
                context_tokens = format_token_count(metadata['context_tokens'])
                max_output = format_token_count(metadata['max_output_tokens'])
                input_modes = ', '.join(metadata['input_modes'])
                output_modes = ', '.join(metadata['output_modes'])
                
                print(f"     Context: {context_tokens} tokens | Max Output: {max_output} tokens")
                print(f"     Input: {input_modes} | Output: {output_modes}")
        print()
    
    def list_tools(self) -> None:
        """List available tools by category."""
        print(c("\nAvailable Tools:", Colors.BOLD))
        print("-" * 40)
        
        tools = self.config.get('tools', default={})
        for category, tool_list in tools.items():
            print(f"  {c(category, Colors.CYAN)}: {', '.join(tool_list)}")
        print()
    
    def list_dirs(self) -> None:
        """Show directory permissions."""
        print(c("\nDirectory Access:", Colors.BOLD))
        print("-" * 40)
        
        dirs = self.config.get('directories', default={})
        
        allowed = dirs.get('allowed', [])
        print(f"  {c('Allowed:', Colors.GREEN)} {', '.join(allowed)}")
        
        readonly = dirs.get('readonly', [])
        print(f"  {c('Read-only:', Colors.YELLOW)} {', '.join(readonly)}")
        
        forbidden = dirs.get('forbidden', [])
        print(f"  {c('Forbidden:', Colors.RED)} {', '.join(forbidden)}")
        print()
    
    def process_command(self, cmd: str) -> bool:
        """Process a slash command. Returns False to exit."""
        cmd = cmd.strip()
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
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
            files, total = self.project_ctx.list_code_files()
            header = f"\nCode files ({len(files)}"
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
                success, output = self.tool_runner.run(args)
                color = Colors.GREEN if success else Colors.RED
                print(c(output[:1000], color))
            else:
                print(c("Usage: /exec <command>", Colors.YELLOW))
        
        elif command == '/history':
            total_entries = len(self.history)
            entries_to_show = self.history[-20:]
            for entry in entries_to_show:
                role = c(entry['role'], Colors.CYAN)
                msg = entry['content'][:100]
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
            parts = args.split(maxsplit=3)
            if len(parts) < 4:
                print(c("Usage: /collab <agents> <workspace> <time_minutes> <task>", Colors.YELLOW))
                print(c("  agents: comma-separated list (e.g., llama,copilot)", Colors.DIM))
                print(c("  workspace: directory path (e.g., ./playground)", Colors.DIM))
                print(c("  time_minutes: session time limit (e.g., 30)", Colors.DIM))
                print(c("  task: description in quotes (e.g., \"Review the code\")", Colors.DIM))
                return True
            
            agents_str, workspace, time_str, task = parts
            agents = [a.strip() for a in agents_str.split(',')]
            
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
                collab = CollaborativeSession(
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
        
        else:
            print(c(f"Unknown command: {command}. Type /help for help.", Colors.YELLOW))
        
        return True
    
    def process_agent_message(self, message: str) -> None:
        """Process an @agent message."""
        # Parse @agent from message
        if not message.startswith('@'):
            agent_name = self.default_agent
            prompt = message
        else:
            parts = message[1:].split(maxsplit=1)
            agent_name = parts[0]
            prompt = parts[1] if len(parts) > 1 else ""
        
        if not prompt:
            print(c("Please provide a task for the agent", Colors.YELLOW))
            return
        
        # Get context
        context = self.project_ctx.get_context_summary()
        
        # Record in history
        self.history.append({'role': 'user', 'agent': agent_name, 'content': prompt})
        
        # Call agent
        print(c(f"\n[{agent_name}] Processing...", Colors.DIM))
        response = self.agent_mgr.call_agent(agent_name, prompt, context)
        
        # Process response for code blocks (READ, EXEC, WRITE)
        processed_response = self.response_processor.process_response(response, agent_name)
        
        # Record response
        self.history.append({'role': agent_name, 'content': processed_response})
        
        # Print response
        print(c(f"\n[{agent_name}]:", Colors.CYAN + Colors.BOLD))
        print(processed_response)
        print()
    
    def run(self) -> None:
        """Run interactive chat session."""
        self.print_banner()
        
        try:
            while True:
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


def restore_agents_on_startup(db_path: str = "axe_agents.db") -> None:
    """
    Display agents from database on startup (informational only).
    
    Note: This function displays agent information from previous sessions
    but does not automatically recreate them in the current session.
    Agents must be explicitly spawned via collaborative sessions or
    other mechanisms. This is informational to show what agents
    existed in previous sessions.
    
    Args:
        db_path: Path to SQLite database
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


def main():
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
    parser.add_argument('--auto-approve', action='store_true',
                        help='Auto-approve tool executions')
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
        
        try:
            collab = CollaborativeSession(
                config=config,
                agents=agents,
                workspace_dir=workspace,
                time_limit_minutes=args.time
            )
            collab.start_session(args.task)
        except ValueError as e:
            print(c(f"Cannot start collaboration: {e}", Colors.RED))
        except Exception as e:
            print(c(f"Collaboration error: {e}", Colors.RED))
        return
    
    # Create session
    session = ChatSession(config, args.dir)
    
    # Update tool runner settings
    session.tool_runner.auto_approve = args.auto_approve
    session.tool_runner.dry_run = args.dry_run
    
    # Single command mode
    if args.command:
        session.process_agent_message(args.command)
        return
    
    # Interactive mode
    session.run()


if __name__ == '__main__':
    main()
