# Privilege Mapping Quick Reference

Quick reference for AXE's Level-to-Privilege Mapping system.

## Level Tiers

| Level | Title | Key Authority |
|-------|-------|---------------|
| 1-9   | Worker | Basic operations |
| 10-19 | Senior Worker / Team Leader | Can SUPPRESS workers, DIRECTIVE |
| 20-29 | Team Leader / Deputy Supervisor | Can ARBITRATE, SPAWN |
| 30+   | Deputy Supervisor / Supervisor-Eligible | Can TASK_COMPLETE, full authority |

## Command Authorization Matrix

| Command | Worker (1-9) | Senior (10-19) | Deputy (20-29) | Supervisor (30+) |
|---------|--------------|----------------|----------------|------------------|
| `BROADCAST:FINDING` | ✓ | ✓ | ✓ | ✓ |
| `XP_VOTE` (max) | +10 | +15 | +20 | +25 |
| `AGENT_BREAK_REQUEST` | ✓ | ✓ | ✓ | ✓ |
| `AGENT_PASS_TURN` | ✓ | ✓ | ✓ | ✓ |
| `DIRECTIVE` | ✗ | ✓ | ✓ | ✓ |
| `SUPPRESS:@worker` | ✗ | ✓ | ✓ | ✓ |
| `SUPPRESS:@senior` | ✗ | ✗ | ✓ | ✓ |
| `ARBITRATE` | ✗ | ✗ | ✓ | ✓ |
| `SPAWN` | ✗ | ✗ | ✓ | ✓ |
| `SUPPRESS:@any` | ✗ | ✗ | ✗ | ✓ |
| `AGENT_TASK_COMPLETE` | ✗ | ✗ | ✗ | ✓ |
| `AGENT_EMERGENCY` | ✗ | ✗ | ✗ | ✓ |

## Quick Code Examples

### Get Agent Privileges
```python
from core.privilege_mapping import get_privileges_for_level

priv = get_privileges_for_level(15)
print(priv['title'])        # "Senior Worker / Team Leader"
print(priv['authorities'])  # List of what they can do
print(priv['restrictions']) # List of what they cannot do
```

### Format for Prompt
```python
from core.privilege_mapping import format_privileges_for_prompt

prompt = format_privileges_for_prompt(15, '@llama')
# Returns formatted string with all privilege info
```

### Validate Command
```python
from core.privilege_mapping import validate_command

is_valid, reason = validate_command(15, '[[SUPPRESS:@worker:reason]]')
# Returns: (True, 'Authorized')
```

### Check Next Promotion
```python
from core.privilege_mapping import get_next_promotion

next_level, next_title = get_next_promotion(15)
# Returns: (20, "Team Leader")
```

## Configuration

Enable/disable in `core/constants.py`:
```python
PRIVILEGE_PROMPT_SECTION = True  # Show privileges in prompts
PRIVILEGE_VALIDATION = True      # Validate commands
```

## Level Milestones

- Level 10 (1000 XP): Senior Worker
- Level 20 (5000 XP): Team Leader  
- Level 30 (15000 XP): Deputy Supervisor
- Level 40 (30000 XP): Supervisor-Eligible

## Testing

```bash
# Run tests
python3 tests/test_privilege_mapping.py

# Run demo
python3 demo_privilege_mapping.py
```

## Files

- `core/privilege_mapping.py` - Core implementation
- `core/constants.py` - Configuration constants
- `axe.py` - Prompt integration
- `tests/test_privilege_mapping.py` - Test suite
- `docs/privilege_mapping.md` - Full documentation

## Theory

Based on Herbert Simon's *Sciences of the Artificial* (1969):
- **Clear Boundaries**: Each level has explicit scope
- **Stable Sub-assemblies**: Changes don't cascade
- **Explicit Interfaces**: Commands define inter-level communication
- **Bounded Rationality**: Restrictions prevent overreach
