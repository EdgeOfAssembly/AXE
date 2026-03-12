#!/usr/bin/env bash
# =============================================================================
# run_feature_validation.sh
# =============================================================================
# Top-level harness that installs Ollama (if needed), pulls the three test
# models, and runs the complete AXE feature-validation suite.
#
# Usage:
#   bash tests/run_feature_validation.sh [--skip-setup] [--skip-live]
#
# Options:
#   --skip-setup    Skip Ollama install / model pull (assume already done)
#   --skip-live     Skip live Ollama tests (run structural tests only)
#
# Exit code:
#   0 — all suites passed (or skipped)
#   1 — one or more suites failed
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log()  { echo "[validate] $*"; }
ok()   { echo "[validate] ✓ $*"; }
warn() { echo "[validate] ⚠ $*"; }
fail() { echo "[validate] ✗ $*" >&2; }

SKIP_SETUP=false
SKIP_LIVE=false

for arg in "$@"; do
    case "$arg" in
        --skip-setup) SKIP_SETUP=true ;;
        --skip-live)  SKIP_LIVE=true ;;
        --help|-h)
            echo "Usage: bash tests/run_feature_validation.sh [--skip-setup] [--skip-live]"
            exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# 1. Environment setup — Ollama + models
# ---------------------------------------------------------------------------
if [ "$SKIP_SETUP" = false ]; then
    log "Checking Ollama installation..."
    if ! command -v ollama &>/dev/null; then
        log "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        ok "Ollama already installed ($(ollama --version 2>&1 | head -1))"
    fi

    # Ensure server is running
    if ! curl -sf http://localhost:11434/ >/dev/null 2>&1; then
        log "Starting Ollama server..."
        nohup ollama serve >/tmp/ollama.log 2>&1 &
        OLLAMA_PID=$!
        log "Waiting for Ollama to start (PID $OLLAMA_PID)..."
        for i in $(seq 1 30); do
            if curl -sf http://localhost:11434/ >/dev/null 2>&1; then
                ok "Ollama server is up"
                break
            fi
            sleep 1
        done
        if ! curl -sf http://localhost:11434/ >/dev/null 2>&1; then
            warn "Ollama server didn't start; live tests will be skipped"
        fi
    else
        ok "Ollama server already running"
    fi

    # Pull three small test models
    MODELS=("qwen2.5-coder:1.5b" "qwen2.5:1.5b" "tinyllama:latest")
    for model in "${MODELS[@]}"; do
        short="${model%%:*}"
        if ollama list 2>/dev/null | grep -qF "$short"; then
            ok "$model already available"
        else
            log "Pulling $model ..."
            ollama pull "$model" 2>&1 | tail -3
            ok "$model pulled"
        fi
    done

    # Python deps
    log "Installing Python requirements..."
    pip install -q -r "$REPO_ROOT/requirements.txt" 2>&1 | tail -3 || true
    pip install -q openai filelock 2>&1 | tail -3 || true
fi

# ---------------------------------------------------------------------------
# 2. Structural / unit suite (test_end_to_end.py) — always runs
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Structural test suite (test_end_to_end.py)"
echo "============================================================"
cd "$REPO_ROOT"
python3 tests/test_end_to_end.py
E2E_RC=$?

# ---------------------------------------------------------------------------
# 3. Live feature matrix (test_live_feature_matrix.py)
# ---------------------------------------------------------------------------
if [ "$SKIP_LIVE" = false ]; then
    echo ""
    echo "============================================================"
    echo "  Live feature matrix (test_live_feature_matrix.py)"
    echo "============================================================"
    python3 tests/test_live_feature_matrix.py
    LIVE_RC=$?
else
    log "Skipping live tests (--skip-live)"
    LIVE_RC=0
fi

# ---------------------------------------------------------------------------
# 4. Final summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Validation Complete"
echo "============================================================"
if [ $E2E_RC -eq 0 ] && [ $LIVE_RC -eq 0 ]; then
    ok "All test suites passed"
    exit 0
else
    fail "One or more test suites failed"
    echo "  test_end_to_end.py        exit $E2E_RC"
    echo "  test_live_feature_matrix  exit $LIVE_RC"
    exit 1
fi
