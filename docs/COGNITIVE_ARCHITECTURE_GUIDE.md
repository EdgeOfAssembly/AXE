# Cognitive Architecture in AXE - User Guide

## Overview

The cognitive architecture features (Subsumption, XP Voting, Arbitration) are now fully integrated into AXE's collaboration runtime. Agents can use these features in real multi-agent sessions, not just demos.

## Integration Status

✅ **FULLY INTEGRATED** - All features work in actual AXE collaboration sessions

### What's Integrated:

1. **Subsumption Architecture (Brooks 1986)** - Hierarchical agent control
2. **XP Voting System (Minsky 1986)** - Peer reputation voting  
3. **Conflict Detection & Arbitration (Minsky 1986)** - Automatic conflict resolution

### Where to Find It:

- **Main Runtime**: `axe.py` - CollaborationSession class
- **Initialization**: Lines 965-968 (GlobalWorkspace, SubsumptionController, ArbitrationProtocol)
- **Token Handler**: Lines 1928-2022 (_handle_cognitive_tokens method)
- **System Prompts**: Lines 1158-1165 (cognitive tokens documented for agents)

## Using Cognitive Features in AXE Sessions

### Starting a Collaboration Session

```bash
# Start a multi-agent collaboration session
python3 axe.py --collab --agents claude,gpt,llama
```

### Cognitive Architecture Tokens

Agents can use these tokens in their responses during collaboration:

#### 1. Broadcasting (Global Workspace)

```
[[BROADCAST:SECURITY:Found buffer overflow in parse_input() function]]
```

- **Purpose**: Share findings with all agents via Global Workspace
- **Categories**: SECURITY, BUG, OPTIMIZATION, CONFLICT, DIRECTIVE, STATUS, XP_VOTE, FINDING
- **Who can use**: All agents
- **Result**: Broadcast stored and available to all agents

#### 2. XP Voting (Peer Reputation)

```
[[XP_VOTE:@claude:+15:Excellent code review of authentication module]]
[[XP_VOTE:@gpt:-5:Introduced a bug in last commit]]
```

- **Purpose**: Vote XP for or against other agents
- **Format**: `@target:±XP:reason`
- **Limits**: Based on voter level (Workers ±10/-5, Team Leaders ±15/-5, Deputies ±20/-10, Supervisors ±25/-15)
- **Who can use**: All agents (cannot self-vote)
- **Result**: Vote applied at end of session, can trigger level-ups

#### 3. Suppression (Hierarchical Control)

```
[[SUPPRESS:@worker1:Handling this task at tactical level]]
```

- **Purpose**: Higher-level agent suppresses lower-level agent
- **Format**: `@target:reason`
- **Who can use**: Only agents at higher subsumption layer than target
- **Result**: Target agent skips turns for 3 turns

#### 4. Release (Restore Control)

```
[[RELEASE:@worker1]]
```

- **Purpose**: Release a suppressed agent early
- **Who can use**: Agent who created the suppression
- **Result**: Target agent can act again

#### 5. Conflict Flagging

```
[[CONFLICT:broadcast_id1,broadcast_id2:Contradictory security assessments]]
```

- **Purpose**: Manually flag conflicting broadcasts
- **Format**: `broadcast_id1,broadcast_id2:reason`
- **Who can use**: All agents
- **Result**: Conflict recorded and can trigger arbitration

#### 6. Arbitration Resolution

```
[[ARBITRATE:arb_123:Accept first assessment:broadcast_id1]]
```

- **Purpose**: Resolve a pending arbitration
- **Format**: `arbitration_id:resolution_text:winning_broadcast_id`
- **Who can use**: Only agents meeting required level (≥ max(conflicting agents) + 10)
- **Result**: Conflict resolved, XP awarded to all parties

## Example Session

### Agent Interaction Flow

```
@boss: "Let's review the authentication module for security issues"

@claude (Level 15):
[[BROADCAST:SECURITY:Authentication uses MD5 hashing - CRITICAL vulnerability]]
The password hashing is using MD5 which is cryptographically broken...

@gpt (Level 10):
[[BROADCAST:SECURITY:Authentication appears secure, uses bcrypt]]
After reviewing auth.py, the implementation looks solid with bcrypt...

@boss (Level 40):
[Detects contradiction: "secure" vs "vulnerability"]
[[CONFLICT:20260130_claude,20260130_gpt:Contradictory security assessments]]

@senior_auditor (Level 25):
[[ARBITRATE:conflict_123:After investigation, auth.py uses bcrypt (secure), test_auth.py uses MD5 (insecure):20260130_gpt]]

@claude:
[[XP_VOTE:@senior_auditor:+20:Excellent detailed investigation and resolution]]

[End of session]
🗳️  Applying 1 pending XP vote(s)...
  ✓ @claude → @senior_auditor
    🎉 @senior_auditor LEVELED UP! 25 → 26
```

## Database Persistence

All cognitive architecture features persist to the AXE database:

- **Broadcasts**: Stored in `broadcasts` table
- **Conflicts**: Stored in `conflicts` table
- **Arbitrations**: Stored in `arbitrations` table
- **Votes**: Stored in GlobalWorkspace JSON, applied to `agent_state` table
- **XP/Levels**: Updated in `agent_state` table

## Verifying Integration

### Check if Features are Active

```python
# In AXE collaboration session, agents will see these in their system prompt:
COGNITIVE ARCHITECTURE TOKENS (Subsumption, Voting, Arbitration):
- Broadcast finding: [[BROADCAST: CATEGORY: your message here ]]
- Vote for peer: [[XP_VOTE: @target:+15:reason ]]
- Suppress agent: [[SUPPRESS: @target:reason ]]
...
```

### Check Database

```bash
# Check if agents have voted
sqlite3 ~/.axe/agent.db "SELECT * FROM agent_state WHERE xp > 0;"

# Check broadcasts table exists
sqlite3 ~/.axe/agent.db ".schema broadcasts"
```

## Key Differences from Demos

| Aspect | Demos | Runtime Integration |
|--------|-------|---------------------|
| **Usage** | Standalone scripts | Part of `axe.py --collab` |
| **Agents** | Mock/test agents | Real LLM agents |
| **Persistence** | Temporary databases | Permanent AXE database |
| **Interaction** | Scripted | Natural agent responses |
| **XP Impact** | Test data | Real XP/level changes |

## Troubleshooting

### Tokens Not Working?

1. Check agent is using exact token format: `[[TOKEN:content]]`
2. Verify token is documented in system prompt
3. Check logs for "⚠️ " warnings

### Votes Not Applied?

- Votes are applied at **end of session** only
- Check for vote limit messages during session
- Verify voter and target are different agents

### Suppression Failed?

- Suppressor must be at higher layer than target
- Worker (1-9) < Tactical (10-19) < Strategic (20-39) < Executive (40+)
- Check agent levels in status

## Architecture Notes

The integration is **non-invasive**:
- Existing AXE features unchanged
- Cognitive features are additive
- Tokens are optional - agents work without them
- Database schema extended, not replaced

## Future Enhancements

Potential improvements:
- [ ] Add Global Workspace recent broadcasts to agent prompts
- [ ] Show active suppressions in status display
- [ ] Auto-detect conflicts (currently manual flagging)
- [ ] Arbitration deadline warnings
- [ ] Vote history in agent prompts

## References

- **Brooks, R.A. (1986)**. *A Robust Layered Control System for a Mobile Robot*. MIT AI Lab.
- **Minsky, M. (1986)**. *The Society of Mind*. Simon & Schuster.
- **Baars, B.J. (1988)**. *A Cognitive Theory of Consciousness*.
