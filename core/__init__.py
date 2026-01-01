"""
Core module for AXE - multiprocessing and coordination.
"""

from .multiprocess import AgentWorkerProcess, MultiAgentCoordinator, SharedContext

__all__ = ['AgentWorkerProcess', 'MultiAgentCoordinator', 'SharedContext']
