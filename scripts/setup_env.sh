#!/usr/bin/env bash
# =============================================================================
# AXE Environment Setup Script
# =============================================================================
# Installs all dependencies required to run AXE and exercise every feature
# documented in README.md, including:
#   - Latest Ollama release (for local LLM support)
#   - Small local models suited for C/C++/Python coding and 16-bit x86 RE
#   - Python requirements (requirements.txt)
#   - Xvfb (headless X11 virtual framebuffer for GUI/interactive testing)
#   - EdgeOfAssembly/keypress (X11 keyboard automation for interactive tests)
#
# RE Toolchain (16-bit DOS reverse engineering):
#   - EdgeOfAssembly/dumpexe  — 16-bit MZ EXE / COM / SYS analyser & disassembler
#   - EdgeOfAssembly/HaxBox   — BBS fixture archive (real DOS EXE/COM/SYS files)
#   - EdgeOfAssembly/dosbox-staging — custom DOSBox fork with debug-trace system
#     (preferred for running/tracing MS-DOS programs; replaces dosbox-x)
#
# Usage:
#   bash scripts/setup_env.sh [options]
#
# Options:
#   --skip-models      Skip pulling Ollama models (use if already pulled)
#   --skip-xvfb        Skip installing Xvfb packages
#   --skip-keypress    Skip installing EdgeOfAssembly/keypress
#   --skip-re-tools    Skip cloning / building RE toolchain (dumpexe, HaxBox, dosbox-staging)
#   --help             Show this help message
#
# Models pulled (all ≤ 2 GB, CPU-friendly):
#   qwen2.5-coder:1.5b  — Qwen 2.5 Coder 1.5B: strong C/C++/Python coding model
#   qwen2.5:1.5b        — Qwen 2.5 1.5B: general-purpose reasoning; good for RE
#   tinyllama:latest    — TinyLlama 1.1B: ultra-fast smoke-test model
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
SKIP_MODELS=false
SKIP_XVFB=false
SKIP_KEYPRESS=false
SKIP_RE_TOOLS=false

for arg in "$@"; do
    case "$arg" in
        --skip-models)   SKIP_MODELS=true ;;
        --skip-xvfb)     SKIP_XVFB=true ;;
        --skip-keypress) SKIP_KEYPRESS=true ;;
        --skip-re-tools) SKIP_RE_TOOLS=true ;;
        --help|-h)
            sed -n '2,35p' "$0" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()  { echo "[setup_env] $*"; }
ok()   { echo "[setup_env] ✓ $*"; }
warn() { echo "[setup_env] ⚠ $*" >&2; }
fail() { echo "[setup_env] ✗ $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------------------
# 1. Detect OS and package manager
# ---------------------------------------------------------------------------
log "Detecting OS..."
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
elif command -v brew &>/dev/null; then
    PKG_MGR="brew"
else
    warn "No recognised package manager found; skipping system package installation."
    PKG_MGR="none"
fi
ok "Package manager: $PKG_MGR"

# ---------------------------------------------------------------------------
# 2. Install system dependencies (curl, python3-xlib for keypress)
# ---------------------------------------------------------------------------
log "Installing system dependencies..."
case "$PKG_MGR" in
    apt)
        sudo apt-get update -qq
        sudo apt-get install -y --no-install-recommends \
            curl wget git python3-xlib python3-pip \
            build-essential libcapstone-dev gcc-14 g++-14 nasm
        ;;
    dnf)
        sudo dnf install -y curl wget git python3-xlib python3-pip \
            gcc gcc-c++ capstone-devel nasm
        ;;
    pacman)
        sudo pacman -Sy --noconfirm curl wget git python-xlib python-pip \
            base-devel capstone nasm
        ;;
    brew)
        brew install curl wget git
        # python-xlib not available via brew; install via pip later
        ;;
    *)
        warn "Skipping system package install."
        ;;
esac
ok "System dependencies installed."

# ---------------------------------------------------------------------------
# 3. Install Xvfb (headless X11 virtual framebuffer)
# ---------------------------------------------------------------------------
if [ "$SKIP_XVFB" = false ]; then
    log "Installing Xvfb for headless X11 testing..."
    case "$PKG_MGR" in
        apt)
            sudo apt-get install -y --no-install-recommends xvfb x11-xserver-utils xterm
            ;;
        dnf)
            sudo dnf install -y xorg-x11-server-Xvfb xterm
            ;;
        pacman)
            sudo pacman -Sy --noconfirm xorg-server-xvfb xterm
            ;;
        brew)
            warn "Xvfb is Linux-only; skipping on macOS. Interactive/GUI tests will be skipped."
            ;;
        *)
            warn "Cannot install Xvfb automatically; install manually if interactive tests are needed."
            ;;
    esac
    ok "Xvfb installed (or skipped on unsupported platform)."
else
    log "Skipping Xvfb install (--skip-xvfb)."
fi

# ---------------------------------------------------------------------------
# 4. Install Python requirements for AXE (in a dedicated virtual environment)
# ---------------------------------------------------------------------------
# Use a venv to avoid modifying the system Python and to stay compatible with
# distros that enforce PEP 668 (externally-managed environments).
VENV_DIR="${REPO_ROOT}/.venv"
VENV_PY="${VENV_DIR}/bin/python3"
VENV_PIP="${VENV_DIR}/bin/pip"

if [ ! -x "$VENV_PY" ]; then
    log "Creating Python virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    ok "Virtual environment created."
fi

log "Installing Python requirements for AXE..."
"$VENV_PIP" install --upgrade pip -q
if [ -f "$REPO_ROOT/requirements.txt" ]; then
    "$VENV_PIP" install -r "$REPO_ROOT/requirements.txt" -q
    ok "Python requirements installed into $VENV_DIR."
else
    warn "requirements.txt not found at $REPO_ROOT/requirements.txt"
fi

# python-xlib for keypress (X11 keyboard automation)
"$VENV_PIP" install python-xlib -q 2>/dev/null || true
ok "Hint: activate the venv with:  source $VENV_DIR/bin/activate"

# ---------------------------------------------------------------------------
# 5. Install latest Ollama
# ---------------------------------------------------------------------------
log "Installing latest Ollama..."
OLLAMA_VERSION_REQUIRED="0.17.7"  # Current latest as of setup script authoring; script auto-detects newer

# Fetch the latest tag from GitHub Releases API
LATEST_OLLAMA=$(curl -s --max-time 15 \
    "https://api.github.com/repos/ollama/ollama/releases/latest" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tag_name','v${OLLAMA_VERSION_REQUIRED}'))" \
    2>/dev/null || echo "v${OLLAMA_VERSION_REQUIRED}")

log "Latest Ollama release: $LATEST_OLLAMA"

# Download the installer to a temp file rather than piping directly to sh.
# This allows optional checksum verification and makes the install auditable.
_install_ollama() {
    local installer="${TMPDIR:-/tmp}/ollama-install-$$.sh"
    log "Downloading Ollama installer..."
    curl -fsSLo "$installer" "https://ollama.ai/install.sh"
    # Optional: set OLLAMA_INSTALL_SHA256 in the environment for pinned installs.
    if [ -n "${OLLAMA_INSTALL_SHA256:-}" ]; then
        log "Verifying Ollama installer checksum..."
        echo "${OLLAMA_INSTALL_SHA256}  $installer" | sha256sum -c -
    fi
    sh "$installer"
    rm -f "$installer"
}

# Check if already installed and up to date
if command -v ollama &>/dev/null; then
    INSTALLED_VER=$(ollama --version 2>&1 | grep -oP '[\d]+\.[\d]+\.[\d]+' | head -1 || echo "0.0.0")
    REQUIRED_VER="${LATEST_OLLAMA#v}"
    if [ "$INSTALLED_VER" = "$REQUIRED_VER" ]; then
        ok "Ollama $INSTALLED_VER already installed and up to date."
    else
        log "Updating Ollama from $INSTALLED_VER to $REQUIRED_VER..."
        _install_ollama
        ok "Ollama updated to $(ollama --version 2>&1 | head -1)."
    fi
else
    log "Ollama not found; installing..."
    _install_ollama
    ok "Ollama installed: $(ollama --version 2>&1 | head -1)."
fi

# ---------------------------------------------------------------------------
# 6. Start Ollama server (if not already running)
# ---------------------------------------------------------------------------
log "Ensuring Ollama server is running..."
if ! curl -s --max-time 3 http://localhost:11434/api/tags &>/dev/null; then
    log "Starting Ollama server in background..."
    nohup ollama serve &>/tmp/ollama_server.log &
    OLLAMA_PID=$!
    log "Ollama server PID: $OLLAMA_PID"
    # Wait up to 30 s for it to be ready
    for i in $(seq 1 30); do
        if curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
            ok "Ollama server is ready."
            break
        fi
        sleep 1
        if [ "$i" -eq 30 ]; then
            warn "Ollama server did not respond in 30 s; model pulls may fail."
        fi
    done
else
    ok "Ollama server already running."
fi

# ---------------------------------------------------------------------------
# 7. Pull local models
# ---------------------------------------------------------------------------
# Model selection rationale:
#   qwen2.5-coder:1.5b — Qwen 2.5 Coder 1.5B (≈ 1 GB).  Best-in-class small
#                         model for C, C++, and Python.  Understands structs,
#                         pointers, memory layout — ideal for RE assistance.
#   qwen2.5:1.5b       — Qwen 2.5 general 1.5B (≈ 1 GB).  Strong reasoning,
#                         useful for analysing binary data and 16-bit x86 DOS
#                         code commentary.  Paired with qwen2.5-coder for
#                         diversity in collaboration mode.
#   tinyllama:latest   — TinyLlama 1.1B (≈ 600 MB).  Ultra-fast smoke-test
#                         model.  Used by existing test_ollama_integration.py
#                         tests; kept for backward compatibility and speed.
MODELS=(
    "qwen2.5-coder:1.5b"
    "qwen2.5:1.5b"
    "tinyllama:latest"
)

if [ "$SKIP_MODELS" = false ]; then
    log "Pulling local Ollama models (this may take a while on first run)..."
    for MODEL in "${MODELS[@]}"; do
        log "Pulling $MODEL ..."
        if ollama pull "$MODEL"; then
            ok "Model pulled: $MODEL"
        else
            warn "Failed to pull $MODEL; continuing."
        fi
    done
    ok "Model pull complete."
    log "Installed models:"
    ollama list
else
    log "Skipping model pull (--skip-models)."
fi

# ---------------------------------------------------------------------------
# 8. Install EdgeOfAssembly/keypress
# ---------------------------------------------------------------------------
if [ "$SKIP_KEYPRESS" = false ]; then
    KEYPRESS_DIR="$REPO_ROOT/tools/keypress"
    log "Installing EdgeOfAssembly/keypress into $KEYPRESS_DIR ..."

    if [ -d "$KEYPRESS_DIR/.git" ]; then
        log "keypress already cloned; pulling latest..."
        git -C "$KEYPRESS_DIR" pull --ff-only 2>/dev/null || true
    else
        git clone --depth=1 https://github.com/EdgeOfAssembly/keypress.git "$KEYPRESS_DIR"
    fi

    chmod +x "$KEYPRESS_DIR/keypress.py"
    ok "keypress installed at $KEYPRESS_DIR/keypress.py"

    # Symlink into tools root for convenience
    if [ ! -L "$REPO_ROOT/tools/keypress.py" ]; then
        ln -sf "$KEYPRESS_DIR/keypress.py" "$REPO_ROOT/tools/keypress.py" 2>/dev/null || true
        ok "Symlink created: tools/keypress.py -> keypress/keypress.py"
    fi
else
    log "Skipping keypress install (--skip-keypress)."
fi

# ---------------------------------------------------------------------------
# 9. Clone and build EdgeOfAssembly/dumpexe
# ---------------------------------------------------------------------------
# dumpexe is a 16-bit MS-DOS binary analyser that can decode MZ EXE headers,
# relocation tables, COM flat-binaries, and SYS device drivers, and can
# produce x86-16 disassembly via Capstone.  It is used in AXE RE tests to
# produce structured text that agents then annotate.
#
# Requirements: GCC 14 (std::format / C++23), libcapstone-dev
# ---------------------------------------------------------------------------
DUMPEXE_DIR="$REPO_ROOT/tools/dumpexe"

if [ "$SKIP_RE_TOOLS" = false ]; then
    log "Installing EdgeOfAssembly/dumpexe ..."

    if [ -d "$DUMPEXE_DIR/.git" ]; then
        log "dumpexe already cloned; pulling latest..."
        git -C "$DUMPEXE_DIR" pull --ff-only 2>/dev/null || true
    else
        git clone --depth=1 https://github.com/EdgeOfAssembly/dumpexe.git "$DUMPEXE_DIR"
    fi

    # Build dumpexe (requires GCC 14 and libcapstone-dev)
    if command -v g++-14 &>/dev/null && pkg-config --exists capstone 2>/dev/null; then
        log "Building dumpexe with GCC 14..."
        make -s -C "$DUMPEXE_DIR" CXX=g++-14 && ok "dumpexe built: $DUMPEXE_DIR/dumpexe" || \
            warn "dumpexe build failed; RE tests that need it will be skipped."
    elif command -v g++ &>/dev/null; then
        log "Trying to build dumpexe with default g++ (may need GCC 14 for C++23)..."
        make -s -C "$DUMPEXE_DIR" && ok "dumpexe built: $DUMPEXE_DIR/dumpexe" || \
            warn "dumpexe build failed; RE tests that need it will be skipped."
    else
        warn "g++ not found; skipping dumpexe build.  Install: apt install build-essential gcc-14 libcapstone-dev"
    fi

    # ---------------------------------------------------------------------------
    # 10. Clone EdgeOfAssembly/HaxBox (DOS fixture files)
    # ---------------------------------------------------------------------------
    # HaxBox/tests/BBS contains real 16-bit DOS programs from the BBS era:
    #   4dos595/ — 4DOS 5.95 shell: 4HELP.EXE, HELPCFG.EXE, OPTION.EXE, 4DOS.COM, KSTACK.COM
    #   Various .SYS device drivers (HIMEM.SYS, ANSI.SYS, …)
    # These are used as RE test fixtures: agents read dumpexe output and are
    # asked to describe the binary's structure, INT 21h usage, etc.
    # ---------------------------------------------------------------------------
    HAXBOX_DIR="$REPO_ROOT/tools/HaxBox"
    FIXTURES_DIR="$REPO_ROOT/tests/fixtures/dos_binaries"

    log "Cloning EdgeOfAssembly/HaxBox (DOS fixture archive)..."

    if [ -d "$HAXBOX_DIR/.git" ]; then
        log "HaxBox already cloned; pulling latest..."
        git -C "$HAXBOX_DIR" pull --ff-only 2>/dev/null || true
    else
        git clone --depth=1 https://github.com/EdgeOfAssembly/HaxBox.git "$HAXBOX_DIR"
    fi

    # Create fixtures symlink (or copy) so tests can reference files without
    # knowing the full HaxBox path.
    mkdir -p "$FIXTURES_DIR"

    BBS_SRC="$HAXBOX_DIR/tests/BBS"
    if [ -d "$BBS_SRC" ]; then
        # Symlink each immediate child (directory and file) into fixtures/dos_binaries/
        for item in "$BBS_SRC"/*; do
            name="$(basename "$item")"
            target="$FIXTURES_DIR/$name"
            if [ ! -e "$target" ] && [ ! -L "$target" ]; then
                ln -sf "$item" "$target"
            fi
        done
        ok "DOS fixture symlinks created in $FIXTURES_DIR"
    else
        warn "HaxBox BBS directory not found at $BBS_SRC"
    fi

    # ---------------------------------------------------------------------------
    # 11. Clone and build EdgeOfAssembly/dosbox-staging (debug-trace DOSBox fork)
    # ---------------------------------------------------------------------------
    # The EdgeOfAssembly fork adds a [debugtrace] section: logs every INT call,
    # file I/O, and video mode switch; and writes a compact binary opcode dump
    # for post-run disassembly.  This is the PREFERRED way to run and trace
    # 16-bit DOS programs in AXE RE workflows.  dosbox-x is deprecated.
    #
    # Run headlessly with:  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy dosbox ...
    # Non-interactive EXEs: use  -c "PROG.EXE" --exit  (no keypress needed)
    # Interactive programs:  drive with keypress.py + dosbox/run_and_trace.txt
    #
    # dosbox-staging.conf is pre-configured with:
    #   trace_instructions = false  (keeps text log small)
    #   binary_opcode_dump = true   (compact opcodes.bin for disassembly)
    #   All deduplicate_* options enabled (reduces repetition in text log)
    # ---------------------------------------------------------------------------
    DOSBOX_DIR="$REPO_ROOT/tools/dosbox-staging"
    DOSBOX_BIN="$DOSBOX_DIR/build/dosbox"

    if [ ! -d "$DOSBOX_DIR/.git" ]; then
        log "Cloning EdgeOfAssembly/dosbox-staging..."
        git clone --depth=1 \
            https://github.com/EdgeOfAssembly/dosbox-staging.git \
            "$DOSBOX_DIR" || { warn "dosbox-staging clone failed; skipping build."; }
    else
        ok "dosbox-staging already cloned at $DOSBOX_DIR"
    fi

    if [ -d "$DOSBOX_DIR/.git" ] && [ ! -f "$DOSBOX_BIN" ]; then
        log "Building dosbox-staging (cmake + make, OPT_OPUS=OFF)..."

        # Build-time dependencies — gated by package manager
        case "${PKG_MGR:-}" in
            apt)
                sudo apt-get install -y --no-install-recommends \
                    libsdl2-dev libsdl2-image-dev libpng-dev \
                    libspeexdsp-dev libasound2-dev libfluidsynth-dev fluidsynth \
                    libasio-dev build-essential 2>/dev/null | grep -E "^(Setting up|E:)" || true
                ;;
            dnf)
                sudo dnf install -y \
                    SDL2-devel SDL2_image-devel libpng-devel \
                    speexdsp-devel alsa-lib-devel fluidsynth-devel \
                    asio-devel @development-tools || true
                ;;
            pacman)
                sudo pacman -S --noconfirm --needed \
                    sdl2 sdl2_image libpng \
                    speexdsp alsa-lib fluidsynth \
                    asio base-devel || true
                ;;
            brew)
                brew install \
                    sdl2 sdl2_image libpng \
                    speexdsp fluidsynth \
                    asio cmake make || true
                ;;
            *)
                warn "Unknown package manager '${PKG_MGR:-unset}'. Please install build deps manually:"
                warn "  SDL2-dev, SDL2_image-dev, libpng-dev, speexdsp-dev, libasound2-dev,"
                warn "  fluidsynth-dev, libasio-dev, build-essential (or distro equivalents)."
                ;;
        esac

        # iir1 (not in apt — build from source, takes ~30s)
        if ! pkg-config --exists iir 2>/dev/null; then
            log "Building iir1 from source..."
            git clone --depth=1 --branch 1.9.3 \
                https://github.com/berndporr/iir1.git /tmp/iir1 2>/dev/null || true
            cmake -S /tmp/iir1 -B /tmp/iir1/build -G "Unix Makefiles" \
                -DCMAKE_BUILD_TYPE=Release -DIIR_INSTALL=ON -DCMAKE_INSTALL_PREFIX=/usr/local \
                -Wno-dev > /dev/null 2>&1
            make -s -C /tmp/iir1/build -j"$(nproc)"
            sudo make -s -C /tmp/iir1/build install
            sudo ldconfig
        fi

        # zlib-ng (compat mode, registers as zlib-ng for pkg-config)
        if ! pkg-config --exists zlib-ng 2>/dev/null; then
            log "Building zlib-ng from source..."
            git clone --depth=1 \
                https://github.com/zlib-ng/zlib-ng.git /tmp/zlib-ng 2>/dev/null || true
            cmake -S /tmp/zlib-ng -B /tmp/zlib-ng/build -G "Unix Makefiles" \
                -DCMAKE_BUILD_TYPE=Release -DZLIB_COMPAT=ON -DBUILD_SHARED_LIBS=OFF \
                -Wno-dev > /dev/null 2>&1
            make -s -C /tmp/zlib-ng/build -j"$(nproc)"
            sudo make -s -C /tmp/zlib-ng/build install
            # Create zlib-ng.pc so pkg-config finds it
            sudo bash -c 'cat > /usr/local/lib/pkgconfig/zlib-ng.pc << EOF
prefix=/usr/local
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir=${prefix}/include
Name: zlib-ng
Description: zlib replacement with optimisations (compat mode)
Version: 2.2.4
Libs: -L${libdir} -lz
Cflags: -I${includedir}
EOF'
            sudo ldconfig
        fi

        # Apply tracked patches (stored in scripts/patches/dosbox-staging/) to fix
        # upstream CMake issues with optional dependency guarding.
        # Patches are idempotent: git apply skips already-applied hunks.
        PATCHES_DIR="$REPO_ROOT/scripts/patches/dosbox-staging"
        if [ -d "$PATCHES_DIR" ]; then
            log "Applying dosbox-staging patches from $PATCHES_DIR..."
            (
                cd "$DOSBOX_DIR"
                for p in "$PATCHES_DIR"/*.patch; do
                    [ -f "$p" ] || continue
                    git apply --whitespace=fix "$p" 2>/dev/null && \
                        log "  Applied: $(basename "$p")" || \
                        log "  Skipped (already applied?): $(basename "$p")"
                done
            )
        fi

        # Configure and build dosbox-staging
        # -DOPT_OPUS=OFF      : skip opusfile (not needed for RE tracing)
        # -DOPT_OPENGL=OFF    : no display needed for headless SDL_VIDEODRIVER=dummy
        # -DOPT_MT32EMU=OFF   : skip Roland MT-32 emulation
        # -DOPT_TESTS=OFF     : skip unit tests
        cmake -S "$DOSBOX_DIR" -B "$DOSBOX_DIR/build" -G "Unix Makefiles" \
            -DOPT_OPUS=OFF \
            -DOPT_OPENGL=OFF \
            -DOPT_MT32EMU=OFF \
            -DOPT_TESTS=OFF \
            -DCMAKE_BUILD_TYPE=Release \
            -Wno-dev > /dev/null 2>&1 && \
        make -s -C "$DOSBOX_DIR/build" -j"$(nproc)" && \
            ok "dosbox-staging built: $DOSBOX_BIN" || \
            warn "dosbox-staging build failed; dosbox-based RE tests will be skipped."

    elif [ -f "$DOSBOX_BIN" ]; then
        ok "dosbox-staging already built: $DOSBOX_BIN"
    fi

    log "dosbox-staging conf: $DOSBOX_DIR/dosbox-staging.conf"
    log "DEBUG_TRACE docs:    $DOSBOX_DIR/docs/DEBUG_TRACE.md"
    log "Headless usage:      SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy $DOSBOX_BIN --help"

else
    log "Skipping RE tool install (--skip-re-tools)."
fi

# ---------------------------------------------------------------------------
# Populate /tmp/bin — place dosbox-staging, dumpexe, and keypress.py here
# so they are on PATH regardless of where the repo is checked out.
# ---------------------------------------------------------------------------
TMPBIN="/tmp/bin"
mkdir -p "$TMPBIN"

# dosbox-staging binary
if [ -x "$REPO_ROOT/tools/dosbox-staging/build/dosbox" ]; then
    ln -sf "$REPO_ROOT/tools/dosbox-staging/build/dosbox" "$TMPBIN/dosbox" && \
        ok "/tmp/bin/dosbox -> $REPO_ROOT/tools/dosbox-staging/build/dosbox"
fi

# dumpexe binary
if [ -x "$REPO_ROOT/tools/dumpexe/dumpexe" ]; then
    ln -sf "$REPO_ROOT/tools/dumpexe/dumpexe" "$TMPBIN/dumpexe" && \
        ok "/tmp/bin/dumpexe -> $REPO_ROOT/tools/dumpexe/dumpexe"
fi

# keypress.py
if [ -f "$REPO_ROOT/tools/keypress/keypress.py" ]; then
    ln -sf "$REPO_ROOT/tools/keypress/keypress.py" "$TMPBIN/keypress.py" && \
        ok "/tmp/bin/keypress.py -> $REPO_ROOT/tools/keypress/keypress.py"
elif [ -f "$REPO_ROOT/tools/keypress.py" ]; then
    ln -sf "$REPO_ROOT/tools/keypress.py" "$TMPBIN/keypress.py" && \
        ok "/tmp/bin/keypress.py -> $REPO_ROOT/tools/keypress.py"
fi

# Emit a shell snippet that callers can eval/source to extend PATH.
# Usage (from CI or other scripts):
#   eval "$(bash scripts/setup_env.sh --skip-models --skip-re-tools 2>/dev/null | grep ^export)" 
# Or simply run:  export PATH="/tmp/bin:$PATH"
if [[ ":$PATH:" != *":/tmp/bin:"* ]]; then
    log "Add /tmp/bin to PATH: export PATH=\"/tmp/bin:\$PATH\""
fi
export PATH="$TMPBIN:$PATH"
ok "/tmp/bin added to PATH (current shell)"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " AXE environment setup complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Activate your Python venv (if using one):"
echo "       source venv/bin/activate"
echo "  2. Run the full AXE test suite:"
echo "       python3 tests/test_end_to_end.py"
echo "  3. Run interactive keypress tests (requires Xvfb):"
echo "       python3 tests/test_interactive_keypress.py"
echo ""
echo "To start AXE:"
echo "  ./axe.py                          # interactive mode"
echo "  ./axe.py -c '@llama hello'        # batch mode"
echo ""
echo "RE Toolchain:"
if [ -x "$REPO_ROOT/tools/dumpexe/dumpexe" ]; then
    echo "  dumpexe: tools/dumpexe/dumpexe (built)"
    echo "    Usage: tools/dumpexe/dumpexe -a tests/fixtures/dos_binaries/4dos595/4HELP.EXE"
else
    echo "  dumpexe: NOT BUILT (install gcc-14 + libcapstone-dev then: make -C tools/dumpexe)"
fi
if [ -d "$REPO_ROOT/tests/fixtures/dos_binaries" ]; then
    echo "  DOS fixtures: tests/fixtures/dos_binaries/ ($(ls "$REPO_ROOT/tests/fixtures/dos_binaries/" 2>/dev/null | wc -l | tr -d ' ') entries)"
fi
if [ -d "$REPO_ROOT/tools/dosbox-staging" ]; then
    echo "  dosbox-staging: tools/dosbox-staging/ (ref: docs/DEBUG_TRACE.md)"
fi
echo ""
echo "Ollama models available:"
ollama list 2>/dev/null || true
echo ""
