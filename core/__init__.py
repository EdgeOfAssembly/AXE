"""
Core module for AXE - multiprocessing, configuration, and coordination.
"""

from .multiprocess import AgentWorkerProcess, MultiAgentCoordinator, SharedContext
from .config import Config
from .agent_manager import AgentManager
from .tool_runner import ToolRunner
from .sandbox import SandboxManager
from .resource_monitor import start_resource_monitor, collect_resources
from .constants import (
    DEFAULT_CONFIG,
    CHARS_PER_TOKEN,
    COLLAB_HISTORY_LIMIT,
    COLLAB_CONTENT_LIMIT,
    COLLAB_PASS_MULTIPLIER,
    COLLAB_SHARED_NOTES_LIMIT,
    RESOURCE_UPDATE_INTERVAL,
    RESOURCE_FILE,
    MAX_WORK_HOURS,
    MIN_SLEEP_MINUTES,
    WORK_TIME_WARNING_HOURS,
    SLEEP_REASON_TIMEOUT,
    SLEEP_REASON_DEGRADATION,
    SLEEP_REASON_MANUAL,
    SLEEP_REASON_BREAK,
    ERROR_THRESHOLD_PERCENT,
    DIFF_HISTORY_LIMIT,
    DEGRADATION_CHECK_INTERVAL,
    EMERGENCY_MAILBOX_DIR,
    GPG_PUBLIC_KEY_FILE,
    MAX_BREAK_MINUTES,
    MAX_BREAKS_PER_HOUR,
    MIN_WORKLOAD_FOR_BREAK,
    MAX_WORKFORCE_ON_BREAK,
    MIN_ACTIVE_AGENTS,
    MAX_TOTAL_AGENTS,
    SPAWN_COOLDOWN_SECONDS,
    AGENT_TOKEN_PASS,
    AGENT_TOKEN_TASK_COMPLETE,
    AGENT_TOKEN_BREAK_REQUEST,
    AGENT_TOKEN_EMERGENCY,
    AGENT_TOKEN_SPAWN,
    AGENT_TOKEN_STATUS,
    READ_BLOCK_PATTERN,
)

__all__ = [
    # Multiprocessing
    'AgentWorkerProcess',
    'MultiAgentCoordinator',
    'SharedContext',
    # Config
    'Config',
    # Agent Management
    'AgentManager',
    # Tool Runner
    'ToolRunner',
    # Sandbox
    'SandboxManager',
    # Resource Monitor
    'start_resource_monitor',
    'collect_resources',
    # Constants
    'DEFAULT_CONFIG',
    'CHARS_PER_TOKEN',
    'COLLAB_HISTORY_LIMIT',
    'COLLAB_CONTENT_LIMIT',
    'COLLAB_PASS_MULTIPLIER',
    'COLLAB_SHARED_NOTES_LIMIT',
    'RESOURCE_UPDATE_INTERVAL',
    'RESOURCE_FILE',
    'MAX_WORK_HOURS',
    'MIN_SLEEP_MINUTES',
    'WORK_TIME_WARNING_HOURS',
    'SLEEP_REASON_TIMEOUT',
    'SLEEP_REASON_DEGRADATION',
    'SLEEP_REASON_MANUAL',
    'SLEEP_REASON_BREAK',
    'ERROR_THRESHOLD_PERCENT',
    'DIFF_HISTORY_LIMIT',
    'DEGRADATION_CHECK_INTERVAL',
    'EMERGENCY_MAILBOX_DIR',
    'GPG_PUBLIC_KEY_FILE',
    'MAX_BREAK_MINUTES',
    'MAX_BREAKS_PER_HOUR',
    'MIN_WORKLOAD_FOR_BREAK',
    'MAX_WORKFORCE_ON_BREAK',
    'MIN_ACTIVE_AGENTS',
    'MAX_TOTAL_AGENTS',
    'SPAWN_COOLDOWN_SECONDS',
    'AGENT_TOKEN_PASS',
    'AGENT_TOKEN_TASK_COMPLETE',
    'AGENT_TOKEN_BREAK_REQUEST',
    'AGENT_TOKEN_EMERGENCY',
    'AGENT_TOKEN_SPAWN',
    'AGENT_TOKEN_STATUS',
    'READ_BLOCK_PATTERN',
]
