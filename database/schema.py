"""
SQLite database schema definitions for AXE agent system.
"""

AGENT_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS agent_state (
    agent_id TEXT PRIMARY KEY,
    alias TEXT UNIQUE,
    model_name TEXT,
    supervisor_id TEXT,
    last_updated TIMESTAMP,
    memory_json TEXT,
    recent_diffs TEXT,
    error_count INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    work_start_time TIMESTAMP,
    total_work_minutes INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    context_summary TEXT
)
"""

# Migration statements for updating existing agent_state tables
AGENT_STATE_MIGRATIONS = [
    "ALTER TABLE agent_state ADD COLUMN tokens_used INTEGER DEFAULT 0",
    "ALTER TABLE agent_state ADD COLUMN context_summary TEXT",
]

SUPERVISOR_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS supervisor_log (
    log_id TEXT PRIMARY KEY,
    supervisor_id TEXT,
    timestamp TIMESTAMP,
    event_type TEXT,
    details TEXT
)
"""

ALIAS_MAPPINGS_TABLE = """
CREATE TABLE IF NOT EXISTS alias_mappings (
    session_alias TEXT PRIMARY KEY,
    external_identity TEXT,
    channel_type TEXT,
    channel_id TEXT,
    created_at TIMESTAMP
)
"""

# WAL mode pragma for better concurrency
WAL_MODE_PRAGMA = "PRAGMA journal_mode=WAL"

WORKSHOP_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS workshop_analysis (
    analysis_id TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,  -- 'chisel', 'saw', 'plane', 'hammer'
    target TEXT NOT NULL,     -- file path, code snippet, process name, etc.
    agent_id TEXT,            -- agent that requested the analysis
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    results_json TEXT,        -- JSON results from the analysis
    status TEXT DEFAULT 'completed',  -- 'completed', 'failed', 'running'
    duration_seconds REAL,    -- analysis duration
    error_message TEXT        -- error details if failed
)
"""

WORKSHOP_ANALYSIS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_workshop_tool ON workshop_analysis(tool_name)",
    "CREATE INDEX IF NOT EXISTS idx_workshop_agent ON workshop_analysis(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_workshop_timestamp ON workshop_analysis(timestamp)",
]

# Global Workspace: Broadcast tracking (Baars' Global Workspace Theory)
BROADCAST_TABLE = """
CREATE TABLE IF NOT EXISTS broadcasts (
    broadcast_id TEXT PRIMARY KEY,
    agent_alias TEXT NOT NULL,
    agent_level INTEGER NOT NULL,
    category TEXT NOT NULL,        -- 'SECURITY', 'CODE_QUALITY', 'CONFLICT', etc.
    content TEXT NOT NULL,
    metadata_json TEXT,             -- JSON metadata (files, functions, etc.)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

BROADCAST_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_broadcast_agent ON broadcasts(agent_alias)",
    "CREATE INDEX IF NOT EXISTS idx_broadcast_category ON broadcasts(category)",
    "CREATE INDEX IF NOT EXISTS idx_broadcast_timestamp ON broadcasts(timestamp)",
]

# Arbitration Protocol: Conflict resolution (Minsky's cross-exclusion)
ARBITRATION_TABLE = """
CREATE TABLE IF NOT EXISTS arbitrations (
    arbitration_id TEXT PRIMARY KEY,
    conflict_broadcasts_json TEXT NOT NULL,  -- JSON array of conflicting broadcast IDs
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_turn INTEGER DEFAULT 0,
    deadline_turn INTEGER NOT NULL,
    required_level INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',           -- 'pending', 'resolved', 'escalated'
    escalation_count INTEGER DEFAULT 0,
    resolution_json TEXT,                    -- JSON resolution details when resolved
    resolved_at TIMESTAMP,
    resolved_turn INTEGER
)
"""

ARBITRATION_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_arbitration_status ON arbitrations(status)",
    "CREATE INDEX IF NOT EXISTS idx_arbitration_level ON arbitrations(required_level)",
    "CREATE INDEX IF NOT EXISTS idx_arbitration_deadline ON arbitrations(deadline_turn)",
]

# Conflict tracking
CONFLICT_TABLE = """
CREATE TABLE IF NOT EXISTS conflicts (
    conflict_id TEXT PRIMARY KEY,
    conflict_type TEXT NOT NULL,             -- 'detected', 'manual', 'explicit'
    broadcast_ids_json TEXT NOT NULL,        -- JSON array of conflicting broadcast IDs
    flagged_by TEXT,
    reason TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending_arbitration',  -- 'pending_arbitration', 'resolved', 'dismissed'
    arbitration_id TEXT                      -- Link to arbitration if created
)
"""

CONFLICT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_conflict_status ON conflicts(status)",
    "CREATE INDEX IF NOT EXISTS idx_conflict_type ON conflicts(conflict_type)",
    "CREATE INDEX IF NOT EXISTS idx_conflict_arbitration ON conflicts(arbitration_id)",
]
