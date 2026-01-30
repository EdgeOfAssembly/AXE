# Level-to-Privilege Mapping System

## Overview

The Level-to-Privilege Mapping system provides explicit privileges for agents at different levels in AXE's progression system. This implementation is based on **Herbert Simon's Sciences of the Artificial (1969)** concept of nearly-decomposable hierarchies.

## Theory Background

Simon's nearly-decomposable hierarchies have four key properties:

1. **Clear Boundaries**: Each level has explicit responsibilities and authorities
2. **Stable Sub-assemblies**: Changes at one level don't cascade destructively
3. **Explicit Interfaces**: Commands serve as the communication protocol between levels
4. **Bounded Rationality**: Restrictions prevent agents from overreaching their authority

**Reference**: Simon, H.A. (1969). *The Sciences of the Artificial*. MIT Press.  
Available at: https://archive.org/details/sciencesofartifi00simo

## System Architecture

### Privilege Tiers

The system defines four privilege tiers aligned with AXE's level milestones:

| Tier | Level Range | Title | Key Authorities |
|------|-------------|-------|-----------------|
| Worker | 1-9 | Worker | Basic broadcasts, XP voting (+10), breaks |
| Senior | 10-19 | Senior Worker / Team Leader | DIRECTIVE broadcasts, suppress workers, +15 XP votes |
| Deputy | 20-29 | Team Leader / Deputy Supervisor | Arbitration, spawning, +20 XP votes |
| Supervisor | 30+ | Deputy Supervisor / Supervisor-Eligible | TASK COMPLETE, suppress any agent, emergency escalation, +25 XP votes |

### Level Milestones

From `progression/levels.py`:
- Level 10 (1000 XP): Senior Worker
- Level 20 (5000 XP): Team Leader
- Level 30 (15000 XP): Deputy Supervisor
- Level 40 (30000 XP): Supervisor-Eligible

## Implementation Details

### Core Module: `core/privilege_mapping.py`

The privilege mapping module provides:

```python
# Get privileges for a specific level
from core.privilege_mapping import get_privileges_for_level

priv = get_privileges_for_level(15)
# Returns: {'title': 'Senior Worker / Team Leader', 'responsibilities': [...], ...}

# Format privileges for agent prompt
from core.privilege_mapping import format_privileges_for_prompt

prompt_section = format_privileges_for_prompt(15, '@llama')
# Returns formatted string explaining agent's role, authorities, restrictions

# Validate if agent can use a command
from core.privilege_mapping import validate_command

is_valid, reason = validate_command(15, '[[SUPPRESS:@worker:reason]]')
# Returns: (True, 'Authorized')

is_valid, reason = validate_command(15, '[[AGENT_TASK_COMPLETE:summary]]')
# Returns: (False, 'Command requires higher level. Your level: 15')
```

### Constants: `core/constants.py`

Control privilege system behavior:

```python
PRIVILEGE_PROMPT_SECTION = True  # Include privileges in prompts
PRIVILEGE_VALIDATION = True      # Validate commands against level
```

### Integration: `axe.py`

The privilege information is automatically injected into collaborative session prompts when `PRIVILEGE_PROMPT_SECTION` is enabled:

```python
def _get_system_prompt_for_collab(self, agent_name: str) -> str:
    # ... existing prompt building ...
    
    # Add privilege section if enabled
    privilege_section = ""
    if PRIVILEGE_PROMPT_SECTION and state:
        privilege_section = "\n\n" + format_privileges_for_prompt(level, alias) + "\n"
    
    return base_prompt + privilege_section + file_operations_section
```

## Privilege Definitions

### Worker (Levels 1-9)

**Responsibilities:**
- Execute assigned tasks thoroughly
- Report findings via broadcasts
- Ask questions when uncertain
- Collaborate with peers

**Authorities:**
- Broadcast FINDING, BUG, SECURITY, OPTIMIZATION, STATUS
- Vote XP for peers (+10 max)
- Request breaks
- Use all workshop tools

**Restrictions:**
- Cannot broadcast DIRECTIVE
- Cannot suppress other agents
- Cannot declare TASK COMPLETE
- Cannot arbitrate conflicts

**Commands:**
- `[[BROADCAST:CATEGORY:message]]`
- `[[XP_VOTE:+N:@agent:reason]]`
- `[[AGENT_BREAK_REQUEST:type:reason]]`
- `[[AGENT_PASS_TURN]]`

### Senior Worker / Team Leader (Levels 10-19)

**Responsibilities:**
- Guide junior workers
- Review peer contributions
- Prioritize subtasks
- Mentor new agents

**Authorities:**
- All Worker authorities PLUS:
- Broadcast DIRECTIVE to workers
- Suppress Worker-level agents
- Vote XP (+15 max)
- Priority turn initiative

**Restrictions:**
- Cannot suppress Senior+ agents
- Cannot declare TASK COMPLETE alone
- Cannot override Deputy decisions

**Commands:**
- `[[SUPPRESS:@worker:reason]]` (3 turns)
- `[[DIRECTIVE:instruction]]`
- `[[XP_VOTE:+15:@agent:reason]]`

### Team Leader / Deputy Supervisor (Levels 20-29)

**Responsibilities:**
- Coordinate multiple sub-teams
- Resolve conflicts between workers
- Allocate resources
- Report to Supervisor

**Authorities:**
- All Senior authorities PLUS:
- Suppress Senior-level agents
- Arbitrate Worker/Senior conflicts
- Spawn sub-sessions
- Vote XP (+20 max, -10 penalty)

**Restrictions:**
- Cannot suppress Supervisors
- Cannot override Supervisor decisions
- TASK COMPLETE requires Supervisor approval

**Commands:**
- `[[SUPPRESS:@senior:reason]]`
- `[[ARBITRATE:arb_id:resolution:winner]]`
- `[[SPAWN:model:role:reason]]`
- `[[XP_VOTE:+20:@agent:reason]]`

### Deputy Supervisor / Supervisor-Eligible (Levels 30+)

**Responsibilities:**
- Overall session success
- Final quality control
- Emergency decisions
- Human communication

**Authorities:**
- All Deputy authorities PLUS:
- Suppress any agent
- Declare TASK COMPLETE
- Final arbitration authority
- Emergency human escalation
- Vote XP (+25 max, -15 penalty)

**Restrictions:**
- Must justify major decisions
- Cannot ignore safety violations
- Must respect human overrides

**Commands:**
- `[[SUPPRESS:@any:reason]]`
- `[[AGENT_TASK_COMPLETE:summary]]`
- `[[AGENT_EMERGENCY:message]]`
- `[[XP_VOTE:+25:@agent:reason]]`

## Example Prompt Output

For a Level 15 agent (@llama), the privilege section added to the prompt would be:

```
## YOUR ROLE: Senior Worker / Team Leader (Level 15)
Agent: @llama

### RESPONSIBILITIES
- Guide junior workers
- Review peer contributions
- Prioritize subtasks
- Mentor new agents

### AUTHORITIES (What You CAN Do)
- All Worker authorities PLUS:
- Broadcast DIRECTIVE to workers
- Suppress Worker-level agents
- Vote XP (+15 max)
- Priority turn initiative

### RESTRICTIONS (What You CANNOT Do)
- ⚠️ Cannot suppress Senior+ agents
- ⚠️ Cannot declare TASK COMPLETE alone
- ⚠️ Cannot override Deputy decisions

### AVAILABLE COMMANDS
  [[SUPPRESS:@worker:reason]] (3 turns)
  [[DIRECTIVE:instruction]]
  [[XP_VOTE:+15:@agent:reason]]

### NEXT PROMOTION
Reach level 20 to become **Team Leader**
New abilities: Arbitration authority, spawn sub-sessions, +20 XP votes
```

## Usage Examples

### Demo Script

Run the demo to see the system in action:

```bash
python3 demo_privilege_mapping.py
```

This shows:
- Privilege information for all four tiers
- Command validation examples
- Promotion paths

### Testing

Run the comprehensive test suite:

```bash
python3 tests/test_privilege_mapping.py
```

The test suite validates:
- Privilege mapping structure
- Level-based privilege lookup
- Boundary level transitions (9→10, 19→20, 29→30)
- Prompt formatting
- Command validation (allow/deny)
- Promotion information
- Privilege progression
- Command token format
- Hierarchy consistency

### Manual Testing

Test privilege lookup:

```python
from core.privilege_mapping import get_privileges_for_level

# Get privileges for level 25
priv = get_privileges_for_level(25)
print(priv['title'])  # "Team Leader / Deputy Supervisor"
print(priv['authorities'])  # List of authorities
```

Test command validation:

```python
from core.privilege_mapping import validate_command

# Can a level 15 agent suppress a worker?
is_valid, reason = validate_command(15, '[[SUPPRESS:@worker:reason]]')
print(f"Valid: {is_valid}, Reason: {reason}")  # Valid: True, Reason: Authorized

# Can a level 15 agent declare task complete?
is_valid, reason = validate_command(15, '[[AGENT_TASK_COMPLETE:done]]')
print(f"Valid: {is_valid}, Reason: {reason}")  # Valid: False, Reason: Command requires higher level...
```

## Configuration

### Enabling/Disabling Privilege Prompts

In `core/constants.py`:

```python
# Enable privilege sections in prompts
PRIVILEGE_PROMPT_SECTION = True

# Enable command validation
PRIVILEGE_VALIDATION = True
```

### Customizing Privileges

To modify privilege definitions, edit `PRIVILEGE_MAPPING` in `core/privilege_mapping.py`:

```python
PRIVILEGE_MAPPING = {
    'worker': {
        'level_range': (1, 9),
        'title': 'Worker',
        'responsibilities': [...],  # Modify as needed
        'authorities': [...],       # Modify as needed
        'restrictions': [...],      # Modify as needed
        'commands': [...],          # Modify as needed
    },
    # ... other tiers
}
```

## Future Enhancements

Potential improvements:

1. **Runtime Command Validation**: Automatically enforce command restrictions in the collaboration loop
2. **Dynamic Privilege Grants**: Temporary privilege elevation for specific tasks
3. **Audit Logging**: Track privilege usage and violations
4. **Custom Tiers**: Allow projects to define custom privilege tiers
5. **Skill-Based Privileges**: Grant privileges based on acquired skills, not just level

## References

- Simon, H.A. (1969). *The Sciences of the Artificial*. MIT Press.
- `progression/levels.py` - AXE level and title system
- `core/agent_manager.py` - Agent management
- `axe.py` - Collaborative session implementation

## Related Systems

This feature depends on:
- **PR #39**: Subsumption Controller (layer definitions)
- **progression/levels.py**: Level thresholds and titles

This feature enables:
- Clear agent hierarchy in collaborative sessions
- Gamification through promotion previews
- Bounded agent autonomy (safety through restrictions)
- Explicit command authorization
