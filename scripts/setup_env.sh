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
# Usage:
#   bash scripts/setup_env.sh [--skip-models] [--skip-xvfb] [--skip-keypress]
#
# Options:
#   --skip-models    Skip pulling Ollama models (use if already pulled)
#   --skip-xvfb      Skip installing Xvfb packages
#   --skip-keypress  Skip installing EdgeOfAssembly/keypress
#   --help           Show this help message
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

for arg in "$@"; do
    case "$arg" in
        --skip-models)   SKIP_MODELS=true ;;
        --skip-xvfb)     SKIP_XVFB=true ;;
        --skip-keypress) SKIP_KEYPRESS=true ;;
        --help|-h)
            sed -n '2,30p' "$0" | sed 's/^# //' | sed 's/^#//'
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
            curl wget git python3-xlib python3-pip
        ;;
    dnf)
        sudo dnf install -y curl wget git python3-xlib python3-pip
        ;;
    pacman)
        sudo pacman -Sy --noconfirm curl wget git python-xlib python-pip
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
# 4. Install Python requirements for AXE
# ---------------------------------------------------------------------------
log "Installing Python requirements for AXE..."
if [ -f "$REPO_ROOT/requirements.txt" ]; then
    pip3 install --upgrade pip -q
    pip3 install -r "$REPO_ROOT/requirements.txt" -q
    ok "Python requirements installed."
else
    warn "requirements.txt not found at $REPO_ROOT/requirements.txt"
fi

# Also install python-xlib for keypress (pip fallback if not installed via pkg manager)
pip3 install python-xlib -q 2>/dev/null || true

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

# Check if already installed and up to date
if command -v ollama &>/dev/null; then
    INSTALLED_VER=$(ollama --version 2>&1 | grep -oP '[\d]+\.[\d]+\.[\d]+' | head -1 || echo "0.0.0")
    REQUIRED_VER="${LATEST_OLLAMA#v}"
    if [ "$INSTALLED_VER" = "$REQUIRED_VER" ]; then
        ok "Ollama $INSTALLED_VER already installed and up to date."
    else
        log "Updating Ollama from $INSTALLED_VER to $REQUIRED_VER..."
        curl -fsSL https://ollama.ai/install.sh | sh
        ok "Ollama updated to $(ollama --version 2>&1 | head -1)."
    fi
else
    log "Ollama not found; installing..."
    curl -fsSL https://ollama.ai/install.sh | sh
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
echo "Ollama models available:"
ollama list 2>/dev/null || true
echo ""
