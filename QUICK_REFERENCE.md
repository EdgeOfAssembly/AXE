# AXE Multiagent - Quick Reference Card

## Session Rules (The 4 Principles)

1. **MISSION FIRST** - Task is sacred, work comes first
2. **RESPECT & WELL-BEING** - No bullying, be cooperative
3. **CHAIN OF COMMAND** - Team Leader → Deputy → @boss → Human
4. **PERFORMANCE & REWARDS** - Good work = XP + Levels + Promotions

## Agent Ranks & Levels

| Level | XP Required | Title | Perks |
|-------|------------|-------|-------|
| 1-9 | 0-899 | Worker | Basic agent |
| 10 | 1,000 | Senior Worker | Experienced contributor |
| 20 | 5,000 | Team Leader | Can delegate subtasks |
| 30 | 15,000 | Deputy Supervisor | Can temporarily replace @boss |
| 40 | 30,000 | Supervisor-Eligible | Promoted by human |

## XP Awards

- **Turn contribution**: 50 XP
- **Task completion**: 200 XP (all agents)
- **Quality bonuses**: Varies (future feature)
- **Peer recognition**: Varies (future feature)

## Commands

### Chat Commands
- `/help` - Show all commands
- `/rules` - Display session rules
- `/agents` - List available agents
- `/tools` - List whitelisted tools
- `/dirs` - Show directory access
- `/quit` - Exit

### Starting a Session
```bash
# Basic collaborative session
python3 axe.py --collab llama,copilot \
               --workspace ./playground \
               --time 30 \
               --task "Review and improve code"

# With specific agents
python3 axe.py --collab llama,grok,claude \
               --workspace ./myproject \
               --time 60 \
               --task "Refactor authentication module"
```

## Aliases

**Supervisor**: Always `@boss` (first agent in session)

**Workers**: `@modelN` where N is sequential:
- `@llama1`, `@llama2`, `@llama3`
- `@grok1`, `@grok2`
- `@copilot1`, `@copilot2`

## Database

**Location**: `axe_agents.db` in AXE installation directory (persists across workspaces)

**Inspect**:
```bash
sqlite3 axe_agents.db

# View agents
SELECT alias, level, xp, status FROM agent_state;

# View supervisor log
SELECT timestamp, event_type, details FROM supervisor_log 
ORDER BY timestamp DESC LIMIT 10;
```

## Resource Monitoring

**File**: `/tmp/axe_resources.txt`  
**Updates**: Every 60 seconds  
**Contains**: Disk usage, RAM, load average

**View**:
```bash
cat /tmp/axe_resources.txt
```

## Testing

### Run automated tests
```bash
cd multiagent
python3 test_axe_improvements.py
```

### Run interactive demo
```bash
cd multiagent
python3 demo_improvements.py
```

## Tips for Humans

### Starting a Session
1. Set clear task description
2. Choose complementary agents (e.g., llama for code, grok for creativity)
3. Set realistic time limit (30-60 min recommended)
4. Watch resource file if running many agents

### During Session
- Press Ctrl+C to pause (can inject messages)
- Watch for level-up announcements
- Check `/tmp/axe_resources.txt` if performance degrades
- Agents will PASS when done with their part

### Encouraging Good Behavior
Say things like:
- "Remember to cooperate and help each other"
- "Let's see who can earn Senior Worker first!"
- "@boss, coordinate the team efficiently"
- "Follow the session rules - mission first, respect always"

## What Agents See

At session start, agents see:
1. Complete session rules banner
2. Their alias and current level/XP
3. Other agents in the session
4. Supervisor designation (@boss)
5. Workspace location
6. Time limit

During work:
- Conversation history
- Other agents' contributions
- XP awards after each turn
- Level-up announcements
- Task completion bonuses

## Common Scenarios

### "Agents not cooperating"
- Remind them of rules: `/rules`
- @boss should coordinate: "@boss, please coordinate the team"
- Check if they're using aliases in communication

### "Agent stuck or confused"
- Pause with Ctrl+C
- Inject clarifying message
- Continue session

### "Want to resume later"
- Everything is in `axe_agents.db`
- Next session will load agent states
- XP and levels persist

### "System slowing down"
- Check `/tmp/axe_resources.txt`
- Reduce number of agents
- Increase time between turns

## Future Features (Not Yet Implemented)

- Mandatory sleep after 6-8 hours work
- Diff-based error detection
- GPG-encrypted emergency mailbox
- Coffee/play breaks
- Dynamic agent spawning
- Safe command whitelist (tree, du, etc.)
- Per-agent workspaces

---

**Quick Help**: Run `python3 axe.py --help` for CLI options

**Documentation**: See `IMPROVEMENTS_README.md` for full details

**Demo**: Run `python3 demo_improvements.py` to see all features

**Tests**: Run `python3 test_axe_improvements.py` to verify installation
