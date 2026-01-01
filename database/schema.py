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
