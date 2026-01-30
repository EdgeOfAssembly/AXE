"""
AXE Managers Module
Contains management systems for agent lifecycle, breaks, spawning, and emergency communication.
"""
from .sleep_manager import SleepManager
from .break_system import BreakSystem
from .dynamic_spawner import DynamicSpawner
from .emergency_mailbox import EmergencyMailbox
__all__ = [
    'SleepManager',
    'BreakSystem',
    'DynamicSpawner',
    'EmergencyMailbox',
]