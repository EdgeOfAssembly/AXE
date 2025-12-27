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
