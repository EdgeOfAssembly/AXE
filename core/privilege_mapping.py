"""
Level-to-Privilege Mapping for AXE agents.
Implements Simon's nearly-decomposable hierarchies (1969).

Each level has explicit:
- Responsibilities (what they should focus on)
- Authorities (what they can do)
- Restrictions (what they cannot do)
- Commands (level-gated actions)

Reference: Simon, H.A. (1969). The Sciences of the Artificial. MIT Press.
"""

from typing import Dict, Any, Tuple, Optional
from progression.levels import (
    LEVEL_SENIOR_WORKER, LEVEL_TEAM_LEADER, 
    LEVEL_DEPUTY_SUPERVISOR, LEVEL_SUPERVISOR_ELIGIBLE
)

# Comprehensive privilege definitions by level range
PRIVILEGE_MAPPING = {
    'worker': {
        'level_range': (1, 9),
        'title': 'Worker',
        'responsibilities': [
            'Execute assigned tasks thoroughly',
            'Report findings via broadcasts',
            'Ask questions when uncertain',
            'Collaborate with peers',
        ],
        'authorities': [
            'Broadcast FINDING, BUG, SECURITY, OPTIMIZATION, STATUS',
            'Vote XP for peers (+10 max)',
            'Request breaks',
            'Use all workshop tools',
        ],
        'restrictions': [
            'Cannot broadcast DIRECTIVE',
            'Cannot suppress other agents',
            'Cannot declare TASK COMPLETE',
            'Cannot arbitrate conflicts',
        ],
        'commands': [
            '[[BROADCAST:CATEGORY:message]]',
            '[[XP_VOTE:+N:@agent:reason]]',
            '[[AGENT_BREAK_REQUEST:type:reason]]',
            '[[AGENT_PASS_TURN]]',
        ],
    },
    
    'senior_worker': {
        'level_range': (10, 19),
        'title': 'Senior Worker',
        'responsibilities': [
            'Guide junior workers',
            'Review peer contributions',
            'Prioritize subtasks',
            'Mentor new agents',
        ],
        'authorities': [
            'All Worker authorities PLUS:',
            'Broadcast DIRECTIVE to workers (planned)',
            'Suppress Worker-level agents (planned)',
            'Vote XP (+15 max)',
            'Priority turn initiative',
        ],
        'restrictions': [
            'Cannot suppress Senior+ agents',
            'Cannot declare TASK COMPLETE alone',
            'Cannot override Deputy decisions',
        ],
        'commands': [
            '[[SUPPRESS:@worker:reason]] (planned - 3 turns)',
            '[[DIRECTIVE:instruction]] (planned)',
            '[[XP_VOTE:+15:@agent:reason]]',
        ],
    },
    
    'deputy': {
        'level_range': (20, 29),
        'title': 'Team Leader',
        'responsibilities': [
            'Coordinate multiple sub-teams',
            'Resolve conflicts between workers',
            'Allocate resources',
            'Report to Supervisor',
        ],
        'authorities': [
            'All Senior authorities PLUS:',
            'Suppress Senior-level agents (planned)',
            'Arbitrate Worker/Senior conflicts (planned)',
            'Spawn sub-sessions (planned)',
            'Vote XP (+20 max, -10 penalty)',
        ],
        'restrictions': [
            'Cannot suppress Supervisors',
            'Cannot override Supervisor decisions',
            'TASK COMPLETE requires Supervisor approval',
        ],
        'commands': [
            '[[SUPPRESS:@senior:reason]] (planned)',
            '[[ARBITRATE:arb_id:resolution:winner]] (planned)',
            '[[SPAWN:model:role:reason]] (planned)',
            '[[XP_VOTE:+20:@agent:reason]]',
        ],
    },
    
    'supervisor': {
        'level_range': (30, 50),
        'title': 'Deputy Supervisor',
        'responsibilities': [
            'Overall session success',
            'Final quality control',
            'Emergency decisions',
            'Human communication',
        ],
        'authorities': [
            'All Deputy authorities PLUS:',
            'Suppress any agent (planned)',
            'Declare TASK COMPLETE',
            'Final arbitration authority (planned)',
            'Emergency human escalation',
            'Vote XP (+25 max, -15 penalty)',
        ],
        'restrictions': [
            'Must justify major decisions',
            'Cannot ignore safety violations',
            'Must respect human overrides',
        ],
        'commands': [
            '[[SUPPRESS:@any:reason]] (planned)',
            '[[AGENT_TASK_COMPLETE:summary]]',
            '[[AGENT_EMERGENCY:message]]',
            '[[XP_VOTE:+25:@agent:reason]]',
        ],
    },
}


def get_privileges_for_level(level: int) -> Dict[str, Any]:
    """Get privilege mapping for a specific level."""
    if level >= LEVEL_DEPUTY_SUPERVISOR:  # 30+
        return PRIVILEGE_MAPPING['supervisor']
    elif level >= LEVEL_TEAM_LEADER:  # 20-29
        return PRIVILEGE_MAPPING['deputy']
    elif level >= LEVEL_SENIOR_WORKER:  # 10-19
        return PRIVILEGE_MAPPING['senior_worker']
    else:  # 1-9
        return PRIVILEGE_MAPPING['worker']


def _get_all_inherited_commands(level: int) -> list:
    """Get all commands available to an agent including inherited commands from lower tiers."""
    all_commands = []
    
    # Always include worker commands
    all_commands.extend(PRIVILEGE_MAPPING['worker']['commands'])
    
    # Add senior worker commands if level >= 10
    if level >= LEVEL_SENIOR_WORKER:
        all_commands.extend(PRIVILEGE_MAPPING['senior_worker']['commands'])
    
    # Add deputy commands if level >= 20
    if level >= LEVEL_TEAM_LEADER:
        all_commands.extend(PRIVILEGE_MAPPING['deputy']['commands'])
    
    # Add supervisor commands if level >= 30
    if level >= LEVEL_DEPUTY_SUPERVISOR:
        all_commands.extend(PRIVILEGE_MAPPING['supervisor']['commands'])
    
    return all_commands


def format_privileges_for_prompt(level: int, agent_alias: str) -> str:
    """
    Format privilege information for injection into agent prompts.
    
    Args:
        level: Agent's current level
        agent_alias: Agent's alias for personalization
    
    Returns:
        Formatted string explaining privileges
    """
    priv = get_privileges_for_level(level)
    
    lines = [
        f"## YOUR ROLE: {priv['title']} (Level {level})",
        f"Agent: {agent_alias}",
        "",
        "### RESPONSIBILITIES",
    ]
    for r in priv['responsibilities']:
        lines.append(f"- {r}")
    
    lines.append("\n### AUTHORITIES (What You CAN Do)")
    for a in priv['authorities']:
        lines.append(f"- {a}")
    
    lines.append("\n### RESTRICTIONS (What You CANNOT Do)")
    for r in priv['restrictions']:
        lines.append(f"- ⚠️ {r}")
    
    lines.append("\n### AVAILABLE COMMANDS")
    for c in priv['commands']:
        lines.append(f"  {c}")
    
    # Add promotion info
    next_level, next_title = get_next_promotion(level)
    if next_level:
        lines.append(f"\n### NEXT PROMOTION")
        lines.append(f"Reach level {next_level} to become **{next_title}**")
        lines.append(f"New abilities: {get_promotion_preview(next_level)}")
    
    return "\n".join(lines)


def get_next_promotion(level: int) -> Tuple[Optional[int], Optional[str]]:
    """Get next promotion level and title."""
    if level < LEVEL_SENIOR_WORKER:
        return LEVEL_SENIOR_WORKER, "Senior Worker"
    elif level < LEVEL_TEAM_LEADER:
        return LEVEL_TEAM_LEADER, "Team Leader"
    elif level < LEVEL_DEPUTY_SUPERVISOR:
        return LEVEL_DEPUTY_SUPERVISOR, "Deputy Supervisor"
    elif level < LEVEL_SUPERVISOR_ELIGIBLE:
        return LEVEL_SUPERVISOR_ELIGIBLE, "Supervisor-Eligible"
    return None, None


def get_promotion_preview(next_level: int) -> str:
    """Get preview of abilities gained at next level."""
    previews = {
        10: "DIRECTIVE broadcasts, suppress workers, +15 XP votes",
        20: "Arbitration authority, spawn sub-sessions, +20 XP votes",
        30: "TASK COMPLETE authority, suppress any agent, emergency escalation",
        40: "Full supervisor privileges",
    }
    return previews.get(next_level, "Enhanced capabilities")


def validate_command(level: int, command: str) -> Tuple[bool, str]:
    """
    Validate if an agent can use a command at their level.
    Includes inherited commands from lower tiers.
    
    Returns:
        (is_valid, reason)
    """
    # Get all commands available to this level (including inherited)
    allowed_commands = _get_all_inherited_commands(level)
    
    # Extract command type from token
    if ':' in command:
        command_type = command.split(':')[0] + ':'
    else:
        command_type = command
    
    for allowed in allowed_commands:
        # Check if command matches (ignoring "(planned)" suffix)
        allowed_base = allowed.split(' (planned')[0]
        if allowed_base.startswith(command_type) or command_type in allowed_base:
            # Check if command is marked as planned
            if '(planned' in allowed:
                return False, f"Command not yet implemented (planned for future). Your level: {level}"
            return True, "Authorized"
    
    return False, f"Command requires higher level. Your level: {level}"
