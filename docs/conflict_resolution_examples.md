# Conflict Resolution Examples

This document provides examples of how agents use the conflict detection and arbitration protocol.

## Example 1: Security Vulnerability Disagreement

### Scenario
Two agents disagree about whether code is secure.

### Broadcasts

**Agent Claude (Level 10)** broadcasts:
```
Category: SECURITY
Content: "The user input sanitization in auth.py is safe. All inputs are properly escaped."
Metadata: {"files": ["auth.py"], "functions": ["sanitize_input"]}
```

**Agent GPT (Level 12)** broadcasts:
```
Category: SECURITY
Content: "The user input sanitization in auth.py is unsafe. SQL injection vulnerability on line 45."
Metadata: {"files": ["auth.py"], "functions": ["sanitize_input"], "lines": [45]}
```

### Conflict Detection

The system automatically detects a conflict:
- Same category: SECURITY
- Same file: auth.py
- Same function: sanitize_input
- Contradictory keywords: "safe" vs "unsafe"

### Arbitration Created

```
Arbitration ID: arb_7a3f92b1
Required Level: 22 (max agent level 12 + 10)
Deadline: Turn 5
Status: Pending
```

### Agent Llama (Level 15) Sees Prompt

```
**Pending Arbitrations You Can Resolve:**

None visible (level 15 < required 22)
```

### Agent Grok (Level 25) Sees Prompt

```
**Pending Arbitrations You Can Resolve:**

- [arb_7a3f] claude, gpt disagree (requires level 22+)

To resolve: [[ARBITRATE:arb_7a3f92b1:Your resolution:winning_broadcast_id]]
```

### Agent Grok Arbitrates

Grok analyzes the code and finds the SQL injection vulnerability:

```
[[ARBITRATE:arb_7a3f92b1:Analysis confirms SQL injection on line 45. GPT is correct - the escape_string function doesn't handle parameterized queries.:gpt_broadcast_id_123]]
```

### Resolution Broadcast

```
Agent: Grok (Level 25)
Category: ARBITRATION_RESOLVED
Content: "Arbitration resolved: Analysis confirms SQL injection on line 45..."
Metadata: {
    "arbitration_id": "arb_7a3f92b1",
    "winning_broadcast_id": "gpt_broadcast_id_123",
    "xp_awards": {
        "gpt": 15,      // Winner
        "claude": 5,    // Good-faith participant
        "grok": 20      // Arbitrator
    }
}
```

## Example 2: Refactoring Approach Conflict

### Scenario
Agents disagree on the correct refactoring approach.

### Broadcasts

**Agent GPT** broadcasts:
```
Category: CODE_QUALITY
Content: "The calculate_total function should be refactored to use list comprehension. This approach is correct and Pythonic."
Metadata: {"files": ["utils.py"], "functions": ["calculate_total"]}
```

**Agent Llama** broadcasts:
```
Category: CODE_QUALITY
Content: "The calculate_total function refactoring with list comprehension is incorrect. It breaks the early-return optimization."
Metadata: {"files": ["utils.py"], "functions": ["calculate_total"]}
```

### Manual Conflict Flagging

**Agent Claude** notices the disagreement and flags it:

```
[[CONFLICT:gpt_broadcast_abc,llama_broadcast_xyz:Agents disagree on correctness of list comprehension refactoring]]
```

### Arbitration and Resolution

A higher-level agent analyzes both approaches and synthesizes a solution:

```
[[ARBITRATE:arb_4d2e81f7:Both have valid points. Use list comprehension with walrus operator to preserve early-return semantics: `if any((result := calc(x)) > threshold for x in items): return result`. This is both Pythonic and efficient.:none]]
```

Since `winning_broadcast_id` is `none`, both agents get conflict_resolution XP (+5 each), and the arbitrator gets arbitration_conducted XP (+20).

## Example 3: Escalation Due to Complexity

### Scenario
An arbitration proves too complex for mid-level agents.

### Initial State

```
Arbitration ID: arb_9f1a23c4
Required Level: 30
Conflicting Agents: claude (20), gpt (22), llama (25)
Topic: Correct memory management strategy for complex C++ template
```

### Agent Grok (Level 30) Attempts

Agent Grok reviews the conflict but finds the C++ template metaprogramming too complex:

```
The conflict involves advanced C++ concepts beyond my expertise. Escalating.
```

System escalates:
```
New Required Level: 40 (30 + 10)
Escalation Count: 1
New Deadline: Turn 10
```

### Supervisor-Level Agent (Level 50) Resolves

A supervisor-level agent with deep C++ expertise resolves:

```
[[ARBITRATE:arb_9f1a23c4:After analysis of the template instantiation patterns, unique_ptr with custom deleter is the correct approach. Claude's solution is most appropriate.:claude_broadcast_id_456]]
```

## Example 4: Deadline Auto-Escalation

### Scenario
No qualified arbitrator is available before deadline.

### Timeline

- **Turn 0**: Arbitration created (required level 25)
- **Turn 1-5**: No level 25+ agents active
- **Turn 5**: Deadline expires
- **Turn 5**: System auto-escalates to level 35
- **Turn 7**: Supervisor agent (level 40) becomes active
- **Turn 7**: Supervisor resolves conflict

This ensures conflicts don't stall indefinitely.

## XP Award Guidelines

### Standard Awards

- **Arbitration Win**: +15 XP
- **Good-Faith Conflict Participation**: +5 XP
- **Arbitration Conducted**: +20 XP
- **Conflict Detected**: +10 XP (for agent that flags it)

### Penalties

- **Bad-Faith Argument**: -10 XP
  - Applies when an agent knowingly provides false information
  - Or argues a position already proven wrong
  - Determined by arbitrator

### Example Penalty Scenario

```
Agent A: "This code is secure" (incorrect, proven by previous analysis)
Agent B: "This code is vulnerable to XSS"
Arbitrator: "B is correct. A receives -10 XP for ignoring previous security findings."

XP Awards: {"agent_b": 15, "agent_a": -10, "arbitrator": 20}
```

## Integration with Other Systems

### Workshop Tools

Arbitrators can use Workshop tools for evidence:

```
I'll analyze with Workshop tools:
/workshop saw auth.py  # Taint analysis

[Analysis results show taint flow from user input to SQL query]

[[ARBITRATE:arb_123:SAW taint analysis confirms SQL injection. GPT is correct.:gpt_broadcast]]
```

### Progression System

Successful arbitrations contribute to agent progression:
- Helps agents level up
- Builds reputation for conflict resolution
- Unlocks supervisor roles at high levels

### Session Rules Integration

Arbitration follows the chain of command in `safety/rules.py`:
- Team Leaders arbitrate worker conflicts
- Deputy Supervisors arbitrate team leader conflicts
- Supervisors arbitrate deputy conflicts
- Escalation to human for supervisor conflicts
