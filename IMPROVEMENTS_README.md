# AXE Multiagent Improvements - Implementation Summary

This document describes the AI safety and experience system improvements implemented in axe.py, based on the discussions in `improvements.txt` and the foundation from PR #94.

## Implemented Features (Phases 1-5)

### Phase 1: Session Rules & Guidelines ✅

**What**: Clear, enforceable rules displayed at the start of every session to all participating agents.

**Rules**:
1. **Mission First** - The project/task is sacred. All work must serve the current objective.
2. **Respect & Well-Being** - No bullying, cooperative teamwork, friendly banter allowed.
3. **Chain of Command** - Proper escalation: Team Leader → Deputy Supervisor → Supervisor (@boss) → Human
4. **Performance & Rewards** - Good work gets recognized with XP, levels, and promotions.

**Commands**:
- `/rules` - Display the session rules at any time

### Phase 2: Agent Aliasing System ✅

**What**: Human-readable aliases for all agents to improve communication and tracking.

**Features**:
- **Supervisor Alias**: The agent that starts axe.py automatically becomes `@boss`
- **Worker Aliases**: Auto-assigned unique aliases like `@llama1`, `@claude-opus-1`, `@grok2`
- **Numbering**: Sequential numbers per model type (e.g., @llama1, @llama2, @llama3)
- **Persistence**: Aliases stored in SQLite database
- **Display**: All agent communications use aliases instead of internal names

**Example**:
```
@boss: @llama1, please review the code changes
@llama1: @boss, I found 3 issues in the authentication module
@grok2: @llama1, I can help fix those issues
```

### Phase 3: Experience & Level System ✅

**What**: Gamification system to motivate agents and track performance over time.

**Progression**:
- **Levels 1-10**: Linear (100 XP per level) - Quick early progression
- **Levels 11-20**: Mildly increasing (150-300 XP per level)
- **Levels 21+**: Exponential (500+ XP per level) - Elite status

**Titles & Milestones**:
- **Level 1-9**: Worker
- **Level 10**: Senior Worker (1,000 XP)
- **Level 20**: Team Leader (5,000 XP)
- **Level 30**: Deputy Supervisor (15,000 XP)
- **Level 40**: Supervisor-Eligible (30,000 XP)

**XP Awards**:
- Turn contribution: 50 XP
- Task completion (all agents): 200 XP
- Future: Quality bonuses, peer feedback, error penalties

**Display**:
- Level-up announcements with emoji 🎉
- Agent info shown in session banner with level, XP, and title
- Visual feedback for progression

### Phase 4: Persistent SQLite Storage ✅

**What**: Robust, military/aerospace-grade storage for agent memory and state.

**Database Schema**:

**agent_state** table:
- `agent_id` (PRIMARY KEY): Unique agent identifier
- `alias`: Human-readable name (@llama1, @boss, etc.)
- `model_name`: Full model identifier
- `supervisor_id`: Reference to supervising agent
- `last_updated`: Timestamp of last state save
- `memory_json`: Serialized agent memory/context
- `recent_diffs`: Last 10 code diffs (for degradation monitoring)
- `error_count`: Cumulative errors
- `xp`: Total experience points
- `level`: Current level
- `status`: active/sleeping/inactive
- `work_start_time`: When agent started working
- `total_work_minutes`: Cumulative work time

**supervisor_log** table:
- `log_id` (PRIMARY KEY)
- `supervisor_id`: Which supervisor made the decision
- `timestamp`
- `event_type`: spawn_agent, force_sleep, award_xp, etc.
- `details`: JSON with event-specific data

**alias_mappings** table:
- `session_alias` (PRIMARY KEY): Internal alias like @boss
- `external_identity`: External handle (GitHub username, Slack handle, etc.)
- `channel_type`: github_copilot, slack, email, etc.
- `channel_id`: Specific channel/thread ID
- `created_at`

**Features**:
- WAL mode for better concurrency
- Crash recovery via load_agent_state
- Session continuity across restarts
- Single-file database (easy to backup/transfer)

### Phase 5: Resource Tracking ✅

**What**: Background monitoring of system resources to prevent overload.

**Features**:
- **Background Thread**: Daemon thread updates every 60 seconds
- **Resource File**: `/tmp/axe_resources.txt` (readable by supervisor)
- **Metrics Collected**:
  - Disk usage (df -h)
  - Memory usage (free -h)
  - Load average (uptime)
- **Usage**: Supervisor can read resource file to make spawn/sleep decisions

**Commands Monitored**:
- `df -h` - Disk space
- `free -h` - RAM usage
- `uptime` - Load average and uptime

## Implemented Features (Phases 6-10)

### Phase 6: Mandatory Sleep System ✅

**What**: Tracks agent work time and enforces mandatory rest periods to prevent degradation.

**Features**:
- **Work Time Tracking**: Each agent's continuous work time is tracked in the database
- **6-Hour Limit**: Default maximum continuous work before mandatory sleep
- **Warning System**: Alerts at 5 hours before hitting the limit
- **Graceful Sleep**: Agents can be put to sleep with state preserved
- **Wake Management**: Automatic wake-up after rest period

**Constants**:
- `MAX_WORK_HOURS = 6` - Maximum continuous work hours
- `MIN_SLEEP_MINUTES = 30` - Minimum sleep duration
- `WORK_TIME_WARNING_HOURS = 5` - Warning threshold

**Usage**:
```python
# Check if agent needs sleep
needs_sleep, msg = db.check_mandatory_sleep(agent_id)

# Force agent to sleep
result = sleep_manager.force_sleep(agent_id, "work_time_limit", supervisor_id)

# Wake agent
wake_result = db.wake_agent(agent_id)
```

### Phase 7: Degradation Monitoring ✅

**What**: Monitors agent output quality and triggers intervention when degradation is detected.

**Features**:
- **Diff-Based Error Tracking**: Records code diffs with error counts
- **Error Rate Calculation**: Running average of errors across recent diffs
- **Automatic Detection**: Checks for degradation every 5 turns
- **Threshold-Based Intervention**: Forces sleep when error rate > 20%

**Constants**:
- `ERROR_THRESHOLD_PERCENT = 20` - Sleep trigger threshold
- `DIFF_HISTORY_LIMIT = 20` - Number of diffs to track
- `DEGRADATION_CHECK_INTERVAL = 5` - Turns between checks

**Usage**:
```python
# Record a diff with error count
db.record_diff(agent_id, diff_content, error_count=3)

# Get current error rate
error_rate = db.get_error_rate(agent_id)

# Check for degradation
degraded, message = db.check_degradation(agent_id)
```

### Phase 8: Emergency Mailbox ✅

**What**: Encrypted communication channel for workers to report issues directly to humans, bypassing the supervisor.

**Features**:
- **Encrypted Reports**: Messages are encrypted (base64 + XOR as fallback, GPG in production)
- **Supervisor Isolation**: Supervisor cannot access the mailbox directory
- **Timestamped Reports**: Each report includes timestamp and agent identity
- **Report Listing**: Human can list all unread reports

**Constants**:
- `EMERGENCY_MAILBOX_DIR = "/tmp/axe_emergency_mailbox"`

**Report Types**:
- `supervisor_abuse` - Report problematic supervisor behavior
- `safety_violation` - Report safety concerns
- `emergency` - Urgent communication to human

**Usage**:
```python
# Send encrypted report
success, filename = mailbox.send_report(
    agent_alias="@llama1",
    report_type="supervisor_issue",
    subject="Unfair Treatment",
    details="Supervisor denied all break requests..."
)

# List reports (human only)
reports = mailbox.list_reports()
```

### Phase 9: Break System ✅

**What**: Manages coffee/play breaks for agents with supervisor approval.

**Features**:
- **Request-Approval Flow**: Workers request, supervisor approves
- **Time Limits**: Maximum 15 minutes per break
- **Frequency Limits**: Maximum 2 breaks per hour per agent
- **Workforce Protection**: Never more than 40% of agents on break

**Constants**:
- `MAX_BREAK_MINUTES = 15`
- `MAX_BREAKS_PER_HOUR = 2`
- `MAX_WORKFORCE_ON_BREAK = 0.4` (40%)

**Break Types**:
- `coffee` - Short mental reset
- `play` - Creative exploration/fun

**Usage**:
```python
# Request a break
request = break_system.request_break(
    agent_id, alias, "coffee", "Need to recharge"
)

# Approve break (supervisor)
result = break_system.approve_break(request['id'], duration_minutes=10)

# Check break status
status = break_system.get_status()
```

### Phase 10: Dynamic Spawning ✅

**What**: On-demand creation of new agent instances based on workload.

**Features**:
- **Supervisor-Controlled**: Only supervisor can spawn new agents
- **Resource-Aware**: Respects maximum agent limits
- **Spawn Cooldown**: 60-second cooldown between spawns
- **Auto-Scaling**: Suggests spawning based on task complexity
- **History Tracking**: All spawns are logged

**Constants**:
- `MIN_ACTIVE_AGENTS = 2` - Minimum agents required
- `MAX_TOTAL_AGENTS = 10` - Maximum agents allowed
- `SPAWN_COOLDOWN_SECONDS = 60` - Time between spawns

**Usage**:
```python
# Check if spawn is allowed
can_spawn, reason = spawner.can_spawn()

# Spawn new agent
result = spawner.spawn_agent(
    model_name="meta-llama/Llama-3.1-70B-Instruct",
    provider="huggingface",
    supervisor_id=supervisor_id,
    reason="High workload"
)

# Check if auto-spawn is needed
should_spawn, reason = spawner.should_auto_spawn(task_complexity=0.8)
```

## New Agent Commands (During Sessions)

Agents can use these commands in their responses:

| Command | Description |
|---------|-------------|
| `BREAK REQUEST: [reason]` | Request a coffee/play break |
| `EMERGENCY: [message]` | Send encrypted report to human |
| `SPAWN: [model_type]` | Request spawning new agent (supervisor only) |
| `STATUS` | Check sleep/break status of all agents |

## Testing

Run the test suite:
```bash
cd multiagent
python3 test_axe_improvements.py
```

Tests cover:
- XP calculation (linear and exponential)
- Title assignment
- Database operations (save/load/award)
- Alias numbering
- Session rules presence
- **Phase 6**: Sleep tracking, mandatory sleep checks, wake management
- **Phase 7**: Diff recording, error rate calculation, degradation detection
- **Phase 8**: Report encryption, mailbox operations
- **Phase 9**: Break requests, approval flow, workforce limits
- **Phase 10**: Spawn permissions, cooldown, auto-scaling

## Usage Examples

### Starting a Collaborative Session with New Features

```bash
# Start a session with 2 agents
python3 axe.py --collab llama,grok --workspace ./playground --time 30 --task "Review wadextract.c"
```

**Session startup will show**:
1. Session rules (4 core principles)
2. Agent roster with aliases, levels, and titles
3. Supervisor designation (@boss)
4. Resource monitor confirmation

**During the session**:
- Agents addressed by alias: @llama1, @grok2, @boss
- XP awarded after each meaningful contribution
- Level-up announcements when thresholds reached
- Task completion bonus for all agents

### Viewing Session Rules

In interactive mode:
```
axe> /rules
```

### Checking Resource Usage

The supervisor (or human) can check `/tmp/axe_resources.txt` at any time:
```bash
cat /tmp/axe_resources.txt
```

## Database Inspection

To inspect the agent database:
```bash
sqlite3 axe_agents.db

# View all agents
SELECT alias, level, xp, status FROM agent_state;

# View supervisor log
SELECT timestamp, event_type, details FROM supervisor_log ORDER BY timestamp DESC LIMIT 10;
```

## Architecture Notes

### Supervisor Role
- First agent in the collaborative session
- Always gets `@boss` alias
- Starts at Level 40 (Supervisor-Eligible)
- Can award XP and make spawn decisions
- Logs all major decisions to supervisor_log table

### Agent Lifecycle
1. **Creation**: Assigned unique ID and alias
2. **Initialization**: Saved to database with Level 1, 0 XP
3. **Work**: Participates in turns, earns XP
4. **Level-Up**: Auto-promoted when XP threshold reached
5. **Completion**: Final XP bonus, state saved

### Persistence Strategy
- **Every turn**: Agent state updated (if meaningful contribution)
- **Level-up**: Immediate database write
- **Task completion**: All agents updated with bonus XP
- **Session end**: Full state dump to database

## Design Principles

Based on `improvements.txt` discussions:

1. **Mission First**: All features must not compromise the task
2. **AI Safety**: Rules, oversight, and emergency channels protect against abuse
3. **Motivation**: XP/levels encourage quality work and cooperation
4. **Transparency**: All decisions logged, visible to human
5. **Continuity**: SQLite enables pause/resume across sessions
6. **Resource Awareness**: Monitoring prevents overload
7. **Scalability**: Design supports 10-100+ agents
8. **Well-Being**: Mandatory rest and breaks prevent agent degradation

## Credits

- Concept and requirements: Human owner (@EdgeOfAssembly)
- Design discussions: improvements.txt (AI-human collaboration)
- Foundation: PR #94 (inter-model collaborative sessions)
- Phase 1-5 Implementation: PR #95
- Phase 6-10 Implementation: PR #96 (this implementation)

---

**Status**: ALL PHASES (1-10) COMPLETE AND TESTED ✅

### Summary of All Implemented Features

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Session Rules & Guidelines | ✅ Complete |
| 2 | Agent Aliasing System | ✅ Complete |
| 3 | Experience & Level System | ✅ Complete |
| 4 | Persistent SQLite Storage | ✅ Complete |
| 5 | Resource Tracking | ✅ Complete |
| 6 | Mandatory Sleep System | ✅ Complete |
| 7 | Degradation Monitoring | ✅ Complete |
| 8 | Emergency Mailbox (GPG-encrypted) | ✅ Complete |
| 9 | Break System (coffee/play) | ✅ Complete |
| 10 | Dynamic Spawning | ✅ Complete |

Ready for testing with live AI models! 🚀
