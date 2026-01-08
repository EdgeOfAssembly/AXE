"""
Resource monitoring utilities for AXE.

Provides background resource monitoring and system status collection.
"""

import os
import subprocess
import threading
import time
from datetime import datetime, timezone

from .constants import RESOURCE_UPDATE_INTERVAL, RESOURCE_FILE
from utils.formatting import Colors, c


def collect_resources() -> str:
    """Collect system resource information."""
    timestamp = datetime.now(timezone.utc).isoformat()
    output = [f"--- Resource Snapshot @ {timestamp} ---"]

    try:
        # Disk usage
        output.append("\nDisk Usage (df -h):")
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
        output.append(result.stdout.strip())

        # Memory
        output.append("\nMemory (free -h):")
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        output.append(result.stdout.strip())

        # Load average
        output.append("\nLoad Average (uptime):")
        result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        output.append(result.stdout.strip())

    except Exception as e:
        output.append(f"\nError collecting resources: {e}")

    return "\n".join(output)


def resource_monitor_thread():
    """Background thread that updates the resource file periodically."""
    while True:
        try:
            resources = collect_resources()
            with open(RESOURCE_FILE, 'w') as f:
                f.write(resources)
        except Exception as e:
            # Log error but don't crash the thread
            try:
                with open(RESOURCE_FILE, 'a') as f:
                    f.write(f"\n\nError in resource monitor: {e}\n")
            except OSError:
                # If even the fallback logging fails, suppress to avoid cascading errors.
                pass

        time.sleep(RESOURCE_UPDATE_INTERVAL)


def start_resource_monitor():
    """Start the background resource monitoring thread."""
    # Clean old file if it exists
    if os.path.exists(RESOURCE_FILE):
        try:
            os.remove(RESOURCE_FILE)
        except OSError as e:
            # Log error but do not prevent the monitor from starting
            print(f"Warning: could not remove old resource file '{RESOURCE_FILE}': {e}")

    thread = threading.Thread(target=resource_monitor_thread, daemon=True)
    thread.start()
    print(c(f"Resource monitoring started → {RESOURCE_FILE}", Colors.DIM))
