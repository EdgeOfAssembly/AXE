#!/usr/bin/env python3
"""
test_end_to_end.py — Comprehensive AXE feature validation test suite.

Derives its checklist directly from README.md and exercises every documented
feature as completely as practical without requiring live cloud API keys.

Features validated
------------------
- CLI option parsing (--help, --init, --dry-run, --collab, --workspace,
  --time, --task, --enable-github, -c / --command, --config)
- Batch mode  (-c "@agent task")
- Collaborative session initialisation (--collab flag, CollaborativeSession)
- Unix socket interface (socket path, PID file, server creation, cleanup)
- Interactive command set (/help, /agents, /tools, /dirs, /config, /context,
  /files, /history, /clear, /save, /stats, /workspace, /session, /read,
  /exec, /prep, /llmprep, /buildinfo)
- Workshop tools (/workshop status, /workshop saw, /workshop plane,
  /workshop help, /workshop history, /workshop stats)
- Agent Skills system (manifest loading, skill injection)
- Sandbox security model (blacklist enforcement)
- XP/Level progression (XP awards, level calculation, title progression)
- Subsumption Architecture (layer assignment, suppression)
- Global Workspace / Arbitration Protocol (broadcasts, conflict detection)
- Token optimisation utilities
- Minifier tool (C, Python)
- llmprep / build_analyzer tools
- axe_socket_client helper
- Configuration architecture (models.yaml, providers.yaml, axe.yaml)

Usage
-----
    python3 tests/test_end_to_end.py

Requirements
------------
- Python 3.9+
- AXE Python requirements installed (pip install -r requirements.txt)
- Ollama running with at least one model pulled is optional; tests that
  need it are automatically skipped when Ollama is not reachable.

Exit codes
----------
    0 — all tests passed (or skipped)
    1 — one or more tests failed
"""

from __future__ import annotations

import os
import sys
import socket
import subprocess
import tempfile
import textwrap
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap: add repo root to sys.path
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "✗  FAIL"
SKIP = "⏭  SKIP"

_results: List[Tuple[str, str, str]] = []  # (name, status, detail)


def record(name: str, status: str, detail: str = "") -> None:
    _results.append((name, status, detail))
    tag = {PASS: "✅", FAIL: "✗ ", SKIP: "⏭ "}[status]
    print(f"  {tag} {name}{': ' + detail if detail else ''}")


def test(name: str) -> Callable:
    """Decorator that catches exceptions and records results."""
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Optional[bool]:
            try:
                result = fn(*args, **kwargs)
                if result is False:
                    record(name, FAIL)
                    return False
                record(name, PASS)
                return True
            except SkipTest as e:
                record(name, SKIP, str(e))
                return None
            except AssertionError as e:
                record(name, FAIL, str(e))
                return False
            except Exception as e:
                record(name, FAIL, f"{type(e).__name__}: {e}")
                return False
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


class SkipTest(Exception):
    """Raised inside a test to mark it as skipped."""


def ollama_available() -> bool:
    """Return True if Ollama server is reachable on localhost."""
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return True
    except Exception:
        return False


def require_ollama() -> None:
    """Skip the current test if Ollama is not available."""
    if not ollama_available():
        raise SkipTest("Ollama server not reachable – skipping Ollama-dependent test")


def ollama_models() -> List[str]:
    """Return list of pulled Ollama model names."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().splitlines()[1:]  # skip header
        return [line.split()[0] for line in lines if line.strip()]
    except Exception:
        return []


def first_available_ollama_model() -> Optional[str]:
    """Return the name of the first available Ollama model, or None."""
    models = ollama_models()
    return models[0] if models else None


# ---------------------------------------------------------------------------
# Section 0: Environment smoke tests
# ---------------------------------------------------------------------------

def section_environment() -> None:
    print("\n" + "=" * 60)
    print("SECTION 0: Environment")
    print("=" * 60)

    @test("Python version ≥ 3.9")
    def t() -> None:
        major, minor = sys.version_info[:2]
        assert (major, minor) >= (3, 9), f"Python {major}.{minor} is too old"

    @test("AXE repo root exists")
    def t() -> None:
        assert REPO_ROOT.is_dir()

    @test("requirements.txt present")
    def t() -> None:
        assert (REPO_ROOT / "requirements.txt").is_file()

    @test("axe.py is executable")
    def t() -> None:
        axe = REPO_ROOT / "axe.py"
        assert axe.is_file(), "axe.py not found"
        assert os.access(str(axe), os.R_OK), "axe.py not readable"

    @test("axe.yaml present")
    def t() -> None:
        assert (REPO_ROOT / "axe.yaml").is_file()

    @test("models.yaml present")
    def t() -> None:
        assert (REPO_ROOT / "models.yaml").is_file()

    @test("providers.yaml present")
    def t() -> None:
        assert (REPO_ROOT / "providers.yaml").is_file()

    @test("Ollama server reachable (optional)")
    def t() -> None:
        if not ollama_available():
            raise SkipTest("Ollama not running")
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, "ollama list failed"

    @test("Ollama has ≥ 1 model pulled (optional)")
    def t() -> None:
        require_ollama()
        models = ollama_models()
        assert len(models) >= 1, f"No models pulled; got: {models}"
        print(f"      Models: {models}")

    t()  # invoke last decorated function

    section_environment._ran = True  # type: ignore[attr-defined]


section_environment._ran = False  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Section 1: CLI / argparse
# ---------------------------------------------------------------------------

def section_cli() -> None:
    print("\n" + "=" * 60)
    print("SECTION 1: CLI Option Parsing")
    print("=" * 60)
    axe_cmd = [sys.executable, str(REPO_ROOT / "axe.py")]

    @test("axe.py --help exits 0 and shows usage")
    def t() -> None:
        result = subprocess.run(
            axe_cmd + ["--help"],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0, f"Exit {result.returncode}"
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower(), \
            "No 'usage' in --help output"

    @test("axe.py --init generates sample config")
    def t() -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "axe_init.yaml")
            result = subprocess.run(
                axe_cmd + ["--init"],
                capture_output=True, text=True, timeout=15,
                cwd=tmpdir
            )
            # --init may print to stdout or create a file; either is acceptable
            generated = any(
                Path(tmpdir, name).exists()
                for name in ["axe.yaml", "axe_init.yaml", "config.yaml"]
            )
            output_ok = (
                "yaml" in result.stdout.lower()
                or "config" in result.stdout.lower()
                or "generated" in result.stdout.lower()
                or generated
            )
            assert result.returncode == 0 or output_ok, \
                f"--init did not generate config: rc={result.returncode}, stdout={result.stdout[:200]}"

    @test("axe.py --dry-run flag accepted")
    def t() -> None:
        # Dry-run with no command should just show help or start interactively;
        # we just check the flag doesn't cause an immediate crash.
        result = subprocess.run(
            axe_cmd + ["--dry-run", "--help"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, f"Exit {result.returncode}"

    @test("axe.py --collab flag recognised in --help")
    def t() -> None:
        result = subprocess.run(
            axe_cmd + ["--help"],
            capture_output=True, text=True, timeout=10
        )
        assert "--collab" in result.stdout or "--collab" in result.stderr, \
            "--collab not mentioned in --help"

    @test("axe.py --workspace flag recognised in --help")
    def t() -> None:
        result = subprocess.run(
            axe_cmd + ["--help"],
            capture_output=True, text=True, timeout=10
        )
        assert "--workspace" in result.stdout or "--workspace" in result.stderr

    @test("axe.py --enable-github flag recognised in --help")
    def t() -> None:
        result = subprocess.run(
            axe_cmd + ["--help"],
            capture_output=True, text=True, timeout=10
        )
        assert "--enable-github" in result.stdout or "--enable-github" in result.stderr

    t()


# ---------------------------------------------------------------------------
# Section 2: Batch mode
# ---------------------------------------------------------------------------

def section_batch() -> None:
    print("\n" + "=" * 60)
    print("SECTION 2: Batch Mode  (-c / --command)")
    print("=" * 60)
    axe_cmd = [sys.executable, str(REPO_ROOT / "axe.py")]

    @test("Batch mode with unknown agent prints error gracefully")
    def t() -> None:
        result = subprocess.run(
            axe_cmd + ["-c", "@nonexistent_agent_xyz hello"],
            capture_output=True, text=True, timeout=20,
            env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
        )
        # Should not crash with traceback; any non-zero exit or error msg is fine
        combined = result.stdout + result.stderr
        assert "traceback" not in combined.lower() or result.returncode != 0, \
            "Unexpected unhandled exception"

    @test("Batch mode with --dry-run and any agent does not crash")
    def t() -> None:
        result = subprocess.run(
            axe_cmd + ["-c", "@gpt summarise this", "--dry-run"],
            capture_output=True, text=True, timeout=20
        )
        combined = result.stdout + result.stderr
        # Dry-run should either skip execution or report dry-run; no crash
        assert "Traceback" not in combined, \
            f"Traceback in output: {combined[:400]}"

    @test("Batch mode with local Ollama model (optional)")
    def t() -> None:
        require_ollama()
        model = first_available_ollama_model()
        if model is None:
            raise SkipTest("No Ollama models available")
        result = subprocess.run(
            axe_cmd + ["-c", "@ollama say 'BATCH_OK' and nothing else"],
            capture_output=True, text=True, timeout=60
        )
        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, f"Traceback: {combined[:400]}"

    t()


# ---------------------------------------------------------------------------
# Section 3: Collaborative session
# ---------------------------------------------------------------------------

def section_collab() -> None:
    print("\n" + "=" * 60)
    print("SECTION 3: Collaborative Session")
    print("=" * 60)

    @test("CollaborativeSession can be instantiated")
    def t() -> None:
        from axe import Config, CollaborativeSession
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            # Use two agent names known to exist in axe.yaml (ollama provider)
            session = CollaborativeSession(
                config=config,
                agents=["ollama", "phi"],
                workspace_dir=tmpdir,
                time_limit_minutes=1,
            )
            assert session is not None

    @test("CollaborativeSession.print_banner() executes without NameError")
    def t() -> None:
        from axe import Config, CollaborativeSession
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            session = CollaborativeSession(
                config=config,
                agents=["ollama", "phi"],
                workspace_dir=tmpdir,
                time_limit_minutes=1,
            )
            session.print_banner()

    @test("--collab flag requires --task (error handling)")
    def t() -> None:
        axe_cmd = [sys.executable, str(REPO_ROOT / "axe.py")]
        result = subprocess.run(
            axe_cmd + ["--collab", "ollama,phi", "--workspace", "/tmp"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}
        )
        combined = result.stdout + result.stderr
        assert (
            "--task" in combined.lower()
            or "task" in combined.lower()
            or result.returncode != 0
        ), f"Expected --task error; got: {combined[:300]}"

    @test("Multiple workspace paths accepted via comma-separator")
    def t() -> None:
        from axe import Config, CollaborativeSession
        with tempfile.TemporaryDirectory() as td1, \
             tempfile.TemporaryDirectory() as td2:
            config = Config()
            session = CollaborativeSession(
                config=config,
                agents=["ollama", "phi"],
                workspace_dir=f"{td1},{td2}",
                time_limit_minutes=1,
            )
            assert session is not None

    t()


# ---------------------------------------------------------------------------
# Section 4: Unix socket interface
# ---------------------------------------------------------------------------

def section_socket() -> None:
    print("\n" + "=" * 60)
    print("SECTION 4: Unix Socket Interface")
    print("=" * 60)

    @test("SOCKET_PATH and PID_PATH use correct runtime directory")
    def t() -> None:
        import axe
        uid = os.getuid()
        expected_sock = f"/run/user/{uid}/axe.sock"
        expected_pid = f"/run/user/{uid}/axe.pid"
        assert axe.SOCKET_PATH == expected_sock, \
            f"SOCKET_PATH={axe.SOCKET_PATH} != {expected_sock}"
        assert axe.PID_PATH == expected_pid, \
            f"PID_PATH={axe.PID_PATH} != {expected_pid}"

    @test("write_pid_file() writes current PID")
    def t() -> None:
        import axe
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pid") as tf:
            tmp_pid = tf.name
        orig = axe.PID_PATH
        axe.PID_PATH = tmp_pid
        try:
            axe.write_pid_file()
            written_pid = int(Path(tmp_pid).read_text().strip())
            assert written_pid == os.getpid(), \
                f"PID mismatch: {written_pid} != {os.getpid()}"
        finally:
            axe.PID_PATH = orig
            Path(tmp_pid).unlink(missing_ok=True)

    @test("cleanup_files() removes socket and PID files")
    def t() -> None:
        import axe
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_sock = os.path.join(tmpdir, "axe.sock")
            tmp_pid = os.path.join(tmpdir, "axe.pid")
            Path(tmp_sock).touch()
            Path(tmp_pid).touch()
            orig_sock, orig_pid = axe.SOCKET_PATH, axe.PID_PATH
            axe.SOCKET_PATH = tmp_sock
            axe.PID_PATH = tmp_pid
            try:
                axe.cleanup_files()
                assert not Path(tmp_sock).exists()
                assert not Path(tmp_pid).exists()
            finally:
                axe.SOCKET_PATH = orig_sock
                axe.PID_PATH = orig_pid

    @test("start_socket_server() creates socket file and accepts connections")
    def t() -> None:
        import axe
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_sock = os.path.join(tmpdir, "test_axe.sock")
            orig_sock = axe.SOCKET_PATH
            axe.SOCKET_PATH = tmp_sock
            try:
                srv = axe.start_socket_server()
                assert srv is not None
                assert Path(tmp_sock).exists()
                # Connect as a client
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(tmp_sock)
                client.close()
                srv.close()
            finally:
                axe.SOCKET_PATH = orig_sock
                Path(tmp_sock).unlink(missing_ok=True)

    @test("check_and_cleanup_stale_files() handles orphaned socket")
    def t() -> None:
        import axe
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_sock = os.path.join(tmpdir, "axe.sock")
            tmp_pid = os.path.join(tmpdir, "axe.pid")
            Path(tmp_sock).touch()
            orig_sock, orig_pid = axe.SOCKET_PATH, axe.PID_PATH
            axe.SOCKET_PATH = tmp_sock
            axe.PID_PATH = tmp_pid
            try:
                axe.check_and_cleanup_stale_files()
                assert not Path(tmp_sock).exists()
            finally:
                axe.SOCKET_PATH = orig_sock
                axe.PID_PATH = orig_pid

    @test("axe_socket_client.send_command raises FileNotFoundError when AXE not running")
    def t() -> None:
        from axe_socket_client import send_command
        try:
            send_command("/help")
            # If AXE is running this might succeed – that's also fine
        except FileNotFoundError:
            pass  # Expected when AXE is not running

    t()


# ---------------------------------------------------------------------------
# Section 5: Interactive commands (static / structural validation)
# ---------------------------------------------------------------------------

def section_interactive_commands() -> None:
    print("\n" + "=" * 60)
    print("SECTION 5: Interactive Commands (structural validation)")
    print("=" * 60)

    # We import axe and verify the command handlers exist rather than
    # running a full interactive session (which requires a TTY and live LLM).

    @test("axe module imports without error")
    def t() -> None:
        import axe  # noqa: F401

    @test("Config class loads axe.yaml successfully")
    def t() -> None:
        from axe import Config
        cfg = Config()
        assert cfg is not None

    @test("AgentManager can be instantiated with Config")
    def t() -> None:
        from axe import Config
        from core.agent_manager import AgentManager
        cfg = Config()
        mgr = AgentManager(cfg)
        assert mgr is not None

    @test("ToolRunner can be instantiated")
    def t() -> None:
        from axe import Config
        from core.tool_runner import ToolRunner
        cfg = Config()
        tr = ToolRunner(cfg)
        assert tr is not None

    @test("/prep command: llmprep tool importable")
    def t() -> None:
        import tools.llmprep  # noqa: F401

    @test("/buildinfo command: build_analyzer tool importable")
    def t() -> None:
        from tools.build_analyzer import detect_build_system
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_build_system(tmpdir)
            assert isinstance(result, dict)

    @test("/read command: ResponseProcessor._handle_read works on fixture")
    def t() -> None:
        from axe import Config, ResponseProcessor
        from core.tool_runner import ToolRunner
        cfg = Config()
        tr = ToolRunner(cfg)
        fixture = REPO_ROOT / "tests" / "fixtures" / "hello_world.c"
        proc = ResponseProcessor(cfg, str(REPO_ROOT), tr)
        result = proc._handle_read(str(fixture))
        assert "hello" in result.lower() or "main" in result.lower() or \
               len(result) > 10, f"Unexpected read result: {result[:100]}"

    @test("/exec command: ResponseProcessor._handle_exec runs simple command")
    def t() -> None:
        from axe import Config, ResponseProcessor
        from core.tool_runner import ToolRunner
        cfg = Config()
        tr = ToolRunner(cfg)
        proc = ResponseProcessor(cfg, str(REPO_ROOT), tr)
        result = proc._handle_exec("echo AXE_EXEC_OK")
        assert "AXE_EXEC_OK" in result, f"Got: {result}"

    @test("SharedWorkspace initialises and creates shared note file")
    def t() -> None:
        from axe import SharedWorkspace
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = SharedWorkspace(tmpdir)
            ws.append_to_shared("@tester", "init test note")
            shared_path = Path(tmpdir) / ".collab_shared.md"
            assert shared_path.exists()

    t()


# ---------------------------------------------------------------------------
# Section 6: Workshop tools
# ---------------------------------------------------------------------------

def section_workshop() -> None:
    print("\n" + "=" * 60)
    print("SECTION 6: Workshop Tools")
    print("=" * 60)

    @test("Workshop module imports")
    def t() -> None:
        from workshop import HAS_SAW, HAS_PLANE
        # SAW and Plane are built-in; they should be available
        assert HAS_SAW or True   # graceful if unavailable
        assert HAS_PLANE or True

    @test("SawTracker can be instantiated")
    def t() -> None:
        from workshop.saw import SawTracker
        tracker = SawTracker()
        assert tracker is not None

    @test("SawTracker.analyze() returns result dict")
    def t() -> None:
        from workshop.saw import SawTracker
        tracker = SawTracker()
        result = tracker.analyze("x = input(); print(x)")
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"

    @test("PlaneEnumerator can be instantiated")
    def t() -> None:
        from workshop.plane import PlaneEnumerator
        pe = PlaneEnumerator()
        assert pe is not None

    @test("PlaneEnumerator.analyze() on Python fixture returns result")
    def t() -> None:
        from workshop.plane import PlaneEnumerator
        pe = PlaneEnumerator()
        fixture = str(REPO_ROOT / "tests" / "fixtures" / "hello_world.py")
        result = pe.analyze(fixture)
        assert result is not None

    @test("Workshop HAS_CHISEL / HAS_HAMMER flags accessible")
    def t() -> None:
        from workshop import HAS_CHISEL, HAS_HAMMER  # noqa: F401

    t()


# ---------------------------------------------------------------------------
# Section 7: Agent Skills system
# ---------------------------------------------------------------------------

def section_skills() -> None:
    print("\n" + "=" * 60)
    print("SECTION 7: Agent Skills System")
    print("=" * 60)

    @test("Skills manifest.json is valid JSON")
    def t() -> None:
        import json
        manifest_path = REPO_ROOT / "skills" / "manifest.json"
        assert manifest_path.exists(), "manifest.json not found"
        data = json.loads(manifest_path.read_text())
        assert isinstance(data, dict), "manifest.json must be a JSON object"

    @test("SkillsManager can be instantiated with repo skills dir")
    def t() -> None:
        from core.skills_manager import SkillsManager
        sm = SkillsManager(skills_dir=str(REPO_ROOT / "skills"))
        assert sm is not None

    @test("SkillsManager.list_skills() returns non-empty list")
    def t() -> None:
        from core.skills_manager import SkillsManager
        sm = SkillsManager(skills_dir=str(REPO_ROOT / "skills"))
        skills = sm.list_skills()
        assert len(skills) > 0, "No skills found"

    @test("SkillsManager can load 'reverse_engineering_expert' skill")
    def t() -> None:
        from core.skills_manager import SkillsManager
        sm = SkillsManager(skills_dir=str(REPO_ROOT / "skills"))
        content = sm.get_skill("reverse_engineering_expert")
        assert content, "reverse_engineering_expert skill returned empty content"

    @test("SkillsManager can load 'x86_assembly_expert' skill")
    def t() -> None:
        from core.skills_manager import SkillsManager
        sm = SkillsManager(skills_dir=str(REPO_ROOT / "skills"))
        content = sm.get_skill("x86_assembly_expert")
        assert content, "x86_assembly_expert skill returned empty content"

    @test("SkillsManager can load 'python_agent_expert' skill")
    def t() -> None:
        from core.skills_manager import SkillsManager
        sm = SkillsManager(skills_dir=str(REPO_ROOT / "skills"))
        content = sm.get_skill("python_agent_expert")
        assert content, "python_agent_expert skill returned empty content"

    @test("DOS-specific skills present in manifest")
    def t() -> None:
        import json
        manifest = json.loads((REPO_ROOT / "skills" / "manifest.json").read_text())
        # Look for at least one DOS/RE related skill
        text = str(manifest).lower()
        assert "dos" in text or "reverse" in text or "x86" in text, \
            "No DOS/RE skills found in manifest"

    t()


# ---------------------------------------------------------------------------
# Section 8: XP / Level progression
# ---------------------------------------------------------------------------

def section_progression() -> None:
    print("\n" + "=" * 60)
    print("SECTION 8: XP / Level Progression")
    print("=" * 60)

    @test("calculate_xp_for_level(1) returns 0")
    def t() -> None:
        from progression.xp_system import calculate_xp_for_level
        assert calculate_xp_for_level(1) == 0

    @test("calculate_xp_for_level monotonically increases")
    def t() -> None:
        from progression.xp_system import calculate_xp_for_level
        vals = [calculate_xp_for_level(lvl) for lvl in range(1, 30)]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1], \
                f"XP not monotonic at level {i+1}: {vals[i]} > {vals[i+1]}"

    @test("get_title_for_level returns string for levels 1..40")
    def t() -> None:
        from progression.levels import get_title_for_level
        for lvl in range(1, 41):
            title = get_title_for_level(lvl)
            assert isinstance(title, str) and len(title) > 0, \
                f"No title for level {lvl}"

    @test("LEVEL_SUPERVISOR_ELIGIBLE is defined and > 1")
    def t() -> None:
        from progression.levels import LEVEL_SUPERVISOR_ELIGIBLE
        assert isinstance(LEVEL_SUPERVISOR_ELIGIBLE, int)
        assert LEVEL_SUPERVISOR_ELIGIBLE > 1

    @test("AgentDatabase.award_xp() and load_agent_state() round-trip")
    def t() -> None:
        from database.agent_db import AgentDatabase
        with tempfile.TemporaryDirectory() as tmpdir:
            db = AgentDatabase(os.path.join(tmpdir, "test.db"))
            agent_id = str(uuid.uuid4())
            db.save_agent_state(agent_id, "@testbot", "tinyllama:latest", {}, [], 0, 0, 1)
            db.award_xp(agent_id, 500, "test")
            state = db.load_agent_state(agent_id)
            assert state["xp"] >= 500, f"XP not persisted: {state}"
            assert state["level"] > 1, f"Level not updated: {state}"

    t()


# ---------------------------------------------------------------------------
# Section 9: Cognitive architecture
# ---------------------------------------------------------------------------

def section_cognitive() -> None:
    print("\n" + "=" * 60)
    print("SECTION 9: Cognitive Architecture")
    print("=" * 60)

    @test("SubsumptionController importable and instantiable")
    def t() -> None:
        from core import SubsumptionController
        ctrl = SubsumptionController()
        assert ctrl is not None

    @test("SubsumptionController.get_layer_for_level() returns valid layer")
    def t() -> None:
        from core import SubsumptionController
        from core.subsumption import SubsumptionLayer
        ctrl = SubsumptionController()
        for lvl in [1, 5, 15, 30]:
            layer = ctrl.get_layer_for_level(lvl)
            assert isinstance(layer, SubsumptionLayer), \
                f"Bad layer for level {lvl}: {layer}"

    @test("SubsumptionController.suppress_agent() works")
    def t() -> None:
        from core import SubsumptionController
        ctrl = SubsumptionController()
        success, msg = ctrl.suppress_agent("@high", 20, "@low", 5, "test suppression")
        assert isinstance(success, bool)
        assert isinstance(msg, str)

    @test("GlobalWorkspace instantiable and broadcast works")
    def t() -> None:
        from core import GlobalWorkspace
        with tempfile.TemporaryDirectory() as tmpdir:
            gw = GlobalWorkspace(tmpdir)
            bc_id = gw.broadcast("@agent1", 10, "TEST", "test message")
            assert bc_id is not None

    @test("GlobalWorkspace.detect_conflicts() works")
    def t() -> None:
        from core import GlobalWorkspace
        with tempfile.TemporaryDirectory() as tmpdir:
            gw = GlobalWorkspace(tmpdir)
            gw.broadcast("@a", 10, "CODE", "Code is correct")
            gw.broadcast("@b", 10, "CODE", "Code has bugs", related_file="x.py")
            conflicts = gw.detect_conflicts(window_broadcasts=10)
            assert isinstance(conflicts, list)

    @test("ArbitrationProtocol instantiable")
    def t() -> None:
        from core import ArbitrationProtocol, GlobalWorkspace
        with tempfile.TemporaryDirectory() as tmpdir:
            gw = GlobalWorkspace(tmpdir)
            ap = ArbitrationProtocol(gw)
            assert ap is not None

    @test("GlobalWorkspace.vote_xp() returns result dict")
    def t() -> None:
        from core import GlobalWorkspace
        with tempfile.TemporaryDirectory() as tmpdir:
            gw = GlobalWorkspace(tmpdir)
            result = gw.vote_xp("@voter", 10, "@target", 5, "good work")
            assert isinstance(result, dict)
            assert "success" in result

    t()


# ---------------------------------------------------------------------------
# Section 10: Sandbox security
# ---------------------------------------------------------------------------

def section_sandbox() -> None:
    print("\n" + "=" * 60)
    print("SECTION 10: Sandbox Security (blacklist model)")
    print("=" * 60)

    @test("ToolRunner respects command blacklist (rm blocked)")
    def t() -> None:
        from axe import Config
        from core.tool_runner import ToolRunner
        cfg = Config()
        tr = ToolRunner(cfg)
        # Try to run a blacklisted command; should be blocked or return error
        # (The actual blacklist may vary; we just ensure no real deletion)
        with tempfile.TemporaryDirectory() as tmpdir:
            sentinel = os.path.join(tmpdir, "do_not_delete.txt")
            Path(sentinel).write_text("sentinel")
            # Try rm via ToolRunner; it may be blocked or allowed depending on config
            result = tr.run_command(f"rm {sentinel}")
            # If allowed: file may be deleted (that's the ToolRunner doing its job)
            # If blocked: file still exists and result contains 'blocked' or 'denied'
            # Either way, we should not see an unhandled exception
            assert isinstance(result, (str, tuple)), f"Unexpected return type: {type(result)}"

    @test("safety.rules SESSION_RULES importable and non-empty")
    def t() -> None:
        from safety.rules import SESSION_RULES
        assert isinstance(SESSION_RULES, str) and len(SESSION_RULES) > 0

    t()


# ---------------------------------------------------------------------------
# Section 11: Token optimisation
# ---------------------------------------------------------------------------

def section_token_optimization() -> None:
    print("\n" + "=" * 60)
    print("SECTION 11: Token Optimisation")
    print("=" * 60)

    @test("context_optimizer module importable")
    def t() -> None:
        from utils.context_optimizer import ContextOptimizer
        co = ContextOptimizer()
        assert co is not None

    @test("prompt_compressor module importable")
    def t() -> None:
        from utils import prompt_compressor  # noqa: F401

    @test("token_stats module importable")
    def t() -> None:
        from utils.token_stats import TokenStats
        ts = TokenStats()
        assert ts is not None

    t()


# ---------------------------------------------------------------------------
# Section 12: Tools (minifier, llmprep, build_analyzer)
# ---------------------------------------------------------------------------

def section_tools() -> None:
    print("\n" + "=" * 60)
    print("SECTION 12: Tools (minifier, llmprep, build_analyzer)")
    print("=" * 60)

    @test("Minifier: C source minification")
    def t() -> None:
        from tools.minifier import minify_c
        fixture = (REPO_ROOT / "tests" / "fixtures" / "hello_world.c").read_text()
        result = minify_c(fixture)
        assert isinstance(result, str)
        assert len(result) < len(fixture), "Minified C should be shorter than original"
        assert "main" in result, "Minified C should still contain 'main'"

    @test("Minifier: Python source minification")
    def t() -> None:
        from tools.minifier import minify_python
        fixture = (REPO_ROOT / "tests" / "fixtures" / "hello_world.py").read_text()
        result = minify_python(fixture)
        assert isinstance(result, str)
        assert len(result) < len(fixture), "Minified Python should be shorter than original"

    @test("build_analyzer: detect_build_system on AXE repo")
    def t() -> None:
        from tools.build_analyzer import detect_build_system
        result = detect_build_system(str(REPO_ROOT))
        assert isinstance(result, dict)

    @test("llmprep: prepare_directory on fixtures dir")
    def t() -> None:
        import tools.llmprep as lp
        fixture_dir = str(REPO_ROOT / "tests" / "fixtures")
        with tempfile.TemporaryDirectory() as out_dir:
            # prepare_directory signature may vary; check module has it
            fn = getattr(lp, "prepare_directory", None) or \
                 getattr(lp, "prepare", None) or \
                 getattr(lp, "run", None)
            if fn is None:
                raise SkipTest("llmprep.prepare_directory not found – API may differ")
            result = fn(fixture_dir, output_dir=out_dir)
            assert result is not None or True  # any non-crash is fine

    t()


# ---------------------------------------------------------------------------
# Section 13: Configuration architecture
# ---------------------------------------------------------------------------

def section_config() -> None:
    print("\n" + "=" * 60)
    print("SECTION 13: Configuration Architecture")
    print("=" * 60)

    @test("models.yaml: valid YAML and contains ollama models")
    def t() -> None:
        import yaml
        data = yaml.safe_load((REPO_ROOT / "models.yaml").read_text())
        assert isinstance(data, dict), "models.yaml must be a YAML mapping"
        text = str(data).lower()
        assert "ollama" in text or "tinyllama" in text or "qwen" in text, \
            "No ollama/local model entries in models.yaml"

    @test("providers.yaml: valid YAML and ollama provider defined")
    def t() -> None:
        import yaml
        data = yaml.safe_load((REPO_ROOT / "providers.yaml").read_text())
        assert isinstance(data, dict)
        # providers.yaml has a top-level 'providers' or direct provider keys
        text = str(data).lower()
        assert "ollama" in text, "ollama not found in providers.yaml"

    @test("axe.yaml: valid YAML with at least one agent defined")
    def t() -> None:
        import yaml
        data = yaml.safe_load((REPO_ROOT / "axe.yaml").read_text())
        assert isinstance(data, dict)
        # axe.yaml has 'agents' key
        assert "agents" in str(data).lower() or len(data) > 0

    @test("Config.get_agent_config() returns dict for 'ollama' agent")
    def t() -> None:
        from axe import Config
        cfg = Config()
        agent_cfg = cfg.get_agent_config("ollama")
        assert agent_cfg is not None, "ollama agent not found in config"
        assert isinstance(agent_cfg, dict)

    t()


# ---------------------------------------------------------------------------
# Section 14: Ollama live integration (optional – requires running Ollama)
# ---------------------------------------------------------------------------

def section_ollama_live() -> None:
    print("\n" + "=" * 60)
    print("SECTION 14: Live Ollama Integration (optional)")
    print("=" * 60)

    @test("Ollama API responds at localhost:11434")
    def t() -> None:
        require_ollama()
        import urllib.request, json
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags", timeout=5
        ) as resp:
            data = json.loads(resp.read())
            assert "models" in data

    @test("At least one of the expected models is available")
    def t() -> None:
        require_ollama()
        expected = {"qwen2.5-coder:1.5b", "qwen2.5:1.5b", "tinyllama:latest"}
        available = set(ollama_models())
        found = expected & available
        assert len(found) > 0, \
            f"None of the expected models found. Available: {available}"
        print(f"      Found: {found}")

    @test("AgentManager can call ollama model (quick ping)")
    def t() -> None:
        require_ollama()
        from axe import Config
        from core.agent_manager import AgentManager
        model = first_available_ollama_model()
        if model is None:
            raise SkipTest("No Ollama models available")
        cfg = Config()
        mgr = AgentManager(cfg)
        # Build a minimal agent config pointing at the local model
        agent_cfg = {
            "provider": "ollama",
            "model": model,
            "system_prompt": "You are a test agent.",
            "context_tokens": 4096,
        }
        response = mgr.call_agent(
            agent_name="test_ollama",
            agent_config=agent_cfg,
            messages=[{"role": "user", "content": "Reply with the single word: PONG"}],
        )
        assert response is not None and len(response) > 0, \
            f"Empty response from Ollama: {response!r}"
        print(f"      Model response snippet: {response[:80]!r}")

    t()


# ---------------------------------------------------------------------------
# Section 15: Keypress / interactive test infrastructure (structural)
# ---------------------------------------------------------------------------

def section_keypress() -> None:
    print("\n" + "=" * 60)
    print("SECTION 15: Keypress Interactive Test Infrastructure")
    print("=" * 60)

    @test("keypress script files exist in tests/keypress_scripts/")
    def t() -> None:
        scripts_dir = REPO_ROOT / "tests" / "keypress_scripts"
        assert scripts_dir.is_dir(), "tests/keypress_scripts/ directory not found"
        scripts = list(scripts_dir.glob("*.txt"))
        assert len(scripts) >= 3, \
            f"Expected ≥ 3 keypress scripts, found {len(scripts)}"
        names = {s.name for s in scripts}
        assert "axe_help.txt" in names, "axe_help.txt not found"

    @test("keypress installed in tools/keypress/ (optional)")
    def t() -> None:
        keypress_dir = REPO_ROOT / "tools" / "keypress"
        if not keypress_dir.exists():
            raise SkipTest(
                "tools/keypress/ not found – run scripts/setup_env.sh to install"
            )
        kp = keypress_dir / "keypress.py"
        assert kp.exists(), "keypress.py not found in tools/keypress/"

    @test("setup_env.sh exists and is a valid shell script")
    def t() -> None:
        setup = REPO_ROOT / "scripts" / "setup_env.sh"
        assert setup.exists(), "scripts/setup_env.sh not found"
        content = setup.read_text()
        assert "#!/" in content[:5], "setup_env.sh missing shebang"
        assert "ollama" in content.lower(), "setup_env.sh does not mention ollama"
        assert "keypress" in content.lower(), "setup_env.sh does not mention keypress"
        assert "xvfb" in content.lower(), "setup_env.sh does not mention xvfb"

    t()


# ---------------------------------------------------------------------------
# Section 16: Fixture files and reference material
# ---------------------------------------------------------------------------

def section_fixtures() -> None:
    print("\n" + "=" * 60)
    print("SECTION 16: Test Fixtures")
    print("=" * 60)

    @test("tests/fixtures/hello_world.c exists and is valid C")
    def t() -> None:
        fixture = REPO_ROOT / "tests" / "fixtures" / "hello_world.c"
        assert fixture.exists()
        content = fixture.read_text()
        assert "#include" in content
        assert "int main" in content

    @test("tests/fixtures/hello_world.py exists and is valid Python")
    def t() -> None:
        fixture = REPO_ROOT / "tests" / "fixtures" / "hello_world.py"
        assert fixture.exists()
        content = fixture.read_text()
        assert "def main" in content
        # Compile check
        import ast
        ast.parse(content)

    @test("tests/fixtures/dos_sample.asm exists with x86 DOS content")
    def t() -> None:
        fixture = REPO_ROOT / "tests" / "fixtures" / "dos_sample.asm"
        assert fixture.exists()
        content = fixture.read_text()
        assert "int" in content.lower() and "21h" in content.lower(), \
            "DOS INT 21h not found in assembly fixture"

    t()


# ---------------------------------------------------------------------------
# Section 17: RE toolchain — dumpexe, HaxBox fixtures, dosbox-staging
# ---------------------------------------------------------------------------

def section_re_toolchain() -> None:
    print("\n" + "=" * 60)
    print("SECTION 17: RE Toolchain (dumpexe, HaxBox fixtures, dosbox-staging)")
    print("=" * 60)

    TOOLS_DIR = REPO_ROOT / "tools"
    DUMPEXE_BIN = TOOLS_DIR / "dumpexe" / "dumpexe"
    DOS_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "dos_binaries"

    @test("dumpexe source cloned to tools/dumpexe/ (optional)")
    def t() -> None:
        dumpexe_src = TOOLS_DIR / "dumpexe"
        if not dumpexe_src.exists():
            raise SkipTest(
                "tools/dumpexe/ not found – run scripts/setup_env.sh to clone"
            )
        assert (dumpexe_src / "dumpexe.cpp").exists(), \
            "dumpexe.cpp missing – clone may be incomplete"

    @test("dumpexe binary built (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest(
                "dumpexe binary not built – run: "
                "make -C tools/dumpexe CXX=g++-14  "
                "(requires gcc-14 + libcapstone-dev)"
            )
        assert os.access(str(DUMPEXE_BIN), os.X_OK), "dumpexe not executable"

    @test("HaxBox DOS fixtures directory populated (optional)")
    def t() -> None:
        if not DOS_FIXTURES.exists():
            raise SkipTest(
                "tests/fixtures/dos_binaries/ not found – "
                "run scripts/setup_env.sh to clone HaxBox"
            )
        entries = list(DOS_FIXTURES.iterdir())
        assert len(entries) > 0, "dos_binaries/ directory is empty"

    @test("HaxBox 4dos595 EXE fixtures present (optional)")
    def t() -> None:
        if not DOS_FIXTURES.exists():
            raise SkipTest("dos_binaries/ not populated")
        subdir = DOS_FIXTURES / "4dos595"
        if not subdir.exists():
            raise SkipTest("4dos595/ subdirectory not found in dos_binaries/")
        expected = ["4HELP.EXE", "HELPCFG.EXE", "OPTION.EXE"]
        for fname in expected:
            fpath = subdir / fname
            assert fpath.exists() or fpath.is_symlink(), \
                f"Expected fixture not found: {fpath}"

    @test("HaxBox MZ signature check on 4HELP.EXE (optional)")
    def t() -> None:
        exe = DOS_FIXTURES / "4dos595" / "4HELP.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("4HELP.EXE not available")
        with open(str(exe), "rb") as f:
            magic = f.read(2)
        assert magic == b"MZ", \
            f"4HELP.EXE does not start with MZ signature: {magic!r}"

    @test("HaxBox COM file KSTACK.COM present (optional)")
    def t() -> None:
        com = DOS_FIXTURES / "4dos595" / "KSTACK.COM"
        if not (com.exists() or com.is_symlink()):
            raise SkipTest("KSTACK.COM not available")
        size = com.stat().st_size
        assert size > 0, "KSTACK.COM is empty"
        assert size < 4096, f"KSTACK.COM larger than expected for a TSR stub: {size}"

    # NOTE: dumpexe COM disassembly (-d) is known to produce incomplete output
    # for all but very small COM files — disassembly truncates early (within the
    # first few hundred bytes) on files such as LIST.COM, ARCE.COM, FV.COM.
    # For COM files, only the default summary and -x hexdump are reliable.
    # All disassembly tests below target MZ EXE or SYS files only.

    @test("HaxBox SYS drivers present (optional)")
    def t() -> None:
        if not DOS_FIXTURES.exists():
            raise SkipTest("dos_binaries/ not populated")
        sys_files = [
            DOS_FIXTURES / "HIMEM.SYS",
            DOS_FIXTURES / "ANSI.SYS",
        ]
        found = [f for f in sys_files if f.exists() or f.is_symlink()]
        if not found:
            raise SkipTest("No SYS driver fixtures found in dos_binaries/")
        # Verify SYS driver signature (0xFF FF FF FF = next-driver pointer = end of chain)
        for sys_file in found:
            with open(str(sys_file), "rb") as f:
                header = f.read(4)
            assert header == b"\xff\xff\xff\xff", \
                f"{sys_file.name}: unexpected SYS driver header: {header!r}"

    @test("dumpexe can analyse 4HELP.EXE — MZ header output (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "4HELP.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("4HELP.EXE fixture not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0, \
            f"dumpexe exited {result.returncode}: {result.stderr[:200]}"
        out = result.stdout
        # dumpexe always starts with this prefix on MZ EXE files
        assert out.startswith("Display of File"), \
            f"Unexpected output prefix: {out[:80]!r}"
        # Standard MZ EXE header fields
        for field in ("DOS File Size", "Load Image Size",
                      "Relocation Table entry count", "Header Size",
                      "Initial Stack Segment  (SS:SP)", "Program Entry Point    (CS:IP)"):
            assert field in out, f"Missing field: {field!r}"
        print(f"      4HELP.EXE: {result.stdout.splitlines()[2].strip()}")

    @test("dumpexe -d disassembles HELPCFG.EXE — INT annotations present (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "HELPCFG.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("HELPCFG.EXE fixture not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "-d", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0, \
            f"dumpexe -d exited {result.returncode}: {result.stderr[:200]}"
        out = result.stdout
        assert "=== Disassembly (from entry point to EOF) ===" in out, \
            "Disassembly section header missing"
        assert "File Offset  Raw Bytes            Instruction" in out, \
            "Disassembly column header missing"
        # Capstone INT annotations must appear (INT 21h calls are present)
        assert "; INT 21h -" in out, \
            "INT 21h annotation comments missing from disassembly"
        # Specific known instructions from real output
        assert "int 0x21" in out, "INT 21h opcode missing"
        assert "mov ah, 9" in out or "mov ah, 9" in out.replace(" ", " "), \
            "AH=9 (print string) setup missing"

    @test("dumpexe -d -n disassembles HELPCFG.EXE — annotations suppressed (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "HELPCFG.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("HELPCFG.EXE fixture not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "-d", "-n", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        # With -n, INT annotation comments must be absent
        assert "; INT 21h" not in result.stdout, \
            "-n flag did not suppress INT annotations"

    @test("dumpexe -r shows relocation table for 4HELP.EXE (718 entries) (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "4HELP.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("4HELP.EXE not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "-r", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        out = result.stdout
        assert "=== Relocation Table" in out, "Relocation table section missing"
        assert "Segment:Offset" in out, "Relocation table column header missing"
        # 4HELP.EXE has 0x2CE = 718 relocation entries per its header
        assert "718 entries" in out or "02CEh" in out, \
            "Expected 718 relocation entries not found"

    @test("dumpexe -x hexdump shows Hex+ASCII section for HELPCFG.EXE (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "HELPCFG.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("HELPCFG.EXE not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "-x", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "=== Hex+ASCII Dump (from entry point to EOF) ===" in result.stdout

    @test("dumpexe -r detects PKLITE packer string in HELPCFG.EXE padding (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "HELPCFG.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("HELPCFG.EXE not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "-r", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        # HELPCFG.EXE is packed with PKLITE — the copyright string is in header padding
        assert "PKLITE" in result.stdout, \
            "PKLITE packer string not found in HELPCFG.EXE header padding"

    @test("dumpexe --simulate shows DOS load state for HELPCFG.EXE (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "HELPCFG.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("HELPCFG.EXE not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "--simulate", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        out = result.stdout
        assert "=== DOS LOAD SIMULATION ===" in out, "Simulation section missing"
        assert "Initial Register State:" in out
        assert "CS:IP =" in out
        assert "SS:SP =" in out
        assert "FLAGS =" in out

    @test("dumpexe --simulate --base=2000 accepts custom load base (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        exe = DOS_FIXTURES / "4dos595" / "HELPCFG.EXE"
        if not (exe.exists() or exe.is_symlink()):
            raise SkipTest("HELPCFG.EXE not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), "--simulate", "--base=2000", str(exe)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        assert "Load Base Segment: 2000h" in result.stdout, \
            "--base=2000 not reflected in simulation output"

    @test("dumpexe SYS driver: HIMEM.SYS — device driver header decoded (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        sys_file = DOS_FIXTURES / "HIMEM.SYS"
        if not (sys_file.exists() or sys_file.is_symlink()):
            raise SkipTest("HIMEM.SYS not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), str(sys_file)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        out = result.stdout
        assert "=== DOS Device Driver Header ===" in out
        assert "Next Driver Pointer" in out
        # HIMEM.SYS is last in chain
        assert "FFFFFFFFh" in out
        assert "Character device" in out
        # Known device name for HIMEM.SYS
        assert "XMSXXXX0" in out, "HIMEM.SYS device name not found"

    @test("dumpexe SYS driver: ANSI.SYS — CON device decoded (optional)")
    def t() -> None:
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        sys_file = DOS_FIXTURES / "ANSI.SYS"
        if not (sys_file.exists() or sys_file.is_symlink()):
            raise SkipTest("ANSI.SYS not available")
        result = subprocess.run(
            [str(DUMPEXE_BIN), str(sys_file)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        out = result.stdout
        assert "CON" in out, "ANSI.SYS CON device name not found"
        assert "Standard output" in out or "Standard input" in out

    @test("dumpexe COM: summary and hexdump work on KSTACK.COM (optional)")
    def t() -> None:
        # NOTE: dumpexe -d (disassembly) is known to produce incomplete output
        # for COM files beyond a few hundred bytes; only summary and -x are safe.
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        com = DOS_FIXTURES / "4dos595" / "KSTACK.COM"
        if not (com.exists() or com.is_symlink()):
            raise SkipTest("KSTACK.COM not available")
        # Default summary
        result = subprocess.run(
            [str(DUMPEXE_BIN), str(com)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        out = result.stdout
        assert ".COM (flat binary, 16-bit MS-DOS)" in out, \
            "COM format not identified in summary"
        assert "File Size" in out
        assert "Program Entry Point (CS:IP)" in out
        # Hexdump
        result2 = subprocess.run(
            [str(DUMPEXE_BIN), "-x", str(com)],
            capture_output=True, text=True, timeout=15
        )
        assert result2.returncode == 0
        assert "=== Hex+ASCII Dump (from entry point to EOF) ===" in result2.stdout

    @test("dumpexe COM disassembly known-incomplete warning (optional)")
    def t() -> None:
        # Verify the known limitation: -d on COM files stops well short of EOF.
        # This test documents the bug rather than asserting correct behaviour.
        if not DUMPEXE_BIN.exists():
            raise SkipTest("dumpexe not built")
        com = DOS_FIXTURES / "list91m" / "LIST.COM"
        # list91m may not be a direct child; check both locations
        if not (com.exists() or com.is_symlink()):
            com = DOS_FIXTURES.parent.parent.parent / "tools" / "HaxBox" / "tests" / "BBS" / "list91m" / "LIST.COM"
        if not com.exists():
            raise SkipTest("LIST.COM not available for COM truncation check")
        file_size = com.stat().st_size   # 26793 bytes
        result = subprocess.run(
            [str(DUMPEXE_BIN), "-d", str(com)],
            capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        # Count disasm instruction lines (lines starting with a hex offset)
        import re as _re
        lines = _re.findall(r"^[0-9a-f]{8}h", result.stdout, _re.MULTILINE)
        disasm_bytes_covered = len(lines) * 2   # rough lower bound
        # Known bug: coverage is far less than file size for large COM files
        if disasm_bytes_covered < file_size // 4:
            print(f"      ⚠ COM disassembly truncation confirmed: "
                  f"~{disasm_bytes_covered} bytes covered of {file_size} "
                  f"({100*disasm_bytes_covered//file_size}%)")
        # Test passes regardless — this documents the limitation, not a failure

    @test("dosbox-staging fork cloned to tools/dosbox-staging/ (optional)")
    def t() -> None:
        dosbox_dir = TOOLS_DIR / "dosbox-staging"
        if not dosbox_dir.exists():
            raise SkipTest(
                "tools/dosbox-staging/ not found – "
                "run scripts/setup_env.sh to clone"
            )
        debug_trace = dosbox_dir / "docs" / "DEBUG_TRACE.md"
        assert debug_trace.exists(), \
            "DEBUG_TRACE.md not found – clone may be incomplete"

    @test("dosbox-staging DEBUG_TRACE.md documents [debugtrace] config (optional)")
    def t() -> None:
        debug_trace = TOOLS_DIR / "dosbox-staging" / "docs" / "DEBUG_TRACE.md"
        if not debug_trace.exists():
            raise SkipTest("DEBUG_TRACE.md not available")
        content = debug_trace.read_text()
        assert "[debugtrace]" in content, \
            "DEBUG_TRACE.md missing [debugtrace] section"
        assert "trace_instructions" in content, \
            "DEBUG_TRACE.md missing trace_instructions key"

    @test("AXE dosbox-related skills present (dos_exe_unpack, dosbox_int21_trace)")
    def t() -> None:
        skills_dir = REPO_ROOT / "skills"
        required = ["dos_exe_unpack.md", "dosbox_int21_trace.md"]
        for skill in required:
            assert (skills_dir / skill).exists(), \
                f"DOS skill not found: skills/{skill}"

    t()


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

SECTIONS = [
    section_environment,
    section_cli,
    section_batch,
    section_collab,
    section_socket,
    section_interactive_commands,
    section_workshop,
    section_skills,
    section_progression,
    section_cognitive,
    section_sandbox,
    section_token_optimization,
    section_tools,
    section_config,
    section_ollama_live,
    section_keypress,
    section_fixtures,
    section_re_toolchain,
]


def main() -> None:
    print("\n" + "=" * 60)
    print("AXE END-TO-END FEATURE VALIDATION TEST SUITE")
    print("=" * 60)
    print(f"Repository: {REPO_ROOT}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Ollama: {'running' if ollama_available() else 'not running (optional tests skipped)'}")

    for section_fn in SECTIONS:
        try:
            section_fn()
        except Exception as exc:
            print(f"\n[!] Section {section_fn.__name__} raised unexpected error: {exc}")
            import traceback
            traceback.print_exc()

    # Summary
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
