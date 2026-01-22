# Global Workspace - Implementation Guide

## Overview

The Global Workspace is an implementation of **Bernard Baars' Global Workspace Theory (1988)** for AXE's collaborative agent sessions. It provides a broadcast mechanism where agents can:
- Post important findings for all agents to see
- Subscribe to specific categories of broadcasts
- Acknowledge critical broadcasts
- Search and filter broadcast history

## Theory Background

Global Workspace Theory proposes that consciousness/coordination emerges from a "global broadcast" mechanism where:
- Specialized modules compete to post information to a shared workspace
- Posted information becomes available to ALL other modules
- This solves the integration problem without a central controller

**Reference**: Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.

## Quick Start

```python
from core.global_workspace import GlobalWorkspace

# Initialize workspace for a collaborative session
workspace = GlobalWorkspace("/path/to/session/dir")

# Broadcast a finding
result = workspace.broadcast(
    agent_alias="@gpt1",
    agent_level=10,
    category="SECURITY",
    message="Buffer overflow vulnerability in parse_header()",
    related_file="src/parser.c",
    tags=["buffer-overflow", "high-priority"]
)

# Get recent broadcasts
recent = workspace.get_broadcasts(limit=10)

# Get pending acknowledgments for an agent
pending = workspace.get_pending_acks("@claude1")

# Acknowledge a broadcast
workspace.acknowledge(
    broadcast_id=result['broadcast_id'],
    agent_alias="@claude1",
    comment="Reviewing this issue now"
)
```

## Broadcast Categories

The workspace supports 8 broadcast categories aligned with AXE's focus areas:

| Category | Purpose | Permission |
|----------|---------|------------|
| `SECURITY` | Security findings (vulnerabilities, risks) | All agents |
| `BUG` | Bug discoveries | All agents |
| `OPTIMIZATION` | Performance/code improvements | All agents |
| `CONFLICT` | Conflicting findings requiring resolution | All agents |
| `DIRECTIVE` | High-level directives | **Team Leader+ (Level 20+)** |
| `STATUS` | Status updates | All agents |
| `XP_VOTE` | Peer XP voting | All agents |
| `FINDING` | General findings | All agents |

## API Reference

### `GlobalWorkspace(session_dir: str)`

Initialize a global workspace for a collaborative session.

**Parameters:**
- `session_dir`: Directory where workspace data will be stored

### `broadcast(agent_alias, agent_level, category, message, ...)`

Post a broadcast to the global workspace.

**Parameters:**
- `agent_alias` (str): Broadcasting agent's alias (e.g., "@llama1")
- `agent_level` (int): Agent's current level (1-40+)
- `category` (str): Broadcast category (from CATEGORIES)
- `message` (str): The broadcast message
- `requires_ack` (bool, optional): Whether other agents must acknowledge
- `related_file` (str, optional): File path related to this broadcast
- `tags` (list, optional): Tags for filtering

**Returns:**
- `Dict` with `success`, `broadcast_id`, and `entry` keys

**Example:**
```python
result = workspace.broadcast(
    agent_alias="@gpt1",
    agent_level=15,
    category="BUG",
    message="Null pointer dereference in main.c:142",
    related_file="src/main.c",
    tags=["crash", "high-priority"]
)
```

### `acknowledge(broadcast_id, agent_alias, comment=None)`

Acknowledge a broadcast that requires acknowledgment.

**Parameters:**
- `broadcast_id` (str): ID of the broadcast to acknowledge
- `agent_alias` (str): Alias of the acknowledging agent
- `comment` (str, optional): Optional comment

**Returns:**
- `Dict` with `success` status

### `get_broadcasts(since=None, category=None, agent=None, requires_ack_only=False, limit=50)`

Get broadcasts with optional filtering.

**Parameters:**
- `since` (str, optional): ISO timestamp - only broadcasts after this time
- `category` (str, optional): Filter by category
- `agent` (str, optional): Filter by agent alias
- `requires_ack_only` (bool): Only broadcasts requiring acknowledgment
- `limit` (int): Maximum number to return (default: 50)

**Returns:**
- `List[Dict]` of broadcast entries (newest first)

**Example:**
```python
# Get recent security broadcasts
security = workspace.get_broadcasts(category='SECURITY', limit=10)

# Get broadcasts from a specific agent
claude_broadcasts = workspace.get_broadcasts(agent='@claude1')

# Get broadcasts requiring acknowledgment
needs_ack = workspace.get_broadcasts(requires_ack_only=True)
```

### `get_pending_acks(agent_alias)`

Get broadcasts requiring acknowledgment from a specific agent.

**Parameters:**
- `agent_alias` (str): The agent to check

**Returns:**
- `List[Dict]` of broadcasts needing acknowledgment

### `get_conflicts()`

Get all unresolved CONFLICT broadcasts.

**Returns:**
- `List[Dict]` of CONFLICT broadcasts requiring acknowledgment

### `get_directives(active_only=True)`

Get DIRECTIVE broadcasts from leadership.

**Parameters:**
- `active_only` (bool): Only return recent directives (default: True)

**Returns:**
- `List[Dict]` of DIRECTIVE broadcasts

### `get_summary()`

Get a summary of the workspace state.

**Returns:**
- `Dict` with counts and recent activity:
  - `total_broadcasts`: Total number of broadcasts
  - `by_category`: Count by category
  - `pending_acks`: Number of unacknowledged broadcasts
  - `metadata`: Additional metadata

### `format_for_prompt(agent_alias, max_entries=10)`

Format recent broadcasts for inclusion in agent prompts.

**Parameters:**
- `agent_alias` (str): The agent receiving the prompt
- `max_entries` (int): Maximum entries to include

**Returns:**
- `str`: Formatted string ready for prompt injection

## Integration with Collaborative Sessions

To integrate the Global Workspace into a collaborative session:

1. **Initialize workspace** when starting a collab session:
```python
workspace = GlobalWorkspace(session_dir)
```

2. **Inject workspace summary** into agent prompts:
```python
prompt = f"""
{base_prompt}

{workspace.format_for_prompt(agent_alias, max_entries=10)}

Continue your work...
"""
```

3. **Parse broadcast tokens** from agent responses:
```python
# Look for [[BROADCAST:CATEGORY:message]] in agent output
if "[[BROADCAST:" in response:
    # Parse and post to workspace
    # Format: [[BROADCAST:SECURITY:Found XSS vulnerability]]
    pass
```

4. **Show pending acks** to agents in their next turn if they have broadcasts requiring acknowledgment.

## Permission System

The workspace implements a level-based permission system:

- **All agents** can broadcast to most categories
- **DIRECTIVE broadcasts** require **Level 20+ (Team Leader)**
  - This prevents junior agents from issuing team-wide directives
  - Ensures only experienced agents coordinate team efforts

Example permission check:
```python
# This will succeed
workspace.broadcast("@senior_agent", 25, "DIRECTIVE", "Focus on security")

# This will fail
result = workspace.broadcast("@junior_agent", 5, "DIRECTIVE", "Do this")
# result['success'] == False
# result['reason'] == "DIRECTIVE requires level 20+ (Team Leader)"
```

## Thread Safety

The GlobalWorkspace uses `filelock` for thread-safe file access:
- All read/write operations are protected by a file lock
- Multiple processes can safely access the same workspace
- Lock file: `GLOBAL_WORKSPACE.lock` in session directory

## Storage Format

The workspace stores data in JSON format:

```json
{
  "version": "1.0",
  "created": "2024-01-22T00:00:00+00:00",
  "broadcasts": [
    {
      "id": "20240122120000123456_gpt1",
      "timestamp": "2024-01-22T12:00:00+00:00",
      "agent": "@gpt1",
      "level": 10,
      "category": "SECURITY",
      "message": "Found vulnerability...",
      "requires_ack": false,
      "acks": [],
      "related_file": "src/main.c",
      "tags": ["xss", "high-priority"]
    }
  ],
  "metadata": {
    "total_broadcasts": 42,
    "categories_used": ["SECURITY", "BUG", "STATUS"]
  }
}
```

## Broadcast Limits

- Maximum broadcasts stored: **200** (configurable via `GLOBAL_WORKSPACE_MAX_BROADCASTS`)
- Older broadcasts are automatically removed when limit is reached
- Total count is maintained in metadata for historical tracking

## Best Practices

1. **Use specific categories**: Choose the most specific category for your broadcast
2. **Include context**: Use `related_file` and `tags` to provide context
3. **Require ack for critical items**: Use `requires_ack=True` for directives and conflicts
4. **Check pending acks**: Agents should check `get_pending_acks()` at the start of each turn
5. **Filter appropriately**: Use filtering to avoid information overload

## Example: Security Audit Workflow

```python
# Agent 1: Security analyst finds vulnerability
workspace.broadcast(
    "@security_bot", 15, "SECURITY",
    "SQL injection in login endpoint",
    related_file="src/auth/login.py",
    tags=["sql-injection", "critical"]
)

# Agent 2: Team lead issues directive
workspace.broadcast(
    "@team_lead", 25, "DIRECTIVE",
    "All agents: prioritize security fixes in auth module",
    requires_ack=True
)

# Agent 3: Developer acknowledges and reports status
pending = workspace.get_pending_acks("@dev_bot")
workspace.acknowledge(pending[0]['id'], "@dev_bot", "Starting work now")

workspace.broadcast(
    "@dev_bot", 10, "STATUS",
    "Fixed SQL injection, running tests"
)

# Get summary
summary = workspace.get_summary()
# {'total_broadcasts': 3, 'by_category': {...}, 'pending_acks': 0}
```

## Testing

Run the test suite:
```bash
python3 tests/test_global_workspace.py
```

Run the demonstration:
```bash
python3 demo_global_workspace.py
```

## See Also

- `core/constants.py` - Global Workspace constants
- `tests/test_global_workspace.py` - Comprehensive test suite
- `demo_global_workspace.py` - Interactive demonstration
- AGENTS.md - Agent collaboration guidelines
