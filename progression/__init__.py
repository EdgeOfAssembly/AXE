"""
AXE Progression Module
Handles agent XP and leveling system.
"""

from .xp_system import calculate_xp_for_level
from .levels import (
    get_title_for_level,
    LEVEL_MILESTONES,
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER,
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE,
)

__all__ = [
    'calculate_xp_for_level',
    'get_title_for_level',
    'LEVEL_MILESTONES',
    'LEVEL_SENIOR_WORKER',
    'LEVEL_TEAM_LEADER',
    'LEVEL_DEPUTY_SUPERVISOR',
    'LEVEL_SUPERVISOR_ELIGIBLE',
]
