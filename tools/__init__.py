"""
AXE Analysis Tools

This package contains analysis tools for codebase preparation and build system detection:
- llmprep: Generates LLM-friendly codebase context
- build_analyzer: Detects and analyzes build systems
- minifier: Minifies source code to reduce token usage
"""

__version__ = "1.0.0"

from .minifier import Minifier, minify_file, minify_directory
