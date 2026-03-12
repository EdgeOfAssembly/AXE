#!/usr/bin/env python3
"""
hello_world.py – simple Python fixture used by AXE feature-validation tests.

Purpose: provide a small, well-structured Python module that AXE agents can
read, analyse, and review during automated testing.  Covers type hints,
docstrings, dataclasses, and simple I/O – features agents are expected to
understand and comment on correctly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Entry:
    """A simple key/value entry."""

    key: str
    value: int


def populate(n: int) -> List[Entry]:
    """
    Create a list of *n* entries with sequential squared values.

    Args:
        n: Number of entries to create.

    Returns:
        List of Entry objects.
    """
    return [Entry(key=f"item_{i}", value=i * i) for i in range(n)]


def print_entries(entries: List[Entry]) -> None:
    """Print each entry to stdout."""
    for entry in entries:
        print(f"{entry.key} = {entry.value}")


def main() -> None:
    entries = populate(5)
    print_entries(entries)


if __name__ == "__main__":
    main()
