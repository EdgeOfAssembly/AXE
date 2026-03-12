# AXE Testing Guide

This document covers how to set up the AXE test environment, which models to
use, and how to run every layer of the test suite.

---

## Quick Start

```bash
# 1. Install all dependencies and build RE toolchain
bash scripts/setup_env.sh

# 2. Activate the Python venv created by setup_env.sh (optional but recommended)
source venv/bin/activate   # or your venv location

# 3. Run the main test suite
python3 tests/test_end_to_end.py

# 4. Run individual test modules
python3 tests/test_skills_manager.py
python3 tests/test_socket_interface.py
python3 tests/test_workshop.py
python3 tests/test_token_optimization.py
python3 tests/test_xp_voting.py
python3 tests/test_sandbox.py
```

---

## Dependency Installation

`scripts/setup_env.sh` handles all dependencies.  Key packages:

| Package | Purpose |
|---|---|
| `python-xlib` | X11 keyboard automation for keypress |
| `capstone` (Python) | Disassembly in test fixtures |
| `libcapstone-dev` | C library for building dumpexe |
| `libsdl2-dev` | SDL2 headers for dosbox-staging |
| `libfluidsynth-dev` / `fluidsynth` | MIDI synthesis for dosbox-staging |
| `xvfb` | Virtual X11 framebuffer for headless GUI tests |
| `cmake`, `ninja-build` | Build system for dosbox-staging |
| `gcc-14` / `g++-14` | C++23 support required by dumpexe |

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-xlib libcapstone-dev \
    libsdl2-dev libsdl2-image-dev libfluidsynth-dev fluidsynth \
    xvfb cmake ninja-build nasm \
    build-essential gcc-14 g++-14 libpng-dev libspeexdsp-dev libasound2-dev
pip install python-xlib capstone filelock
```

---

## Ollama Setup

AXE uses local Ollama models for offline testing.  Three models are pulled by
`setup_env.sh`:

| Model | Size | Role | Why |
|---|---|---|---|
| `qwen2.5-coder:1.5b` | ~0.9–1.2 GB | **Supervisor** | Best structured code output |
| `qwen2.5:1.5b` | ~0.9–1.2 GB | Worker A | Strong reasoning, good for RE |
| `tinyllama` | ~0.6 GB | Worker B | Ultra-fast smoke tests |

All three run on CPU-only hardware (no GPU required).

```bash
# Install latest Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the server
ollama serve &

# Pull models
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5:1.5b
ollama pull tinyllama
```

Tests that require Ollama are automatically **skipped** when the server is not
running, so the suite still passes offline.

---

## Helper Tool Setup

### `/tmp/bin` and PATH

`setup_env.sh` creates symlinks in `/tmp/bin` for the three key tools:

```
/tmp/bin/dosbox      → tools/dosbox-staging/build/dosbox
/tmp/bin/dumpexe     → tools/dumpexe/dumpexe
/tmp/bin/keypress.py → tools/keypress/keypress.py
```

Add `/tmp/bin` to your PATH:

```bash
export PATH="/tmp/bin:$PATH"
```

The CI workflow (`copilot-setup-steps.yml`) does this automatically.

### Building dosbox-staging

dosbox-staging requires SDL2, FluidSynth, and several other libraries.
`setup_env.sh` handles this, but manual build steps are:

```bash
cd tools/dosbox-staging

# Apply patches (guard optional deps behind OPT_* flags)
for p in ../../scripts/patches/dosbox-staging/*.patch; do
    git apply --whitespace=fix "$p" 2>/dev/null || true
done

# Configure (headless: no OpenGL, no Opus, no MT-32)
cmake -S . -B build -G "Unix Makefiles" \
    -DOPT_OPUS=OFF \
    -DOPT_OPENGL=OFF \
    -DOPT_MT32EMU=OFF \
    -DOPT_TESTS=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -Wno-dev

# Build
make -s -C build -j"$(nproc)"
```

Headless usage (no real display required):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    tools/dosbox-staging/build/dosbox \
    -conf tools/dosbox-staging/dosbox-staging.conf \
    -c "MYPROGRAM.EXE" --exit
```

### Building dumpexe

```bash
cd tools/dumpexe
make CXX=g++-14    # or just make if g++14 is default

# Test it
./dumpexe -a tests/fixtures/dos_binaries/4dos595/4HELP.EXE
```

See `tests/fixtures/dumpexe_samples/` for pre-captured reference output.

---

## Test Suite Overview

### `tests/test_end_to_end.py`  (main suite)

17 sections covering every README-documented AXE feature.  Exit code 0 = all
pass or skip; exit code 1 = at least one failure.

```
Section 1:  CLI option parsing
Section 2:  Batch mode
Section 3:  Collaborative session initialisation + workspace paths
Section 4:  Unix socket interface
Section 5:  Interactive slash commands
Section 6:  Session management (/session save / load / list)
Section 7:  Token optimisation
Section 8:  Workshop tools
Section 9:  Agent Skills system
Section 10: Sandbox security
Section 11: XP/Level progression
Section 12: Subsumption architecture
Section 13: Global Workspace / Arbitration
Section 14: Live Ollama integration (skipped if server not running)
Section 15: Keypress interactive test infrastructure
Section 16: Test fixtures
Section 17: RE toolchain (dumpexe, HaxBox, dosbox-staging)
```

### Other test modules

| Module | What it tests |
|---|---|
| `test_skills_manager.py` | Skill loading, manifest, injection |
| `test_socket_interface.py` | Unix socket server/client |
| `test_workshop.py` | Chisel, Hammer, Saw, Plane workshop tools |
| `test_token_optimization.py` | Context compression, minifier |
| `test_xp_voting.py` | XP awards, level progression, title system |
| `test_sandbox.py` | Bubblewrap blacklist enforcement |
| `test_interactive_keypress.py` | Keypress-driven interactive mode (needs Xvfb) |
| `test_collab_integration.py` | End-to-end collaboration session |
| `test_ollama_integration.py` | Ollama-specific integration (needs server) |

### Running interactive/GUI tests with Xvfb

```bash
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
python3 tests/test_interactive_keypress.py
```

---

## Feature Validation Checklist

The following features are documented in `README.md` and validated by the test
suite:

- [x] Batch mode (`-c "@agent task"`)
- [x] Interactive mode (slash commands, session management)
- [x] Unix socket bidirectional interface
- [x] `/collab` collaborative session
- [x] Session save / load (`/session save` / `/session load`)
- [x] Token optimization (compression, summarization)
- [x] Multiple workspace directories (`--workspace a,b`, `/workspace +path`)
- [x] Workshop tools (Chisel, Hammer, Saw, Plane)
- [x] Agent Skills system (25+ domain-specific skills)
- [x] Sandbox security (Bubblewrap, blacklist)
- [x] XP/Level/Title progression
- [x] Subsumption architecture
- [x] Global Workspace / Arbitration Protocol
- [x] keypress-driven interactive testing
- [x] RE toolchain (dumpexe, dosbox-staging, DOS fixtures)
- [ ] Live Ollama collab (requires `ollama serve` + pulled models)

---

## Patches for dosbox-staging

Six patches are stored in `scripts/patches/dosbox-staging/` and applied
automatically by `setup_env.sh`:

| Patch | Description |
|---|---|
| `0001-guard-opengl-link.patch` | Wraps `OpenGL::GL` behind `OPT_OPENGL` generator expression |
| `0002-fix-zlib-ng-cmakedefine01.patch` | Fixes `#if C_SYSTEM_ZLIB_NG` preprocessor usage |
| `0003-guard-fluidsynth-midi.patch` | Guards FluidSynth source/link behind `OPT_FLUIDSYNTH` |
| `0004-add-c-fluidsynth-cmakedefine.patch` | Adds `C_FLUIDSYNTH` CMake variable |
| `0005-guard-fluidsynth-source.patch` | Wraps `FSYNTH_*` references in `#if C_FLUIDSYNTH` |
| `0006-debugtrace-conf-trace-off-dedup-on.patch` | Default conf: binary dump on, dedup on, trace off |

To re-apply manually:

```bash
cd tools/dosbox-staging
for p in ../../scripts/patches/dosbox-staging/*.patch; do
    git apply --whitespace=fix "$p"
done
```

---

## Known Limitations

1. **COM-file disassembly truncation** (`dumpexe -d`): Files > ~300 bytes
   (e.g. `ARCE.COM`, 6644 bytes) produce truncated output.  Tests for COM
   files use summary (`-r`) and hexdump (`-x`) modes only; disassembly tests
   use MZ EXE or SYS files.

2. **Ollama live tests require a running server**: Tests in Section 14 and
   `test_ollama_integration.py` are skipped when `localhost:11434` is not
   reachable.  Run `ollama serve` before these tests.

3. **dosbox-staging build time**: Full build takes 3–8 minutes on a 2-core CI
   runner.  The CI workflow caches the build directory where possible.

4. **keypress X11 tests require Xvfb**: `test_interactive_keypress.py` starts
   a virtual display automatically when `Xvfb` is installed.  On systems
   without Xvfb the test is skipped.

---

## Further Reading

- [`docs/SRI_FUTURE_WORK.md`](SRI_FUTURE_WORK.md) — Self-Recursive Improvement roadmap
- [`docs/AXE_IMPROVEMENT_SUGGESTIONS.md`](AXE_IMPROVEMENT_SUGGESTIONS.md) — Concrete improvement ideas
- [`docs/socket_interface.md`](socket_interface.md) — Unix socket protocol
- [`docs/xp_voting.md`](xp_voting.md) — XP/Level/Title system
- [`scripts/patches/dosbox-staging/README.md`](../scripts/patches/dosbox-staging/README.md) — Patch details
- [`tests/fixtures/README.md`](../tests/fixtures/README.md) — Fixture descriptions and dumpexe bug notes
