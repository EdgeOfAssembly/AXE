"""
Experience point (XP) calculation and award system.
Implements hybrid linear/exponential progression curve.
"""

# Constants
XP_PER_LEVEL_LINEAR = 100  # XP per level for levels 1-10


def calculate_xp_for_level(level: int) -> int:
    """Calculate total XP required to reach a given level."""
    if level <= 1:
        return 0
    
    total_xp = 0
    for lvl in range(2, level + 1):
        if lvl <= 10:
            # Linear progression for levels 1-10
            total_xp += XP_PER_LEVEL_LINEAR
        elif lvl <= 20:
            # Mildly increasing for levels 11-20
            total_xp += 150 + (lvl - 11) * 15
        else:
            # Exponential for levels 21+
            total_xp += int(500 * (1.3 ** (lvl - 21)))
    
    return total_xp


# XP Awards for various activities
XP_AWARDS = {
    # Workshop tool usage
    'workshop_chisel': 25,      # Symbolic execution
    'workshop_saw': 20,         # Taint analysis
    'workshop_plane': 15,       # Source/sink enumeration
    'workshop_hammer': 30,      # Live instrumentation
    
    # Analysis quality bonuses
    'workshop_vulnerability_found': 50,  # Finding a real vulnerability
    'workshop_clean_analysis': 10,       # Successful analysis with no errors
    
    # Multi-agent collaboration
    'agent_collaboration': 15,
    'task_completion': 20,
    
    # Code quality
    'code_review': 10,
    'bug_fix': 25,
    
    # Peer voting (Minsky's Society of Mind)
    'peer_endorsement': 10,             # Endorsed by another agent
    'peer_strong_endorsement': 20,      # Strong endorsement from Team Leader+
    'peer_penalty': -5,                 # Penalized (limited to prevent abuse)
    
    # Conflict resolution and arbitration (Minsky's cross-exclusion)
    'conflict_resolution': 15,          # Successfully resolved a conflict (PR #55 value)
    'arbitration_win': 25,              # Won an arbitration decision (PR #55 value)
    'arbitration_conducted': 20,        # Successfully arbitrated a conflict (PR #56)
    'conflict_detected': 10,            # Detecting a valid conflict (PR #56)
    
    # Default awards
    'message_processed': 1,
    'command_executed': 5,
}


def award_xp_for_activity(activity: str, quality_multiplier: float = 1.0) -> int:
    """
    Calculate XP award for a specific activity.
    
    Args:
        activity: Activity name (key from XP_AWARDS)
        quality_multiplier: Multiplier for analysis quality (0.5 to 2.0)
        
    Returns:
        XP points to award
    """
    base_xp = XP_AWARDS.get(activity, 0)
    return int(base_xp * quality_multiplier)


def get_workshop_xp_bonus(results: dict, tool_name: str) -> int:
    """
    Calculate XP bonus based on workshop analysis results.
    
    Args:
        results: Analysis results dictionary
        tool_name: Name of the workshop tool
        
    Returns:
        Bonus XP points
    """
    bonus = 0
    
    if tool_name == 'chisel':
        # Bonus for finding vulnerabilities
        vulnerabilities = results.get('vulnerabilities', [])
        bonus += len(vulnerabilities) * 10
        
        # Bonus for exploring many paths
        paths = results.get('found_paths', 0)
        bonus += min(paths // 10, 20)  # Max 20 XP for path exploration
        
    elif tool_name == 'saw':
        # Bonus for finding taint flows
        flows = results.get('taint_flows', [])
        bonus += len(flows) * 15
        
        # Bonus for vulnerabilities
        vulnerabilities = results.get('vulnerabilities', [])
        bonus += len(vulnerabilities) * 25
        
    elif tool_name == 'plane':
        # Bonus for comprehensive enumeration
        sources = results.get('sources', [])
        sinks = results.get('sinks', [])
        bonus += (len(sources) + len(sinks)) // 5  # 1 XP per 5 items
        
    elif tool_name == 'hammer':
        # Bonus for successful instrumentation
        if results.get('status') == 'running':
            bonus += 20
    
    return bonus
