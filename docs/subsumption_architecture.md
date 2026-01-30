# Subsumption Architecture Controller

Implementation of **Rodney Brooks' Subsumption Architecture (1986)** for layered agent execution in AXE.

## Overview

The Subsumption Controller organizes AXE agents into behavioral layers where:
- **Lower layers** handle basic "survival" behaviors (safety, degradation)
- **Higher layers** handle strategic planning and supervision
- **Higher layers can suppress lower layers** when needed
- **System remains robust** - lower layers continue if higher layers fail
- **No central control** - coordination emerges from layer interactions

**Reference**: Brooks, R. A. (1986). *A Robust Layered Control System for a Mobile Robot*. MIT AI Lab.

## Layer Definitions

Agents are assigned to layers based on their XP level:

| Layer | Name | XP Levels | Role |
|-------|------|-----------|------|
| 0 | **Survival** | System-level | Token limits, security, degradation |
| 1 | **Worker** | 1-9 | Basic task execution |
| 2 | **Tactical** | 10-19 | Task coordination, team management |
| 3 | **Strategic** | 20-39 | Long-term planning, resource allocation |
| 4 | **Executive** | 40+ | System-wide supervision and policy |

## Usage

### Basic Setup

```python
from core import SubsumptionController

controller = SubsumptionController()
```

### Layer Assignment

```python
# Get layer for an agent based on XP level
layer = controller.get_layer_for_level(25)  # Returns SubsumptionLayer.STRATEGIC
print(f"Agent is in layer: {layer.name} (Layer {layer.value})")
```

### Suppression

Higher-layer agents can suppress lower-layer agents:

```python
# Strategic agent suppresses worker for 3 turns
success, message = controller.suppress_agent(
    suppressor_id="@strategic",
    suppressor_level=25,
    target_id="@worker",
    target_level=5,
    reason="Strategic planning in progress",
    turns=3  # Optional, defaults to SUPPRESSION_DEFAULT_TURNS
)

if success:
    print(message)  # "✓ @strategic (L3) suppressed @worker (L1) for 3 turns..."
```

### Checking Suppression Status

```python
# Check if an agent is suppressed
if controller.is_suppressed("@worker"):
    supp_info = controller.get_suppression_info("@worker")
    print(f"Suppressed by {supp_info.suppressor_id}")
    print(f"Turns remaining: {supp_info.turns_remaining}")
    print(f"Reason: {supp_info.reason}")
```

### Manual Release

```python
# Original suppressor or higher-layer agent can release
success, message = controller.release_suppression(
    releaser_id="@strategic",
    releaser_level=25,
    target_id="@worker"
)
```

### Execution Order

```python
# Get agents sorted by layer (highest first), excluding suppressed
agents = [
    {'id': '@worker', 'level': 5},
    {'id': '@tactical', 'level': 15},
    {'id': '@executive', 'level': 40}
]

ordered = controller.get_execution_order(agents)
# Returns: [@executive, @tactical, @worker] (highest layer first)
```

### Turn Management

```python
# Call at end of each collaboration turn to decrement suppressions
expired = controller.tick_suppressions()
if expired:
    print(f"Suppressions expired for: {expired}")
```

### Prompt Formatting

```python
# Generate subsumption layer info for agent prompts
prompt_section = controller.format_for_prompt('@tactical', 15)
# Returns formatted markdown explaining:
# - Agent's layer and responsibilities
# - What layers they can suppress
# - What layers can suppress them
# - Current suppression status (if any)
```

## Agent Tokens

Agents can use special tokens in their responses to trigger suppressions:

```
[[SUPPRESS:@target_agent:reason]]  - Suppress target for 3 turns
[[RELEASE:@target_agent]]           - Release suppression
```

These tokens should be parsed by the collaboration system and converted into `suppress_agent()` and `release_suppression()` calls.

## Suppression Rules

1. **Higher layers suppress lower layers**: Executive (L4) > Strategic (L3) > Tactical (L2) > Worker (L1) > Survival (L0)
2. **Same-layer agents cannot suppress each other** (prevents conflicts)
3. **Lower layers cannot suppress higher layers**
4. **Suppression duration**: Default 3 turns, maximum 10 turns
5. **Release permission**: Only original suppressor or higher-layer agents can release

## Integration with GlobalWorkspace

The controller supports optional GlobalWorkspace integration (from PR #38):

```python
# Set GlobalWorkspace instance for broadcasting suppression events
controller.set_global_workspace(workspace)

# Events are broadcast as STATUS category:
# - suppression_created
# - suppression_released  
# - suppression_expired
```

If GlobalWorkspace is not available, the controller works standalone without errors.

## Examples

### Example 1: Strategic Planning

```python
controller = SubsumptionController()

# Strategic agent needs workers to pause while planning
controller.suppress_agent('@strategic', 25, '@worker1', 5, 
                         "Strategic planning requires worker pause")
controller.suppress_agent('@strategic', 25, '@worker2', 7,
                         "Strategic planning requires worker pause")

# Get execution order - workers are excluded
active_agents = controller.get_execution_order(all_agents)
# Only strategic and tactical agents execute

# After 3 turns, suppressions expire automatically
controller.tick_suppressions()
controller.tick_suppressions()
expired = controller.tick_suppressions()  # ['@worker1', '@worker2']
```

### Example 2: Emergency Override

```python
# Executive agent takes control in emergency
controller.suppress_agent('@executive', 42, '@strategic', 25,
                         "Emergency situation - executive override")
controller.suppress_agent('@executive', 42, '@tactical', 15,
                         "Emergency situation - executive override")

# Only executive and workers execute
# Executive can release early when emergency is over
controller.release_suppression('@executive', 42, '@strategic')
controller.release_suppression('@executive', 42, '@tactical')
```

## Testing

Run the comprehensive test suite:

```bash
python3 tests/test_subsumption.py
```

Run the interactive demonstration:

```bash
python3 demo_subsumption.py
```

## Constants

Defined in `core/constants.py`:

```python
SUPPRESSION_DEFAULT_TURNS = 3   # Default suppression duration
SUPPRESSION_MAX_TURNS = 10      # Maximum allowed duration
AGENT_TOKEN_SUPPRESS = "[[SUPPRESS:"
AGENT_TOKEN_RELEASE = "[[RELEASE:"
```

## Architecture Benefits

1. **Robustness**: Lower layers continue functioning if higher layers fail
2. **Graceful Degradation**: System adapts to agent failures
3. **Emergent Coordination**: No central planner needed
4. **Clear Authority**: Layer hierarchy prevents conflicts
5. **Flexible Control**: Higher layers can temporarily take control when needed

## References

- Brooks, R. A. (1986). *A Robust Layered Control System for a Mobile Robot*. MIT AI Lab.
- AXE Progression System: `progression/levels.py`
- Agent Communication Tokens: `core/constants.py`
