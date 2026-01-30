"""
AXE Constants Module

Central location for all configuration constants used throughout AXE.
"""

# Token optimization constants
CHARS_PER_TOKEN = 4  # Rough approximation for token estimation (chars / 4 ≈ tokens)

# Collaborative session constants
# Limits increased for bigger shared view between agents
COLLAB_HISTORY_LIMIT = 200      # Max messages to show in conversation history (increased from 50)
COLLAB_CONTENT_LIMIT = 100000   # Max chars per message in history (increased from 50000)
COLLAB_PASS_MULTIPLIER = 2      # Times agents can pass before session ends
COLLAB_SHARED_NOTES_LIMIT = 100000  # Max chars of shared notes to show (increased from 10000)

# Global Workspace constants (Baars' Global Workspace Theory)
GLOBAL_WORKSPACE_FILE = "GLOBAL_WORKSPACE.json"
GLOBAL_WORKSPACE_MAX_BROADCASTS = 200
GLOBAL_WORKSPACE_PROMPT_ENTRIES = 10

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

# Agent Communication: Unique Token System
# These tokens are extremely unlikely to appear in normal text/files/command output
AGENT_TOKEN_PASS = "[[AGENT_PASS_TURN]]"
AGENT_TOKEN_TASK_COMPLETE = "[[AGENT_TASK_COMPLETE:"  # Followed by summary, ends with ]]
AGENT_TOKEN_BREAK_REQUEST = "[[AGENT_BREAK_REQUEST:"  # Followed by type, reason, ends with ]]
AGENT_TOKEN_EMERGENCY = "[[AGENT_EMERGENCY:"  # Followed by message, ends with ]]
AGENT_TOKEN_SPAWN = "[[AGENT_SPAWN:"  # Followed by model, role, ends with ]]
AGENT_TOKEN_STATUS = "[[AGENT_STATUS]]"
AGENT_TOKEN_GITHUB_READY = "[[GITHUB_READY:"  # Agent signals ready to push to GitHub
AGENT_TOKEN_BROADCAST = "[[BROADCAST:"  # Format: [[BROADCAST:CATEGORY:message]]
AGENT_TOKEN_SUPPRESS = "[[SUPPRESS:"  # Format: [[SUPPRESS:@target:reason]]
AGENT_TOKEN_RELEASE = "[[RELEASE:"    # Format: [[RELEASE:@target]]
AGENT_TOKEN_XP_VOTE = "[[XP_VOTE:"    # Format: [[XP_VOTE:@target:±XP:reason]]
AGENT_TOKEN_CONFLICT = "[[CONFLICT:"    # Format: [[CONFLICT:broadcast_id1,broadcast_id2:reason]]
AGENT_TOKEN_ARBITRATE = "[[ARBITRATE:"  # Format: [[ARBITRATE:arb_id:resolution:winner_id]]

# Subsumption Architecture constants (Brooks 1986)
SUPPRESSION_DEFAULT_TURNS = 3
SUPPRESSION_MAX_TURNS = 10

# Arbitration constants (Minsky's conflict resolution)
ARBITRATION_DEADLINE_TURNS = 5      # Turns before escalation
ARBITRATION_AUTO_ESCALATE = True    # Auto-escalate on deadline
ARBITRATION_MIN_LEVEL_BUMP = 10     # Level increase on escalation

# Contradiction keywords for detection
CONTRADICTION_PAIRS = [
    ('safe', 'unsafe'), ('secure', 'vulnerable'), ('secure', 'insecure'),
    ('correct', 'incorrect'), ('valid', 'invalid'),
    ('approve', 'reject'), ('yes', 'no'),
    ('no issues', 'found issues'), ('clean', 'buggy'),
    ('recommended', 'not recommended'), ('should', 'should not'),
]

# Regex pattern for removing [READ filename] blocks while avoiding [[ token false positives
# Matches: [READ ...] (case-insensitive) followed by content until:
#   - \n\n (double newline) OR
#   - \n\[(?!\[)[A-Z] (newline + [ + not another [ + any letter, indicating [COMMAND]) OR
#   - \Z (end of string)
# Note: Used with re.IGNORECASE flag, so [A-Z] matches both uppercase and lowercase letters
READ_BLOCK_PATTERN = r'\[READ[^\]]*\].*?(?=\n\n|\n\[(?!\[)[A-Z]|\Z)'

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
            'context_tokens': 128000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are an expert software engineer. Provide clear, working code.
For C/C++: Prefer portable code; when DOS/16-bit targets are requested, explain that true DOS support typically needs compilers like Open Watcom or DJGPP and that 16-bit ints/far pointers are non-standard in modern toolchains.
For Python: Clean, type-hinted code.
For reverse-engineering: Use hexdump/objdump analysis. Workshop tools available: /workshop chisel for symbolic execution, /workshop saw for taint analysis, /workshop plane for source/sink enumeration."""
        },
        'claude': {
            'alias': ['c', 'anthropic'],
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022',
            'role': 'Code reviewer and security auditor',
            'context_tokens': 200000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are a code review expert and security auditor.
Analyze code for bugs, security issues, and improvements.
For rev-eng: Check endianness, memory safety, DOS compatibility.
For security analysis: Use Workshop tools: /workshop saw for taint analysis to find injection vulnerabilities, /workshop plane to enumerate attack surface, /workshop chisel for binary vulnerability analysis."""
        },
        'llama': {
            'alias': ['l', 'hf'],
            'provider': 'huggingface',
            'model': 'meta-llama/Llama-3.1-70B-Instruct',
            'role': 'Open-source hacker and asm expert',
            'context_tokens': 128000,
            'capabilities': ['text'],
            'system_prompt': """You are an open-source hacker fluent in x86 assembly.
Specialize in nasm, DOS interrupts, binary analysis.
Use hexdump, objdump, ndisasm for reverse engineering.
Workshop tools available: /workshop chisel for symbolic execution of binaries, /workshop hammer for live process instrumentation."""
        },
        'grok': {
            'alias': ['x', 'xai'],
            'provider': 'xai',
            'model': 'grok-beta',
            'role': 'Creative problem solver',
            'context_tokens': 128000,
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
            'context_tokens': 128000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'system_prompt': """You are a GitHub Copilot-style assistant.
Help with code completion, documentation, and testing.
Focus on practical, working solutions."""
        }
    },

    # Tool access control (blacklist model)
    # When sandbox is enabled: All tools allowed except those in blacklist
    # When sandbox is disabled: All tools allowed except those in blacklist (full host access)
    'tools': {
        'blacklist': []  # Tools explicitly forbidden (empty = all tools allowed)
    },

    # Directory access control (blacklist model)
    # When sandbox is enabled: Full access inside sandbox except blacklist
    # When sandbox is disabled: Full host access within user permissions except blacklist
    'directories': {
        'blacklist': []  # Directories explicitly forbidden (empty = full access within sandbox/host)
    },

    # Sandbox configuration (bubblewrap isolation)
    'sandbox': {
        'enabled': False,  # Opt-in for backward compatibility
        'runtime': 'bubblewrap',
        
        # Workspace configuration
        'workspaces': [
            {'path': '.', 'writable': True}
        ],
        
        # Host directories to expose
        'host_binds': {
            'readonly': ['/usr', '/lib', '/lib64', '/bin', '/etc', '/run', '/sys'],
            'writable': [],
            'none': ['~/.ssh', '~/.gnupg', '/root']
        },
        
        # Optional tool blacklist (empty = all allowed inside sandbox)
        'tool_blacklist': [],
        
        # Namespace options
        'namespaces': {
            'user': True,
            'mount': True,
            'pid': True,
            'uts': True,
            'network': False,  # Set true for network isolation
            'ipc': True,
            'cgroup': True
        },
        
        # Additional options
        'options': {
            'new_session': True,  # Block TTY attacks
            'die_with_parent': True,  # Kill sandbox if parent dies
            'proc': '/proc',  # Mount fresh /proc
            'dev': '/dev',   # Full /dev (includes /dev/fuse for FUSE mounts)
            'tmpfs': '/tmp'  # Writable tmp inside sandbox
        }
    },

    # File extensions for code detection
    'code_extensions': ['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx',
                        '.py', '.pyx', '.pyi',
                        '.asm', '.s', '.inc',
                        '.exe', '.com', '.wad', '.bin']
}

# Level-to-Privilege constants (Simon's hierarchies)
PRIVILEGE_PROMPT_SECTION = True  # Include privileges in prompts
# Note: Command validation is available via validate_command() but not yet
# enforced in the collaboration loop. Future work will add runtime enforcement.
