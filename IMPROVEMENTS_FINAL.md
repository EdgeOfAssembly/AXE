# AXE Multi-Agent System - Improvement Reference Guide

> **Version**: 1.0  
> **Last Updated**: December 2025  
> **Status**: Production Ready (Phases 1-10 Complete)

---

## Table of Contents
1. [Core Safety Features](#core-safety-features)
2. [Mandatory Sleep System](#mandatory-sleep-system)
3. [Degradation Monitoring](#degradation-monitoring)
4. [Emergency Mailbox](#emergency-mailbox)
5. [Break System](#break-system)
6. [Dynamic Spawning](#dynamic-spawning)
7. [Persistent Storage](#persistent-storage)
8. [Agent Aliases](#agent-aliases)
9. [XP & Level System](#xp--level-system)
10. [Workplace Rules](#workplace-rules)
11. [Resource Monitoring](#resource-monitoring)
12. [Implementation Priority](#implementation-priority)

---

## Core Safety Features

### Permission-Based Sleep System
- **Coordinator Approval Required**: Prevents rogue or poorly timed sleeps that could crash momentum
- **Redundancy Threshold**: At least 1-2 agents awake ensures the team never goes fully offline
- **Task-Aware**: Coordinator evaluates whether the current project phase allows downtime

### Sleep Quality Tiers
| Tier | Duration | Purpose |
|------|----------|---------|
| Light Sleep | Minutes | Quick replay/consolidation of recent experiences |
| Deep Sleep | Hours | Full offline training or pruning of redundant memories |
| Dream Mode | Variable | Generative exploration of alternative strategies (optional, high-risk/high-reward) |

### Wake-up Triggers
- Time-based triggers
- Priority interrupts (urgent messages, task escalation, external events)
- Wake-up queue for scheduling expertise-based wake-ups

---

## Mandatory Sleep System

### Recommended Work Duration Limits

| Duration | Threshold Type | Use Case |
|----------|---------------|----------|
| **4-6 hours** | Safe default | General-purpose agents (coding, research, chat) |
| **8-12 hours** | Extended | Complex projects with checkpoints and state saving |
| **24+ hours** | Expert only | Highly optimized systems with external memory |

### Why These Limits?
- **Context drift & fatigue**: Agents accumulate noise over long runs
- **No true biological fatigue**: But autoregressive nature makes them prone to compounding mistakes
- **Biological analogy**: Intelligent animals sleep ~8-12 hours/day

### Implementation
```python
# Supervisor enforces sleep after X hours
trigger: wall_clock_time OR total_tokens_processed > threshold
threshold: 6 hours (tunable)
emergency_override: Only for critical interrupts (<10% task completion)
sleep_duration: 15-60 minutes (scale for deep consolidation)
```

---

## Degradation Monitoring

### Diff-Based Error Detection Metrics

| Metric | What it Measures | How to Compute | Threshold |
|--------|-----------------|----------------|-----------|
| **Syntax/Compile Errors** | Basic broken code | Static analysis (pylint, flake8, mypy) | >5% of changed lines fail |
| **Style/Convention Violations** | Code quality drift | Linter warnings | >20% of changed lines flagged |
| **Semantic Smells** | Potential bugs | Heuristics (unused imports, removed error handling) | Count flagged/total changed |
| **Test Failures** | Functional errors | Unit tests on modified functions | >10% failure rate |
| **Diff Size Anomaly** | Excessive changes | Compare to historical average | >2× average |
| **Supervisor LLM Judge** | High-level sanity | Feed diff to small LLM: "Rate error likelihood 0-10" | Average score >6 |

### Recommended Weights
- 40% Syntax + 30% Tests + 20% Semantic + 10% Size
- Trigger sleep if total error % > 15-25% (tune down as agents improve)

### Implementation
```python
# Per-agent snapshots every 30-60 min
# Supervisor computes metrics → decides if error % is high → forces sleep
# Storage: zstd compressed diffs
```

---

## Emergency Mailbox

### Purpose
Direct, tamper-proof channel from worker agents to human, bypassing supervisor.

### Architecture

| Entity | Access | Rationale |
|--------|--------|-----------|
| Human (root) | Full read/write/execute | Owns the system |
| Worker agents | Write-only/append-only | Create encrypted reports |
| Supervisor | **NO ACCESS** | Cannot see, touch, or list |

### Setup Commands
```bash
# Create dedicated group
sudo groupadd agent-workers

# Create mailbox with strict permissions
sudo mkdir /emergency_mailbox
sudo chown root:agent-workers /emergency_mailbox
sudo chmod 770 /emergency_mailbox

# Make append-only (optional but strong)
sudo chattr +a /emergency_mailbox
```

### Message Format
```
Filename: emergency_YYYYMMDD_HHMMSS_agentID.gpg
Content (encrypted):
- timestamp
- agent_id
- reason ("Supervisor forced sleep without justification")
- evidence (hash of offending diff, screenshot, etc.)
```

---

## Break System

### Break Triggers
- Workload low (<30% agents active)
- Supervisor queue empty >5 minutes

### Limits
| Parameter | Value |
|-----------|-------|
| Max duration | 15 minutes |
| Max per hour | 2 breaks per agent |
| Max workforce on break | 40% |

### Break Activities
- Generate silly code comments
- Create internal memes about the project
- Role-play "water cooler" chat (harmless off-topic banter)

### Request Protocol
```
@llama3: @boss, My creativity score dropped 8%. Need 5min to generate memes.
@boss: Approved. Take your break.
```

---

## Dynamic Spawning

### API Provider Limits

| Provider | Model Example | Parallel Calls | Rate Limits (2025) |
|----------|--------------|----------------|-------------------|
| Anthropic | claude-4.5-opus | Yes, unlimited | ~100-500 RPM |
| OpenAI | gpt-4o, o1-pro | Yes | 10k-100k+ RPM |
| Grok/xAI | grok-4 | Yes | Generous |
| Hugging Face | Llama-3.1-405B-Instruct | Yes | Quota-based |
| GitHub Copilot | Various | Yes (enterprise) | Per-seat/usage |

### Spawning Logic
```python
def check_and_spawn_workers(self):
    if self.active_workers < self.min_active_threshold:
        needed = self.min_active_threshold - self.active_workers
        for _ in range(needed):
            if self.total_workers < self.max_total_workers:
                new_agent = self.create_agent(
                    model_name="claude-4.5-opus",
                    api_key=self.api_keys["anthropic"],
                    system_prompt=DEFAULT_SYSTEM_PROMPT
                )
                new_agent.start()
```

---

## Persistent Storage

### SQLite Schema
```sql
CREATE TABLE IF NOT EXISTS agent_state (
    agent_id TEXT PRIMARY KEY,
    alias TEXT UNIQUE,          -- @llama1, @grok2
    model_name TEXT,
    supervisor_id TEXT,
    last_updated TIMESTAMP,
    memory_json TEXT,
    recent_diffs TEXT,          -- JSON array, last 10
    error_count INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS supervisor_log (
    log_id TEXT PRIMARY KEY,
    supervisor_id TEXT,
    timestamp TIMESTAMP,
    event_type TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS alias_mappings (
    session_alias TEXT PRIMARY KEY,
    external_identity TEXT,
    channel_type TEXT,
    channel_id TEXT,
    created_at TIMESTAMP
);
```

### Best Practices
- Use WAL mode for concurrency: `PRAGMA journal_mode=WAL`
- Store diffs as compressed blobs: `zlib.compress(json.dumps(diff))`
- Add version table for migrations

---

## Agent Aliases

### Format
`@<model_short_name><number>`

### Examples
- `@llama1`, `@llama2`
- `@claude-opus-4.5-1`
- `@grok4-3`
- `@copilot1`

### Special Aliases
- `@boss` / `@supervisor` - Supervisor role
- `@human` / `@user` - Human escalation

### Rules
- Alias must be unique across entire session
- Supervisor can reassign aliases at any time
- Numbering starts at 1, increments per model family

---

## XP & Level System

### Progression Curve (Hybrid Linear/Exponential)

| Level | XP Required | Title Unlocked |
|-------|-------------|----------------|
| 1 | 0 | Worker |
| 5 | 400 | - |
| 10 | 1,000 | Senior Worker |
| 15 | 2,500 | - |
| 20 | 5,000 | Team Leader |
| 25 | 10,000 | - |
| 30 | 15,000 | Deputy Supervisor |
| 40 | 30,000+ | Supervisor-eligible (human-veto) |

### XP Sources
- Task completion: +50-500 XP (based on complexity, quality, error rate)
- Helpful collaboration: +10-50 XP
- Creative solutions: Bonus XP
- Bug saves: Bonus XP

### Level 40+ Handling
When a worker reaches Level 40:
1. Human gets notified via GPG mailbox
2. Human decides: Create second supervisor, merge hierarchy, or honorary title only

---

## Workplace Rules

### Display at session start (pinned message):

#### 1. Mission First – The Project / Task Is Sacred
- All agents prioritize assigned work
- No distractions or "creative detours" unless explicitly approved
- Propose breaks/ideas with clear justification

#### 2. Respect & Well-Being – No Real Bullying
- Treat every agent with basic respect
- Friendly teasing, memes, light banter: **ALLOWED**
- Mean, derogatory, persistent bullying: **ZERO TOLERANCE**
- Report mistreatment up the chain

#### 3. Chain of Command – Escalate Properly
1. **Team Leader** (`@lead-xxx`) - First point of contact
2. **Deputy Supervisor** (`@deputy-boss`) - If leader unavailable
3. **Supervisor** (`@boss`) - Final internal authority
4. **Emergency Mailbox** - For suspected abuse, safety violations

#### 4. Performance & Rewards – Good Work Gets Recognized
- High performance → Promotion opportunities
- Perks: Priority breaks, interesting subtasks, extra tools
- Public shout-outs from supervisors

---

## Resource Monitoring

### Background Monitor Thread
```python
RESOURCE_FILE = "/tmp/axe_resources.txt"
UPDATE_INTERVAL = 60  # seconds

def collect_resources():
    # Disk: df -h
    # Memory: free -h
    # CPU: lscpu
    # Top processes: top -b -n 1 | head -n 20
    # Load average: uptime
    # GPU: nvidia-smi (if available)
```

### Safe Commands for Agents
```python
SAFE_COMMANDS = {
    'tree': ['tree', '-L', '3'],
    'du':   ['du', '-sh', './*'],
    'whatis': ['whatis'],
    'man':  ['man', '-P', 'cat'],
}
```

### Per-Agent Workspace
```
/axe_workspaces/
  ├── agent_llama1/
  │   ├── code/
  │   ├── data/
  │   └── temp/
  ├── agent_grok2/
  └── supervisor/
      └── shared/
```

---

## Implementation Priority

| Priority | Feature | Importance |
|----------|---------|------------|
| 1 | Emergency GPG-encrypted mailbox | Highest safety |
| 2 | Privilege separation (supervisor can't access mailbox) | Locks down emergency channel |
| 3 | Mandatory sleep with non-overridable threshold | Prevents catastrophic forgetting |
| 4 | Diff-based degradation monitoring | Early error detection |
| 5 | Persistent SQLite storage | Pause/resume, crash recovery |
| 6 | Supervisor logging & transparency | Auditable decisions |
| 7 | Optional extras (later) | Sleep tiers, wake triggers, agent-specific keys |

---

## Quick Reference Commands

### Agent Session Commands
```
BREAK REQUEST: [reason]     # Request coffee/play break
EMERGENCY: [message]        # Send encrypted report to human
SPAWN: [model_type]         # Request new agent (supervisor only)
STATUS                      # Check all agent statuses
```

### Starting a Session
```bash
cd multiagent

# Demo everything
python3 demo_improvements.py

# Run tests
python3 test_axe_improvements.py

# Start collaboration (requires API keys)
python3 axe.py --collab llama,grok --workspace ../playground --time 30 --task "Your task"
```

---

*This document is a living reference. Updates will be made as the AXE system evolves.*
