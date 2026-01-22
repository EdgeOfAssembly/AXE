# Peer XP Voting System - Implementation Summary

## What Was Implemented

This PR implements **Minsky's Society of Mind** (1986) concept of agent negotiation and emergent reputation through a peer XP voting system. Agents can now endorse or penalize each other's contributions, creating dynamic reputation that emerges from peer interactions rather than central assignment.

## Key Features

### 1. GlobalWorkspace Class (`core/global_workspace.py`)
- **Peer voting system** with level-based limits
- **Vote tracking** in persistent JSON workspace
- **Broadcast messaging** for inter-agent communication
- **Session limits** to prevent vote spam (3 votes per agent)
- **Self-vote prevention** for fairness
- **Vote history** and summary analytics

### 2. Vote Power Scales with Level

| Level | Title | Max Positive | Max Negative |
|-------|-------|--------------|--------------|
| 1-9 | Worker | +10 XP | -5 XP |
| 10-19 | Team Leader | +15 XP | -5 XP |
| 20-29 | Deputy | +20 XP | -10 XP |
| 30+ | Supervisor | +25 XP | -15 XP |

### 3. Database Integration (`database/agent_db.py`)
- **`apply_xp_votes()`** - Process pending votes from workspace
- **`get_agent_by_alias()`** - Look up agents for vote processing
- **Automatic level-ups** when votes push agent over threshold

### 4. XP Awards (`progression/xp_system.py`)
New peer voting awards:
- `peer_endorsement`: +10 XP
- `peer_strong_endorsement`: +20 XP  
- `peer_penalty`: -5 XP
- `conflict_resolution`: +15 XP
- `arbitration_win`: +25 XP

### 5. Token System (`core/constants.py`)
New token: `AGENT_TOKEN_XP_VOTE = "[[XP_VOTE:"`

Format: `[[XP_VOTE:<amount>:<target>:<reason>]]`

Example: `[[XP_VOTE:+10:@claude:Excellent buffer overflow analysis]]`

## Files Created

1. **`core/global_workspace.py`** (360 lines)
   - Complete voting infrastructure
   - Vote tracking and limits
   - Broadcast system
   - Workspace persistence

2. **`tests/test_xp_voting.py`** (486 lines)
   - 10 comprehensive test functions
   - Tests all voting mechanics
   - Tests database integration
   - Tests anti-abuse limits

3. **`docs/xp_voting.md`** (320 lines)
   - Complete documentation
   - API reference
   - Usage examples
   - Best practices
   - Theory alignment

4. **`examples/xp_voting_demo.py`** (217 lines)
   - Interactive demonstration
   - 13 usage scenarios
   - Educational walkthrough

## Files Modified

1. **`progression/xp_system.py`**
   - Added 5 peer voting XP awards

2. **`database/agent_db.py`**
   - Added `apply_xp_votes()` method
   - Added `get_agent_by_alias()` helper

3. **`core/constants.py`**
   - Added `AGENT_TOKEN_XP_VOTE` token

4. **`docs/README.md`**
   - Added documentation links

## Test Results

✅ **All 10 tests passing:**
- ✅ XP award definitions
- ✅ Vote limits by level
- ✅ Self-vote prevention
- ✅ Session vote limits
- ✅ Vote history retrieval
- ✅ Vote application to database
- ✅ Level-up from votes
- ✅ Negative votes
- ✅ Workspace persistence
- ✅ Broadcast system

## Usage Example

```python
from core.global_workspace import GlobalWorkspace
from database.agent_db import AgentDatabase

# Create workspace
ws = GlobalWorkspace('workspace.json')
db = AgentDatabase()

# Agent votes
ws.vote_xp('@llama', 12, '@claude', 15, 
          'Excellent security analysis found buffer overflow')

# Apply votes to database
pending = ws.get_pending_votes()
results = db.apply_xp_votes(pending)

# Mark as applied
for vote in pending:
    ws.mark_vote_applied(vote['id'])
```

## Theory Alignment (Minsky 1986)

✅ **Emergent Reputation**: Agents gain/lose influence through peer recognition

✅ **Negotiation**: Votes are a form of inter-agent negotiation

✅ **Competition & Cooperation**: Both endorsement and penalty mechanisms

✅ **Heterarchy**: Influence flows dynamically, not fixed hierarchy

✅ **Anti-Abuse**: Multiple limits prevent gaming the system

## Statistics

- **Total Lines Added**: 1,382
- **New Classes**: 1 (GlobalWorkspace)
- **New Methods**: 11
- **Test Coverage**: 10 test functions
- **Documentation**: 320 lines
- **Examples**: 217 lines

## Integration Points

The voting system integrates with:
1. **XP System** - Uses existing XP and level-up mechanics
2. **Agent Database** - Persists votes and applies to agent state
3. **Constants** - Uses token system for agent communication
4. **Skills System** - Can be triggered by agent skills
5. **Multi-agent Collaboration** - Enables peer assessment

## Next Steps (Future Work)

Potential enhancements:
1. **Vote categories** - Separate votes for different aspects
2. **Vote reputation** - Track accuracy of voters
3. **Arbitration system** - Formal dispute resolution
4. **Vote decay** - Older votes count less
5. **Vote analytics** - Visualize voting patterns
6. **Vote delegation** - Agents delegate to trusted peers

## Security Considerations

✅ **Self-vote prevention** - Cannot vote for yourself

✅ **Session limits** - Max 3 votes per agent per session

✅ **Level-based caps** - Vote power scales with level

✅ **Negative vote limits** - Penalties smaller than endorsements

✅ **Persistent tracking** - All votes logged to workspace

## Performance

- **O(1)** vote casting
- **O(n)** vote history retrieval (n = number of votes)
- **O(m)** vote application (m = number of pending votes)
- **Lightweight** JSON workspace storage
- **No blocking** operations

## Acceptance Criteria Status

- [x] Peer XP awards added to `xp_system.py`
- [x] `vote_xp()` method in GlobalWorkspace with level-based limits
- [x] Vote tracking in workspace JSON
- [x] Vote processing in agent_db
- [x] Self-vote prevention
- [x] Session vote limits
- [x] Token parsing for `[[XP_VOTE:...]]`
- [x] Tests passing
- [x] Documentation complete
- [x] Demo example created

## References

- **Minsky, M. (1986)**. *The Society of Mind*. Simon & Schuster.
- Full text: http://aurellem.org/society-of-mind/

---

**Status**: ✅ **COMPLETE** - Ready for review and merge

**Test Status**: ✅ All 10 tests passing

**Documentation**: ✅ Complete with examples

**Integration**: ✅ Verified with existing codebase
