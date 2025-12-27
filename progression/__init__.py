"""
AXE Progression Module
Handles agent XP and leveling system.
"""

from .xp_system import calculate_xp_for_level
from .levels import get_title_for_level, LEVEL_MILESTONES

__all__ = ['calculate_xp_for_level', 'get_title_for_level', 'LEVEL_MILESTONES']
