"""
Workshop Module - Dynamic Analysis Tools for AXE

This module provides woodworking-themed dynamic analysis tools:
- Chisel: Symbolic execution for precise path analysis
- Saw: Taint analysis for data flow tracking
- Plane: Source/sink enumeration for entry/exit point cataloging
- Hammer: Live instrumentation for runtime monitoring

All tools integrate with AXE's safety and execution frameworks.
"""

from .chisel import ChiselAnalyzer
from .saw import SawTracker
from .plane import PlaneEnumerator
from .hammer import HammerInstrumentor

__all__ = [
    'ChiselAnalyzer',
    'SawTracker',
    'PlaneEnumerator',
    'HammerInstrumentor'
]