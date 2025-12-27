"""
Terminal formatting utilities for AXE multiagent system.
Handles banners, colors, tables, and visual displays.
"""

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def colorize(text: str, color: str) -> str:
    """Colorize text for terminal output."""
    return f"{color}{text}{Colors.END}"


# Short alias for convenience
c = colorize
