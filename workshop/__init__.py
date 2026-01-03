"""
Workshop Module - Dynamic Analysis Tools for AXE

This module provides woodworking-themed dynamic analysis tools:
- Chisel: Symbolic execution for precise path analysis
- Saw: Taint analysis for data flow tracking
- Plane: Source/sink enumeration for entry/exit point cataloging
- Hammer: Live instrumentation for runtime monitoring

All tools integrate with AXE's safety and execution frameworks.
"""

def _missing_tool_factory(tool_name: str, module_name: str):
    """
    Create a stub class for an unavailable analysis tool.

    The stub raises an ImportError as soon as it is instantiated,
    providing a clear and informative error message instead of
    failing later with an AttributeError on `None`.
    """

    class _MissingTool:
        def __init__(self, *_, **__):
            raise ImportError(
                f"{tool_name} is unavailable because its dependency "
                f"module '{module_name}' could not be imported. "
                f"Install the required dependencies to use this tool."
            )

    _MissingTool.__name__ = tool_name
    return _MissingTool

# Optional imports - gracefully handle missing dependencies
try:
    from .chisel import ChiselAnalyzer
    HAS_CHISEL = True
except ImportError:
    ChiselAnalyzer = _missing_tool_factory("ChiselAnalyzer", "workshop.chisel")
    HAS_CHISEL = False

try:
    from .saw import SawTracker
    HAS_SAW = True
except ImportError:
    SawTracker = _missing_tool_factory("SawTracker", "workshop.saw")
    HAS_SAW = False

try:
    from .plane import PlaneEnumerator
    HAS_PLANE = True
except ImportError:
    PlaneEnumerator = _missing_tool_factory("PlaneEnumerator", "workshop.plane")
    HAS_PLANE = False

try:
    from .hammer import HammerInstrumentor
    HAS_HAMMER = True
except ImportError:
    HammerInstrumentor = _missing_tool_factory("HammerInstrumentor", "workshop.hammer")
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