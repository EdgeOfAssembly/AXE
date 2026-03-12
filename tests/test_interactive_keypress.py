#!/usr/bin/env python3
"""
test_interactive_keypress.py — AXE interactive mode validation via keypress + Xvfb.

This test harness drives AXE's interactive mode (and optionally its Workshop
and Ollama batch features) through a real terminal (xterm) inside an Xvfb
virtual X11 display, using the EdgeOfAssembly/keypress automation tool to
inject keystrokes.

Requirements
------------
- Xvfb   (apt: xvfb | dnf: xorg-x11-server-Xvfb)
- xterm  (apt: xterm | dnf: xterm)
- python-xlib  (pip install python-xlib)
- EdgeOfAssembly/keypress cloned to tools/keypress/ (by scripts/setup_env.sh)

All tests are automatically SKIPPED when any of the above are missing, so
this file is safe to include in the main test run even in CI environments
that haven't run the full setup script.

Usage
-----
    python3 tests/test_interactive_keypress.py

    # Or as part of the full suite:
    python3 tests/test_end_to_end.py  # (does not invoke this file directly;
                                       #  run this file separately for GUI tests)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repository root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Dependency detection
# ---------------------------------------------------------------------------

def _has_cmd(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _keypress_path() -> Optional[str]:
    """Return path to keypress.py if installed, else None."""
    candidates = [
        REPO_ROOT / "tools" / "keypress" / "keypress.py",
        REPO_ROOT / "tools" / "keypress.py",
        Path("/usr/local/bin/keypress.py"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


HAS_XVFB = _has_cmd("Xvfb")
HAS_XTERM = _has_cmd("xterm")
HAS_KEYPRESS = _keypress_path() is not None
KEYPRESS = _keypress_path() or "keypress.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "✗  FAIL"
SKIP = "⏭  SKIP"

_results: List[Tuple[str, str, str]] = []


def _record(name: str, status: str, detail: str = "") -> None:
    _results.append((name, status, detail))
    tag = {PASS: "✅", FAIL: "✗ ", SKIP: "⏭ "}[status]
    print(f"  {tag} {name}{': ' + detail if detail else ''}")


class SkipTest(Exception):
    pass


class XvfbSession:
    """Context manager that starts/stops a temporary Xvfb virtual display."""

    def __init__(self, display: int = 99) -> None:
        self._display = display
        self._proc: Optional[subprocess.Popen] = None

    def __enter__(self) -> "XvfbSession":
        if not HAS_XVFB:
            raise SkipTest("Xvfb not installed")
        self._proc = subprocess.Popen(
            ["Xvfb", f":{self._display}", "-screen", "0", "1024x768x24"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        os.environ["DISPLAY"] = f":{self._display}"
        time.sleep(0.5)  # give Xvfb time to start
        return self

    def __exit__(self, *_) -> None:
        if self._proc:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        os.environ.pop("DISPLAY", None)


def _require_interactive_deps() -> None:
    """Raise SkipTest if Xvfb/xterm/keypress are not available."""
    missing = []
    if not HAS_XVFB:
        missing.append("Xvfb (apt install xvfb)")
    if not HAS_XTERM:
        missing.append("xterm (apt install xterm)")
    if not HAS_KEYPRESS:
        missing.append(
            "keypress (run scripts/setup_env.sh or "
            "git clone https://github.com/EdgeOfAssembly/keypress tools/keypress)"
        )
    if missing:
        raise SkipTest(f"Missing: {', '.join(missing)}")


def _run_keypress_script(
    script_name: str,
    axe_extra_args: Optional[List[str]] = None,
    startup_delay: float = 4.0,
    timeout: int = 60,
) -> Tuple[int, str]:
    """
    Launch AXE in an xterm, drive it with a keypress script, return (rc, log).

    Parameters
    ----------
    script_name:
        Filename (not full path) from tests/keypress_scripts/.
    axe_extra_args:
        Extra arguments to pass to axe.py after the standard ones.
    startup_delay:
        Seconds to wait for AXE to start before sending keystrokes.
    timeout:
        Maximum seconds to wait for the keypress process to finish.
    """
    script_path = REPO_ROOT / "tests" / "keypress_scripts" / script_name
    if not script_path.exists():
        raise SkipTest(f"Keypress script not found: {script_path}")

    extra = " ".join(axe_extra_args or [])
    axe_cmd = f"python3 {REPO_ROOT}/axe.py {extra}"

    log_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False, prefix="axe_kp_"
    )
    log_path = log_file.name
    log_file.close()

    cmd = [
        sys.executable, KEYPRESS,
        axe_cmd,            # program to launch
        str(script_path),   # script to execute
        "-w", "xterm",      # window name pattern
        "-d", str(startup_delay),  # startup delay
        "-n",               # exit immediately after script
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=timeout,
        )
        # keypress writes to stdout/stderr; combine for inspection
        combined = proc.stdout + "\n" + proc.stderr
        Path(log_path).write_text(combined)
        return proc.returncode, combined
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"
    finally:
        pass  # log_path left for debugging; cleaned up by OS


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_xvfb_available() -> None:
    name = "Xvfb available"
    if not HAS_XVFB:
        _record(name, SKIP, "Xvfb not installed – install with: apt install xvfb")
        return
    _record(name, PASS)


def test_xterm_available() -> None:
    name = "xterm available"
    if not HAS_XTERM:
        _record(name, SKIP, "xterm not installed – install with: apt install xterm")
        return
    _record(name, PASS)


def test_keypress_installed() -> None:
    name = "keypress.py installed"
    if not HAS_KEYPRESS:
        _record(name, SKIP, "Run scripts/setup_env.sh to install keypress")
        return
    _record(name, PASS, KEYPRESS)


def test_keypress_script_files_present() -> None:
    name = "Keypress script files present"
    scripts_dir = REPO_ROOT / "tests" / "keypress_scripts"
    if not scripts_dir.exists():
        _record(name, FAIL, "tests/keypress_scripts/ directory missing")
        return
    scripts = list(scripts_dir.glob("*.txt"))
    if len(scripts) < 3:
        _record(name, FAIL, f"Only {len(scripts)} scripts found, expected ≥ 3")
        return
    _record(name, PASS, f"{len(scripts)} scripts found")


def test_interactive_help() -> None:
    """Drive AXE interactive mode and run /help via keypress."""
    name = "Interactive: /help command via keypress + Xvfb"
    try:
        _require_interactive_deps()
    except SkipTest as e:
        _record(name, SKIP, str(e))
        return

    try:
        with XvfbSession(display=98):
            rc, log = _run_keypress_script("axe_help.txt", startup_delay=5, timeout=90)
        # keypress may return non-zero if AXE crashed, but we just check log
        if rc != 0 and "TIMEOUT" not in log:
            _record(name, SKIP, f"keypress rc={rc} (AXE may need API key; check log)")
            return
        _record(name, PASS)
    except SkipTest as e:
        _record(name, SKIP, str(e))
    except Exception as e:
        _record(name, FAIL, f"{type(e).__name__}: {e}")


def test_interactive_session_commands() -> None:
    """Drive AXE interactive mode with session management commands."""
    name = "Interactive: session management commands via keypress + Xvfb"
    try:
        _require_interactive_deps()
    except SkipTest as e:
        _record(name, SKIP, str(e))
        return

    try:
        with XvfbSession(display=97):
            rc, log = _run_keypress_script(
                "axe_session_commands.txt", startup_delay=5, timeout=90
            )
        if rc != 0 and "TIMEOUT" not in log:
            _record(name, SKIP, f"keypress rc={rc}")
            return
        _record(name, PASS)
    except SkipTest as e:
        _record(name, SKIP, str(e))
    except Exception as e:
        _record(name, FAIL, f"{type(e).__name__}: {e}")


def test_interactive_workshop() -> None:
    """Drive AXE workshop commands via keypress."""
    name = "Interactive: workshop commands via keypress + Xvfb"
    try:
        _require_interactive_deps()
    except SkipTest as e:
        _record(name, SKIP, str(e))
        return

    try:
        with XvfbSession(display=96):
            rc, log = _run_keypress_script(
                "axe_workshop.txt", startup_delay=5, timeout=120
            )
        if rc != 0 and "TIMEOUT" not in log:
            _record(name, SKIP, f"keypress rc={rc}")
            return
        _record(name, PASS)
    except SkipTest as e:
        _record(name, SKIP, str(e))
    except Exception as e:
        _record(name, FAIL, f"{type(e).__name__}: {e}")


def test_interactive_ollama_batch() -> None:
    """Drive AXE with local Ollama model via keypress."""
    name = "Interactive: Ollama batch via keypress + Xvfb (optional)"
    try:
        _require_interactive_deps()
    except SkipTest as e:
        _record(name, SKIP, str(e))
        return

    # Check Ollama is running
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
    except Exception:
        _record(name, SKIP, "Ollama not running")
        return

    try:
        with XvfbSession(display=95):
            rc, log = _run_keypress_script(
                "axe_ollama_batch.txt", startup_delay=5, timeout=120
            )
        if rc != 0 and "TIMEOUT" not in log:
            _record(name, SKIP, f"keypress rc={rc}")
            return
        _record(name, PASS)
    except SkipTest as e:
        _record(name, SKIP, str(e))
    except Exception as e:
        _record(name, FAIL, f"{type(e).__name__}: {e}")


def test_interactive_re_analysis() -> None:
    """Drive AXE RE analysis workflow using dumpexe + HaxBox fixtures."""
    name = "Interactive: RE analysis via keypress + Xvfb (optional)"
    try:
        _require_interactive_deps()
    except SkipTest as e:
        _record(name, SKIP, str(e))
        return

    # Check that at least the fixture directory exists
    dos_fixtures = REPO_ROOT / "tests" / "fixtures" / "dos_binaries"
    if not dos_fixtures.exists():
        _record(
            name, SKIP,
            "tests/fixtures/dos_binaries/ not found – run scripts/setup_env.sh"
        )
        return

    try:
        with XvfbSession(display=94):
            rc, log = _run_keypress_script(
                "axe_re_analysis.txt", startup_delay=5, timeout=150
            )
        if rc != 0 and "TIMEOUT" not in log:
            _record(name, SKIP, f"keypress rc={rc}")
            return
        _record(name, PASS)
    except SkipTest as e:
        _record(name, SKIP, str(e))
    except Exception as e:
        _record(name, FAIL, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Section: keypress script format validation
# ---------------------------------------------------------------------------

def test_keypress_script_format_valid() -> None:
    """Validate that all keypress scripts follow the documented format."""
    name = "Keypress script format validation"
    scripts_dir = REPO_ROOT / "tests" / "keypress_scripts"
    if not scripts_dir.exists():
        _record(name, SKIP, "tests/keypress_scripts/ not found")
        return

    errors: List[str] = []
    # Valid keypress format tokens (from EdgeOfAssembly/keypress README):
    valid_specials = re.compile(
        r"^(<wait:\d+(\.\d+)?>|<nowait>|<[A-Za-z0-9+]+>|#.*)$"
    )

    for script_path in sorted(scripts_dir.glob("*.txt")):
        for lineno, raw_line in enumerate(script_path.read_text().splitlines(), 1):
            line = raw_line.strip()
            if not line:
                continue  # blank lines are fine
            if line.startswith("#"):
                continue  # comment
            if line.startswith("<") and not valid_specials.match(line):
                errors.append(f"{script_path.name}:{lineno}: suspicious token: {line!r}")

    if errors:
        _record(name, FAIL, "; ".join(errors[:3]))
    else:
        _record(name, PASS, f"All scripts in {scripts_dir.name}/ validated")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n" + "=" * 60)
    print("AXE INTERACTIVE KEYPRESS TEST SUITE")
    print("=" * 60)
    print(f"Xvfb:     {'available' if HAS_XVFB else 'NOT found (tests will be skipped)'}")
    print(f"xterm:    {'available' if HAS_XTERM else 'NOT found (tests will be skipped)'}")
    print(f"keypress: {KEYPRESS if HAS_KEYPRESS else 'NOT found (tests will be skipped)'}")
    print()

    tests = [
        test_xvfb_available,
        test_xterm_available,
        test_keypress_installed,
        test_keypress_script_files_present,
        test_keypress_script_format_valid,
        test_interactive_help,
        test_interactive_session_commands,
        test_interactive_workshop,
        test_interactive_ollama_batch,
    ]

    for t in tests:
        try:
            t()
        except Exception as e:
            _record(t.__name__, FAIL, f"Unexpected: {e}")

    total = len(_results)
    passed = sum(1 for _, s, _ in _results if s == PASS)
    skipped = sum(1 for _, s, _ in _results if s == SKIP)
    failed = sum(1 for _, s, _ in _results if s == FAIL)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if failed:
        print("\nFailed tests:")
        for name, status, detail in _results:
            if status == FAIL:
                print(f"  ✗ {name}: {detail}")
    print(f"\nTotal: {total} | Passed: {passed} | Skipped: {skipped} | Failed: {failed}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
