"""
Workshop Module - Dynamic Analysis Tools for AXE

This module provides woodworking-themed dynamic analysis tools:
- Chisel: Symbolic execution for precise path analysis
- Saw: Taint analysis for data flow tracking
- Plane: Source/sink enumeration for entry/exit point cataloging
- Hammer: Live instrumentation for runtime monitoring

All tools integrate with AXE's safety and execution frameworks.
"""

# Optional imports - gracefully handle missing dependencies
try:
    from .chisel import ChiselAnalyzer
    HAS_CHISEL = True
except ImportError:
    ChiselAnalyzer = None
    HAS_CHISEL = False

try:
    from .saw import SawTracker
    HAS_SAW = True
except ImportError:
    SawTracker = None
    HAS_SAW = False

try:
    from .plane import PlaneEnumerator
    HAS_PLANE = True
except ImportError:
    PlaneEnumerator = None
    HAS_PLANE = False

try:
    from .hammer import HammerInstrumentor
    HAS_HAMMER = True
except ImportError:
    HammerInstrumentor = None
    HAS_HAMMER = False

__all__ = [
    'ChiselAnalyzer',
    'SawTracker',
    'PlaneEnumerator',
    'HammerInstrumentor',
    'HAS_CHISEL',
    'HAS_SAW',
    'HAS_PLANE',
    'HAS_HAMMER'
]