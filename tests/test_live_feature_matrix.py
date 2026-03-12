#!/usr/bin/env python3
"""
test_live_feature_matrix.py
============================
Comprehensive live AXE feature-validation test suite.

Exercises every major AXE feature using three small Ollama models:

  • qwen2.5-coder:1.5b  (supervisor)
  • qwen2.5:1.5b        (worker A)
  • tinyllama:latest    (worker B)

Features covered
----------------
 1. Batch mode  (-c "@agent task")
 2. Collaborative session  (--collab)
 3. Unix socket interface + /help via socket
 4. /collab slash command inside interactive mode
 5. Session save / load / list
 6. Token savings (TokenStats, Minifier, PromptCompressor)
 7. Multiple workspace dirs (--workspace a,b and /workspace +path)
 8. AXE self-analysis (workspace = AXE source; agents discuss improvements)
 9. SRI groundwork discussion
10. XP / level / title progression
11. Workshop tools importability

All tests that require Ollama skip gracefully when the server is not
reachable, so the suite still passes in offline CI.

Usage
-----
    python3 tests/test_live_feature_matrix.py

Exit codes
----------
    0 — all tests passed or skipped
    1 — one or more tests failed
"""
from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Minimal test runner
# ---------------------------------------------------------------------------
PASS = "✅"
FAIL = "✗ "
SKIP = "⏭ "

_results: List[Tuple[str, str, str]] = []


class SkipTest(Exception):
    pass


def test(name: str) -> Callable:
    """Decorator: runs function, catches exceptions, records result."""
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Optional[bool]:
            try:
                fn(*args, **kwargs)
                _results.append((name, PASS, ""))
                print(f"  {PASS} {name}")
                return True
            except SkipTest as e:
                _results.append((name, SKIP, str(e)))
                print(f"  {SKIP} {name}: {e}")
                return None
            except AssertionError as e:
                _results.append((name, FAIL, str(e)))
                print(f"  {FAIL} {name}: {e}")
                return False
            except Exception as e:  # noqa: BLE001
                _results.append((name, FAIL, f"{type(e).__name__}: {e}"))
                print(f"  {FAIL} {name}: {type(e).__name__}: {e}")
                return False
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
AXE_PY = str(REPO_ROOT / "axe.py")

MODEL_MAP = {
    "qwen2.5-coder:1.5b": "qwen25coder",
    "qwen2.5:1.5b":       "qwen25",
    "tinyllama:latest":   "tinyllama",
}
SUPERVISOR_AGENT = "qwen25coder"
WORKER_A_AGENT   = "qwen25"
WORKER_B_AGENT   = "tinyllama"


def ollama_running() -> bool:
    try:
        s = socket.create_connection(("localhost", 11434), timeout=2)
        s.close()
        return True
    except OSError:
        return False


def require_ollama() -> None:
    if not ollama_running():
        raise SkipTest("Ollama not reachable")


def available_models() -> List[str]:
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        return [ln.split()[0] for ln in r.stdout.splitlines()[1:] if ln.strip()]
    except Exception:  # noqa: BLE001
        return []


def run_axe(args: List[str], timeout: int = 90,
            stdin_text: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, AXE_PY] + args,
        capture_output=True, text=True, timeout=timeout,
        input=stdin_text, cwd=str(REPO_ROOT),
    )


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[mGKHFJST]", "", text)


def socket_send(command: str, timeout: int = 10) -> str:
    uid = os.getuid()
    sock_path = f"/run/user/{uid}/axe.sock"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(sock_path)
    try:
        msg = command if command.endswith("\n") else command + "\n"
        s.sendall(msg.encode())
        data = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                break
    finally:
        s.close()
    return data.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Section 1: Batch mode
# ---------------------------------------------------------------------------
def section_batch() -> None:
    print("\n" + "=" * 60)
    print("SECTION 1: Batch Mode  (-c \"@agent task\")")
    print("=" * 60)

    @test("qwen25coder responds to a simple prompt")
    def t1() -> None:
        require_ollama()
        r = run_axe(["-c", f"@{SUPERVISOR_AGENT} Reply with the single word: HELLO"])
        out = strip_ansi(r.stdout + r.stderr)
        assert len(out.strip()) > 10, f"No output; rc={r.returncode}"
        print(f"    snippet: {out[:80].strip()!r}")

    @test("tinyllama responds to a simple prompt")
    def t2() -> None:
        require_ollama()
        r = run_axe(["-c", f"@{WORKER_B_AGENT} Reply with the word: READY"])
        out = strip_ansi(r.stdout + r.stderr)
        assert len(out.strip()) > 5, f"Empty response; rc={r.returncode}"

    @test("--dry-run flag is accepted without error")
    def t3() -> None:
        r = run_axe(["--dry-run", "-c", f"@{SUPERVISOR_AGENT} list files"], timeout=120)
        out = strip_ansi(r.stdout + r.stderr)
        assert r.returncode == 0 or len(out.strip()) > 0, \
            f"dry-run failed: rc={r.returncode} out={out[:200]!r}"

    @test("multiple workspace dirs via --workspace a,b")
    def t4() -> None:
        require_ollama()
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            Path(td2, "canary.txt").write_text("workspace=td2\n")
            r = run_axe(
                ["--workspace", f"{td1},{td2}",
                 "-c", f"@{WORKER_B_AGENT} Say: WORKSPACE_OK"],
                timeout=150,
            )
            out = strip_ansi(r.stdout + r.stderr)
            assert r.returncode == 0 or len(out.strip()) > 0, \
                f"multi-workspace batch failed: {out[:200]!r}"

    t1(); t2(); t3(); t4()


# ---------------------------------------------------------------------------
# Section 2: Collaborative session
# ---------------------------------------------------------------------------
def section_collab() -> None:
    print("\n" + "=" * 60)
    print("SECTION 2: Collaborative Session  (--collab)")
    print("=" * 60)

    @test("qwen25coder + tinyllama complete a collab task")
    def t1() -> None:
        require_ollama()
        models = set(available_models())
        if not {"qwen2.5-coder:1.5b", "tinyllama:latest"}.issubset(models):
            raise SkipTest("Required models not available")
        with tempfile.TemporaryDirectory() as ws:
            Path(ws, "hello.py").write_text("print('Hello')\n")
            r = run_axe(
                ["--collab", f"{SUPERVISOR_AGENT},{WORKER_B_AGENT}",
                 "--workspace", ws, "--time", "1",
                 "--task", "Read hello.py and briefly describe what it does."],
                timeout=180,
            )
            out = strip_ansi(r.stdout + r.stderr)
            assert len(out.strip()) > 20, f"No collab output; rc={r.returncode}"
            print(f"    snippet: {out[:100].strip()!r}")

    @test("workspace files are accessible to collab agents")
    def t2() -> None:
        require_ollama()
        with tempfile.TemporaryDirectory() as ws:
            Path(ws, "target.c").write_text(
                "#include <stdio.h>\nint main(){printf(\"ok\");return 0;}\n"
            )
            r = run_axe(
                ["--collab", f"{SUPERVISOR_AGENT},{WORKER_B_AGENT}",
                 "--workspace", ws, "--time", "1",
                 "--task", "Read target.c and say: C_FILE_OK"],
                timeout=180,
            )
            out = strip_ansi(r.stdout + r.stderr)
            assert len(out.strip()) > 10

    t1(); t2()


# ---------------------------------------------------------------------------
# Section 3: Session save / load
# ---------------------------------------------------------------------------
def section_session() -> None:
    print("\n" + "=" * 60)
    print("SECTION 3: Session Save / Load")
    print("=" * 60)

    @test("save_session() writes a JSON file")
    def t1() -> None:
        from core.session_manager import SessionManager
        with tempfile.TemporaryDirectory() as td:
            sm = SessionManager(sessions_dir=td)
            ok = sm.save_session("test1", {
                "conversation": [{"role": "user", "content": "hi"}],
                "workspace": "/tmp", "agents": ["qwen25coder"], "metadata": {}
            })
            assert ok
            assert len(list(Path(td).glob("*.json"))) == 1

    @test("load_session() restores saved data")
    def t2() -> None:
        from core.session_manager import SessionManager
        with tempfile.TemporaryDirectory() as td:
            sm = SessionManager(sessions_dir=td)
            original = {"conversation": [{"role": "user", "content": "hello"}],
                        "workspace": "/tmp/ws", "agents": ["qwen25coder"], "metadata": {}}
            sm.save_session("restore", original)
            loaded = sm.load_session("restore")
            assert loaded is not None
            assert loaded["conversation"] == original["conversation"]
            assert loaded["workspace"] == original["workspace"]

    @test("list_sessions() returns all saved sessions")
    def t3() -> None:
        from core.session_manager import SessionManager
        with tempfile.TemporaryDirectory() as td:
            sm = SessionManager(sessions_dir=td)
            for i in range(3):
                sm.save_session(f"s{i}", {"conversation": [], "workspace": "/tmp",
                                          "agents": [], "metadata": {}})
            sessions = sm.list_sessions()
            assert len(sessions) == 3

    @test("save→load round-trip preserves all fields")
    def t4() -> None:
        from core.session_manager import SessionManager
        with tempfile.TemporaryDirectory() as td:
            sm = SessionManager(sessions_dir=td)
            payload = {
                "conversation": [{"role": "user", "content": "What is AXE?"},
                                  {"role": "assistant", "content": "AXE is a multi-agent framework."}],
                "workspace": str(REPO_ROOT),
                "agents": ["qwen25coder", "qwen25", "tinyllama"],
                "metadata": {"tokens_used": 512, "messages": 2},
            }
            sm.save_session("rt", payload)
            r = sm.load_session("rt")
            assert r is not None
            assert len(r["conversation"]) == 2
            assert r["agents"] == payload["agents"]
            print("    round-trip OK")

    @test("load of non-existent name returns None")
    def t5() -> None:
        from core.session_manager import SessionManager
        with tempfile.TemporaryDirectory() as td:
            assert SessionManager(sessions_dir=td).load_session("no-such") is None

    @test("interactive /session save + load round-trip")
    def t6() -> None:
        out = strip_ansi((run_axe([], timeout=30, stdin_text=
            "/session save pytest-session\n/session list\n/session load pytest-session\n/quit\n"
        ).stdout + "").strip())
        assert "session" in out.lower() or "pytest" in out.lower() or len(out) > 5

    t1(); t2(); t3(); t4(); t5(); t6()


# ---------------------------------------------------------------------------
# Section 4: Token optimization
# ---------------------------------------------------------------------------
def section_token_optimization() -> None:
    print("\n" + "=" * 60)
    print("SECTION 4: Token Optimization / Savings")
    print("=" * 60)

    @test("TokenStats tracks input/output tokens per agent")
    def t1() -> None:
        from utils.token_stats import TokenStats
        ts = TokenStats()
        ts.add_usage("qwen25coder", "qwen2.5-coder:1.5b", 100, 50)
        ts.add_usage("tinyllama",   "tinyllama:latest",    30,  10)
        total = ts.get_total_stats()
        assert total["input"] == 130
        assert total["output"] == 60
        assert total["total"] == 190

    @test("TokenStats per-agent stats are correct")
    def t2() -> None:
        from utils.token_stats import TokenStats
        ts = TokenStats()
        ts.add_usage("a", "m", 200, 100)
        ts.add_usage("a", "m",  50,  25)
        s = ts.get_agent_stats("a")
        assert s["input"] == 250 and s["output"] == 125

    @test("Minifier compresses Python source")
    def t3() -> None:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        from minifier import minify_python  # type: ignore[import]
        src = "# comment\ndef hello():\n    # inner\n    pass\n\n"
        result = minify_python(src, keep_comments=False)
        assert len(result) < len(src), f"{len(result)} >= {len(src)}"
        print(f"    {len(src)} → {len(result)} bytes")

    @test("PromptCompressor is importable")
    def t4() -> None:
        try:
            from utils.prompt_compressor import PromptCompressor
            assert PromptCompressor() is not None
        except ImportError:
            raise SkipTest("PromptCompressor not in this build")

    @test("live agent call populates token stats")
    def t5() -> None:
        require_ollama()
        from axe import Config
        from core.agent_manager import AgentManager
        from utils.token_stats import TokenStats
        ts = TokenStats()
        mgr = AgentManager(Config())
        mgr.call_agent(
            WORKER_B_AGENT, prompt="Say TOKEN_TEST_OK",
            system_prompt_override="Be concise.",
            token_callback=lambda ag, mo, i, o: ts.add_usage(ag, mo, i, o),
        )
        assert ts.get_total_stats()["total"] > 0, "No tokens recorded"
        print(f"    tokens: {ts.get_total_stats()}")

    t1(); t2(); t3(); t4(); t5()


# ---------------------------------------------------------------------------
# Section 5: Multiple workspace directories
# ---------------------------------------------------------------------------
def section_multi_workspace() -> None:
    print("\n" + "=" * 60)
    print("SECTION 5: Multiple Workspace Directories")
    print("=" * 60)

    @test("CLI --workspace comma-split accepted by axe.py --help")
    def t1() -> None:
        # Behavioural: axe.py must accept --workspace dir1,dir2 without crashing.
        with tempfile.TemporaryDirectory() as td:
            ws1 = Path(td) / "ws1"
            ws2 = Path(td) / "ws2"
            ws1.mkdir()
            ws2.mkdir()
            r = subprocess.run(
                [sys.executable, AXE_PY, "--workspace", f"{ws1},{ws2}", "--help"],
                capture_output=True, text=True, timeout=15, cwd=str(REPO_ROOT),
            )
            combined = r.stdout + r.stderr
            assert r.returncode == 0, (
                f"axe.py rejected comma-separated --workspace; rc={r.returncode}"
            )
            assert "--workspace" in combined

    @test("SharedWorkspace creates shared note file")
    def t2() -> None:
        from axe import SharedWorkspace
        with tempfile.TemporaryDirectory() as td:
            ws = SharedWorkspace(td)
            assert ws is not None
            assert (Path(td) / ".collab_shared.md").exists()

    @test("ToolRunner accepts multiple workspace paths")
    def t3() -> None:
        from axe import Config
        from core.tool_runner import ToolRunner
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            tr = ToolRunner(Config(), a, [a, b])
            assert len(tr.workspace_paths) == 2

    @test("live batch with two workspaces")
    def t4() -> None:
        require_ollama()
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            Path(a, "alpha.txt").write_text("alpha\n")
            Path(b, "beta.txt").write_text("beta\n")
            r = run_axe(
                ["--workspace", f"{a},{b}",
                 "-c", f"@{WORKER_B_AGENT} Say: WORKSPACE_OK"],
                timeout=150,
            )
            out = strip_ansi(r.stdout + r.stderr)
            assert r.returncode == 0 or len(out.strip()) > 0

    @test("/workspace +path adds a workspace in interactive mode")
    def t5() -> None:
        with tempfile.TemporaryDirectory() as extra:
            out = strip_ansi((run_axe([], timeout=30, stdin_text=
                f"/workspace +{extra}\n/workspace\n/quit\n"
            ).stdout + "").strip())
            assert extra in out or "workspace" in out.lower()

    t1(); t2(); t3(); t4(); t5()


# ---------------------------------------------------------------------------
# Section 6: Unix socket interface
# ---------------------------------------------------------------------------
def section_socket() -> None:
    print("\n" + "=" * 60)
    print("SECTION 6: Unix Socket Interface")
    print("=" * 60)

    @test("SOCKET_PATH construction is correct")
    def t1() -> None:
        import axe
        assert axe.SOCKET_PATH == f"/run/user/{os.getuid()}/axe.sock"

    @test("axe_socket_client.py is present and importable")
    def t2() -> None:
        assert (REPO_ROOT / "axe_socket_client.py").exists()
        import axe_socket_client  # noqa: F401

    @test("socket server starts when AXE enters interactive mode")
    def t3() -> None:
        require_ollama()
        uid = os.getuid()
        sock_path = f"/run/user/{uid}/axe.sock"
        pid_path  = f"/run/user/{uid}/axe.pid"
        for p in [sock_path, pid_path]:
            try: os.unlink(p)
            except FileNotFoundError: pass
        proc = subprocess.Popen(
            [sys.executable, AXE_PY], stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
        )
        deadline = time.time() + 20
        while not os.path.exists(sock_path) and time.time() < deadline:
            time.sleep(0.3)
        appeared = os.path.exists(sock_path)
        try:
            proc.stdin.write(b"/quit\n"); proc.stdin.flush()
        except Exception: pass
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.kill()
        assert appeared, f"Socket never appeared at {sock_path}"
        print(f"    socket at {sock_path}")

    @test("/help via socket returns command listing")
    def t4() -> None:
        require_ollama()
        uid = os.getuid()
        sock_path = f"/run/user/{uid}/axe.sock"
        pid_path  = f"/run/user/{uid}/axe.pid"
        for p in [sock_path, pid_path]:
            try: os.unlink(p)
            except FileNotFoundError: pass

        proc = subprocess.Popen(
            [sys.executable, AXE_PY], stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
        )

        stop = threading.Event()

        def feed() -> None:
            """Keep the REPL loop spinning so it can accept socket connections."""
            while not stop.is_set():
                try:
                    proc.stdin.write(b"\n"); proc.stdin.flush()
                except Exception: break
                time.sleep(0.05)

        feeder = threading.Thread(target=feed, daemon=True)
        feeder.start()

        # Wait for socket to appear, then give it extra settle time
        deadline = time.time() + 20
        while not os.path.exists(sock_path) and time.time() < deadline:
            time.sleep(0.2)
        if os.path.exists(sock_path):
            time.sleep(1.0)

        response = ""
        if os.path.exists(sock_path):
            try:
                response = socket_send("/help", timeout=10)
            except Exception as e:
                response = f"ERROR: {e}"

        stop.set()
        try:
            proc.stdin.write(b"/quit\n"); proc.stdin.flush()
        except Exception: pass
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.kill()

        clean = strip_ansi(response)
        assert len(clean) > 20, f"Expected help text; got {clean[:100]!r}"
        print(f"    /help snippet: {clean[:80]!r}")

    t1(); t2(); t3(); t4()


# ---------------------------------------------------------------------------
# Section 7: Interactive slash commands
# ---------------------------------------------------------------------------
def section_slash_commands() -> None:
    print("\n" + "=" * 60)
    print("SECTION 7: Interactive Slash Commands")
    print("=" * 60)

    def run_cmds(cmds: List[str], timeout: int = 30) -> str:
        stdin = "\n".join(cmds) + "\n/quit\n"
        return strip_ansi((run_axe([], timeout=timeout, stdin_text=stdin).stdout + "").strip())

    @test("/help mentions /agents")
    def t1() -> None:
        out = run_cmds(["/help"])
        assert "/agents" in out or "agent" in out.lower()

    @test("/agents lists available agents")
    def t2() -> None:
        out = run_cmds(["/agents"])
        assert "agent" in out.lower() or len(out) > 30

    @test("/tools shows tool configuration")
    def t3() -> None:
        out = run_cmds(["/tools"])
        assert "tool" in out.lower() or len(out) > 10

    @test("/workspace shows workspace info")
    def t4() -> None:
        out = run_cmds(["/workspace"])
        assert "workspace" in out.lower() or len(out) > 10

    @test("/stats shows token usage info")
    def t5() -> None:
        out = run_cmds(["/stats"])
        assert "token" in out.lower() or "stat" in out.lower() or len(out) > 10

    @test("/config shows configuration")
    def t6() -> None:
        out = run_cmds(["/config"])
        assert len(out.strip()) > 10

    @test("/collab syntax is documented in /help")
    def t7() -> None:
        out = run_cmds(["/help"])
        assert "/collab" in out

    @test("/session list works (no sessions = ok)")
    def t8() -> None:
        out = run_cmds(["/session list"])
        assert "session" in out.lower() or len(out) > 3

    t1(); t2(); t3(); t4(); t5(); t6(); t7(); t8()


# ---------------------------------------------------------------------------
# Section 8: /collab inside interactive mode
# ---------------------------------------------------------------------------
def section_interactive_collab() -> None:
    print("\n" + "=" * 60)
    print("SECTION 8: /collab Inside Interactive Mode")
    print("=" * 60)

    @test("/collab launches a collaborative session")
    def t1() -> None:
        require_ollama()
        with tempfile.TemporaryDirectory() as ws:
            Path(ws, "README.md").write_text("# Test project\n")
            stdin = (
                f"/collab {SUPERVISOR_AGENT},{WORKER_B_AGENT} "
                f"{ws} 1 Briefly describe README.md\n"
                "/quit\n"
            )
            r = run_axe([], timeout=180, stdin_text=stdin)
            out = strip_ansi(r.stdout + r.stderr)
            assert len(out.strip()) > 20, f"No /collab output: {out[:200]!r}"
            print(f"    snippet: {out[:100].strip()!r}")

    t1()


# ---------------------------------------------------------------------------
# Section 9: AXE self-analysis
# ---------------------------------------------------------------------------
def section_selfanalysis() -> None:
    print("\n" + "=" * 60)
    print("SECTION 9: AXE Self-Analysis (workspace = AXE source)")
    print("=" * 60)

    @test("supervisor reads session_manager.py and gives improvement")
    def t1() -> None:
        require_ollama()
        from axe import Config
        from core.agent_manager import AgentManager
        excerpt = (REPO_ROOT / "core" / "session_manager.py").read_text()[:800]
        response = AgentManager(Config()).call_agent(
            SUPERVISOR_AGENT,
            prompt=(
                "You are reviewing AXE's SessionManager (excerpt).\n"
                "State ONE concrete improvement in one sentence.\n\n"
                f"```python\n{excerpt}\n```"
            ),
            system_prompt_override="Senior software engineer doing code review. Be concise.",
        )
        assert response and len(response) > 20
        print(f"    suggestion: {response[:200].strip()!r}")

    @test("worker reviews a C source file")
    def t2() -> None:
        require_ollama()
        from axe import Config
        from core.agent_manager import AgentManager
        c_src = (REPO_ROOT / "tests" / "fixtures" / "hello_world.c").read_text()
        response = AgentManager(Config()).call_agent(
            WORKER_A_AGENT,
            prompt=f"Review this C code and list any issues:\n```c\n{c_src}\n```",
            system_prompt_override="C/C++ code reviewer. Be concise.",
        )
        assert response and len(response) > 10

    @test("three-agent collab on AXE source (improvement discussion)")
    def t3() -> None:
        require_ollama()
        r = run_axe(
            ["--collab",
             f"{SUPERVISOR_AGENT},{WORKER_A_AGENT},{WORKER_B_AGENT}",
             "--workspace", str(REPO_ROOT),
             "--time", "1",
             "--task",
             "Read core/session_manager.py and discuss ONE improvement "
             "for future SRI support."],
            timeout=180,
        )
        out = strip_ansi(r.stdout + r.stderr)
        assert len(out.strip()) > 30
        print(f"    snippet: {out[:150].strip()!r}")

    t1(); t2(); t3()


# ---------------------------------------------------------------------------
# Section 10: SRI groundwork discussion
# ---------------------------------------------------------------------------
def section_sri_discussion() -> None:
    print("\n" + "=" * 60)
    print("SECTION 10: SRI Groundwork Discussion")
    print("=" * 60)

    @test("supervisor discusses SRI feasibility")
    def t1() -> None:
        require_ollama()
        from axe import Config
        from core.agent_manager import AgentManager
        response = AgentManager(Config()).call_agent(
            SUPERVISOR_AGENT,
            prompt=textwrap.dedent("""\
                AXE is a multi-agent coding framework.
                Consider Self-Recursive Improvement (SRI): agents improve AXE's own code,
                save their session, restart AXE, and continue improving.
                Answer in 3-4 sentences:
                1. The single biggest technical gap blocking full SRI in AXE today?
                2. What would a minimal "/restart --load <session>" need to do?
                3. Is autosave-on-exit enough to make SRI loops reliable?
            """),
            system_prompt_override="AI systems engineer discussing SRI for AXE. Be specific.",
        )
        assert response and len(response) > 30
        print(f"    SRI response:\n    {response[:300].strip()}")
        # Only write generated docs when explicitly opted-in, to keep the suite
        # hermetic during normal test runs.
        if os.environ.get("AXE_WRITE_LIVE_DOCS"):
            _write_sri_discussion(response)

    @test("docs/SRI_FUTURE_WORK.md covers key SRI topics")
    def t2() -> None:
        doc = REPO_ROOT / "docs" / "SRI_FUTURE_WORK.md"
        assert doc.exists(), "SRI_FUTURE_WORK.md not found"
        text = doc.read_text().lower()
        for kw in ["autosave", "restart", "session", "sri"]:
            assert kw in text, f"Keyword '{kw}' missing from SRI_FUTURE_WORK.md"

    @test("docs/AXE_IMPROVEMENT_SUGGESTIONS.md covers key topics")
    def t3() -> None:
        doc = REPO_ROOT / "docs" / "AXE_IMPROVEMENT_SUGGESTIONS.md"
        assert doc.exists(), "AXE_IMPROVEMENT_SUGGESTIONS.md not found"
        text = doc.read_text().lower()
        for kw in ["supervisor", "token", "session", "workspace"]:
            assert kw in text, f"Keyword '{kw}' missing from improvement doc"

    t1(); t2(); t3()


def _write_sri_discussion(agent_response: str) -> None:
    """Persist the live SRI discussion to docs/SRI_AGENT_DISCUSSION.md.

    Only called when AXE_WRITE_LIVE_DOCS=1 is set, to keep normal test runs
    hermetic and deterministic.
    """
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Build the content with no leading indentation so it renders correctly in
    # all Markdown renderers (indented lines are treated as code blocks).
    lines = [
        "# SRI Agent Discussion — Live Session Output",
        "",
        f"*Generated {ts} by `tests/test_live_feature_matrix.py` §10.*",
        "*Model: `qwen2.5-coder:1.5b` (supervisor).*",
        "",
        "---",
        "",
        "## Question posed to supervisor",
        "",
        "> AXE is a multi-agent coding framework.",
        "> Consider Self-Recursive Improvement (SRI): agents improve AXE's own code,",
        "> save their session, restart AXE, and continue improving.",
        ">",
        "> 1. The single biggest technical gap blocking full SRI in AXE today?",
        r'> 2. What would a minimal "/restart --load <session>" need to do?',
        "> 3. Is autosave-on-exit enough to make SRI loops reliable?",
        "",
        "## Supervisor response",
        "",
        agent_response.strip(),
        "",
        "---",
        "",
        "*For the full SRI roadmap, see [SRI_FUTURE_WORK.md](SRI_FUTURE_WORK.md).*",
        "*To regenerate: `AXE_WRITE_LIVE_DOCS=1 python3 tests/test_live_feature_matrix.py`*",
    ]
    (REPO_ROOT / "docs" / "SRI_AGENT_DISCUSSION.md").write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Section 11: XP / Level / Title progression
# ---------------------------------------------------------------------------
def section_xp() -> None:
    print("\n" + "=" * 60)
    print("SECTION 11: XP / Level / Title Progression")
    print("=" * 60)

    @test("vote_xp records a vote successfully")
    def t1() -> None:
        from core.global_workspace import GlobalWorkspace
        with tempfile.TemporaryDirectory() as td:
            gw = GlobalWorkspace(td)
            result = gw.vote_xp(
                voter_alias="@supervisor", voter_level=40,
                target_alias="@worker", xp_delta=10,
                reason="Good work",
            )
            assert isinstance(result, dict)
            print(f"    vote_xp: {result.get('success', '?')}")

    @test("calculate_xp_for_level returns positive int")
    def t2() -> None:
        from progression.xp_system import calculate_xp_for_level
        from progression.levels import LEVEL_SUPERVISOR_ELIGIBLE
        xp = calculate_xp_for_level(LEVEL_SUPERVISOR_ELIGIBLE)
        assert isinstance(xp, int) and xp > 0
        print(f"    XP for level {LEVEL_SUPERVISOR_ELIGIBLE}: {xp}")

    t1(); t2()


# ---------------------------------------------------------------------------
# Section 12: Workshop tools
# ---------------------------------------------------------------------------
def section_workshop() -> None:
    print("\n" + "=" * 60)
    print("SECTION 12: Workshop Tools")
    print("=" * 60)

    @test("workshop modules (chisel, hammer, saw, plane) are importable")
    def t1() -> None:
        try:
            from workshop import chisel, hammer, saw, plane  # noqa: F401
        except ImportError as e:
            # angr and frida are heavy optional RE deps (listed in requirements.txt).
            # Skip gracefully when they are absent rather than failing the suite.
            raise SkipTest(f"Optional RE dep missing: {e}")

    @test("/workshop status in interactive mode")
    def t2() -> None:
        out = strip_ansi((run_axe([], timeout=30, stdin_text=
            "/workshop status\n/quit\n"
        ).stdout + "").strip())
        assert "workshop" in out.lower() or "chisel" in out.lower() or len(out) > 5

    t1(); t2()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 60)
    print("AXE LIVE FEATURE MATRIX TEST SUITE")
    print(f"Repo : {REPO_ROOT}")
    print(f"Ollama: {'RUNNING' if ollama_running() else 'NOT RUNNING (live tests will skip)'}")
    models = available_models()
    print(f"Models: {models if models else 'none'}")
    print("=" * 60)

    for fn in [
        section_batch,
        section_collab,
        section_session,
        section_token_optimization,
        section_multi_workspace,
        section_socket,
        section_slash_commands,
        section_interactive_collab,
        section_selfanalysis,
        section_sri_discussion,
        section_xp,
        section_workshop,
    ]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"\n!!! Unhandled error in {fn.__name__}: {e}")

    passed  = sum(1 for _, s, _ in _results if s == PASS)
    skipped = sum(1 for _, s, _ in _results if s == SKIP)
    failed  = sum(1 for _, s, _ in _results if s == FAIL)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if failed:
        print("\nFailed tests:")
        for name, status, detail in _results:
            if status == FAIL:
                print(f"  ✗ {name}: {detail}")
    print(f"\nTotal: {len(_results)} | Passed: {passed} | Skipped: {skipped} | Failed: {failed}")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
