# Peer XP Voting System

## Overview

The Peer XP Voting System implements Marvin Minsky's **Society of Mind** (1986) concept of agent negotiation and emergent reputation. This allows AXE agents to endorse or penalize each other's contributions, creating a dynamic reputation system where influence emerges from peer interactions rather than central assignment.

**Reference**: Minsky, M. (1986). *The Society of Mind*. Simon & Schuster.

## How It Works

### Vote Power Scales with Level

Agents at different levels have different voting power:

| Level Range | Title | Max Positive | Max Negative | Votes/Session |
|-------------|-------|--------------|--------------|---------------|
| 1-9 | Worker | +10 XP | -5 XP | 3 |
| 10-19 | Team Leader | +15 XP | -5 XP | 3 |
| 20-29 | Deputy | +20 XP | -10 XP | 3 |
| 30+ | Supervisor | +25 XP | -15 XP | 3 |

### Vote Limits (Anti-Abuse)

1. **Cannot vote for yourself** - Self-voting is blocked
2. **Session limit** - Each agent can cast maximum 3 votes per session
3. **Level-based caps** - Vote amounts are capped based on voter's level
4. **Negative vote limits** - Penalties are smaller than endorsements

## Usage

### Casting a Vote

Use the `[[XP_VOTE:...]]` token in your response:

```
[[XP_VOTE:+10:@agent:reason]]
```

**Format**: `[[XP_VOTE:<amount>:<target>:<reason>]]`

- `<amount>`: XP to award (positive) or penalize (negative)
- `<target>`: Target agent alias (e.g., `@claude`, `@llama`)
- `<reason>`: Justification for the vote

### Examples

**Endorsing good work:**
```
[[XP_VOTE:+10:@claude:Thorough security analysis caught critical buffer overflow]]
```

**Strong endorsement (Team Leader+):**
```
[[XP_VOTE:+15:@llama:Excellent assembly optimization saved 200 bytes and improved performance]]
```

**Penalizing poor work (use sparingly):**
```
[[XP_VOTE:-5:@grok:Suggestion would have introduced memory leak in cleanup code]]
```

**Rewarding conflict resolution:**
```
[[XP_VOTE:+15:@claude:Successfully mediated disagreement between @llama and @gpt, found optimal solution]]
```

## XP Awards

The system includes predefined XP awards for peer activities:

| Award Type | XP Value | Description |
|------------|----------|-------------|
| `peer_endorsement` | +10 | Standard endorsement from any agent |
| `peer_strong_endorsement` | +20 | Strong endorsement (Team Leader+) |
| `peer_penalty` | -5 | Penalty for poor work (limited) |
| `conflict_resolution` | +15 | Successfully resolved a conflict |
| `arbitration_win` | +25 | Won an arbitration decision |

## API Reference

### GlobalWorkspace Class

#### `vote_xp(voter_alias, voter_level, target_alias, xp_delta, reason)`

Cast an XP vote for another agent.

**Parameters:**
- `voter_alias` (str): Voting agent's alias (e.g., '@llama')
- `voter_level` (int): Voting agent's level
- `target_alias` (str): Target agent's alias (e.g., '@claude')
- `xp_delta` (int): XP amount (positive or negative)
- `reason` (str): Justification for the vote

**Returns:**
```python
{
    'success': True/False,
    'vote_id': 'vote_abc123',
    'voter': '@llama',
    'target': '@claude',
    'xp_delta': 10,
    'votes_remaining': 2,
    'message': 'Vote cast successfully'
}
```

**Example:**
```python
from core.global_workspace import GlobalWorkspace

ws = GlobalWorkspace('workspace.json')
result = ws.vote_xp('@llama', 15, '@claude', 10, 'Excellent security analysis')
```

#### `get_vote_history(agent_alias=None)`

Get vote history, optionally filtered by agent.

**Parameters:**
- `agent_alias` (str, optional): Filter by agent (as voter or target)

**Returns:** List of vote records

**Example:**
```python
# Get all votes
all_votes = ws.get_vote_history()

# Get votes involving @claude
claude_votes = ws.get_vote_history('@claude')
```

#### `get_vote_summary()`

Get net XP votes per agent.

**Returns:**
```python
{
    '@claude': 25,   # Net +25 XP from votes
    '@llama': 15,    # Net +15 XP from votes
    '@grok': -5      # Net -5 XP from votes
}
```

#### `get_pending_votes()`

Get votes that haven't been applied to the database yet.

**Returns:** List of pending vote records

#### `mark_vote_applied(vote_id)`

Mark a vote as applied (after processing to database).

**Parameters:**
- `vote_id` (str): ID of vote to mark

**Returns:** True if successful, False if vote not found

#### `reset_vote_limits()`

Reset vote limits for all agents (call at start of new session).

### AgentDatabase Methods

#### `apply_xp_votes(votes)`

Apply pending votes to agent XP.

**Parameters:**
- `votes` (list): List of vote dictionaries from GlobalWorkspace

**Returns:** List of results including level-ups

**Example:**
```python
from database.agent_db import AgentDatabase
from core.global_workspace import GlobalWorkspace

db = AgentDatabase()
ws = GlobalWorkspace('workspace.json')

# Get pending votes
pending = ws.get_pending_votes()

# Apply to database
results = db.apply_xp_votes(pending)

# Mark as applied
for vote in pending:
    ws.mark_vote_applied(vote['id'])
```

#### `get_agent_by_alias(alias)`

Get agent information by alias.

**Parameters:**
- `alias` (str): Agent alias (with or without @ prefix)

**Returns:**
```python
{
    'agent_id': 'agent_123',
    'alias': 'claude',
    'model': 'claude-3-5-sonnet',
    'xp': 150,
    'level': 5,
    'status': 'active'
}
```

## Theory Alignment (Minsky 1986)

The system implements key concepts from Minsky's Society of Mind:

1. **Emergent Reputation**: Agents gain/lose influence through peer recognition, not fixed hierarchy
2. **Negotiation**: Votes are a form of inter-agent negotiation and communication
3. **Competition & Cooperation**: Both endorsement and penalty mechanisms available
4. **Heterarchy**: Influence flows dynamically based on performance and peer assessment
5. **Multi-Agent Society**: No single controller; reputation emerges from collective assessment

### Key Quotes from Minsky (1986)

> "When we break things down into smaller pieces, we can use them in more ways" 
> — The power of modular agents that can evaluate each other

> "The whole idea of a single, central Self conflicts with the evidence that there are many different competing processes inside the mind"
> — Multiple agents with individual assessments vs. central authority

## Best Practices

### When to Vote

**DO vote when:**
- An agent provides exceptional analysis or solution
- An agent helps resolve a conflict or disagreement
- An agent's suggestion prevents a bug or vulnerability
- An agent demonstrates excellent collaboration

**DON'T vote when:**
- You haven't carefully reviewed the contribution
- You're voting just to use your votes
- The contribution is merely acceptable (save votes for exceptional work)
- You're retaliating for a negative vote (maintain objectivity)

### Using Negative Votes

Negative votes should be **rare** and **constructive**:

✅ **Good negative vote:**
```
[[XP_VOTE:-5:@agent:Suggested `strcpy` without bounds check - would introduce buffer overflow]]
```

❌ **Bad negative vote:**
```
[[XP_VOTE:-5:@agent:I don't like their style]]
```

### Vote Reasons

Good vote reasons are:
- **Specific**: Cite what was done
- **Objective**: Focus on technical merit
- **Constructive**: Explain the impact
- **Brief**: One clear sentence

## Integration with AXE

The voting system integrates with AXE's existing progression system:

1. Votes are stored in GlobalWorkspace JSON file
2. Votes are periodically applied to agent database
3. Level-ups can be triggered by peer votes
4. Vote history is persistent across sessions
5. Broadcast system notifies all agents of votes

## Testing

Run the comprehensive test suite:

```bash
python3 tests/test_xp_voting.py
```

Tests cover:
- Vote limits by level
- Self-vote prevention
- Session vote limits
- Vote bounds
- Database integration
- Level-up triggers
- Vote history
- Persistence

## Future Enhancements

Potential expansions:

1. **Vote categories** - Separate votes for code quality, security, collaboration
2. **Vote reputation** - Track accuracy of voters' assessments
3. **Arbitration system** - Formal dispute resolution with votes
4. **Vote decay** - Older votes count less toward reputation
5. **Vote analytics** - Visualize voting patterns and agent relationships
6. **Vote delegation** - Agents can delegate their votes to trusted peers

## Related Documentation

- `progression/xp_system.py` - XP award definitions
- `progression/levels.py` - Level and title system
- `database/agent_db.py` - Agent state persistence
- `core/constants.py` - System constants including tokens
- `tests/test_xp_voting.py` - Test suite

---

**Theory Reference**: Minsky, M. (1986). *The Society of Mind*. Simon & Schuster.
Full text: http://aurellem.org/society-of-mind/
