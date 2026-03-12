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
        # Download installer to a temp file rather than piping directly to sh,
        # so it is auditable.  Set OLLAMA_INSTALL_SHA256 to verify the checksum.
        tmp_install_sh="$(mktemp)"
        curl -fsSL https://ollama.com/install.sh -o "$tmp_install_sh"
        if [ -n "${OLLAMA_INSTALL_SHA256:-}" ]; then
            log "Verifying Ollama installer checksum..."
            actual_sha256="$(sha256sum "$tmp_install_sh" | awk '{print $1}')"
            if [ "$actual_sha256" != "$OLLAMA_INSTALL_SHA256" ]; then
                fail "Ollama installer checksum mismatch (expected $OLLAMA_INSTALL_SHA256, got $actual_sha256)"
                rm -f "$tmp_install_sh"
                exit 1
            fi
            ok "Ollama installer checksum verified"
        fi
        sh "$tmp_install_sh"
        rm -f "$tmp_install_sh"
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

    # Pull three small test models — check for the exact tag to avoid false positives
    # (e.g. having qwen2.5:7b installed must not skip pulling qwen2.5:1.5b).
    MODELS=("qwen2.5-coder:1.5b" "qwen2.5:1.5b" "tinyllama:latest")
    for model in "${MODELS[@]}"; do
        if ollama list 2>/dev/null | awk 'NR>1{print $1}' | grep -qxF "$model"; then
            ok "$model already available"
        else
            log "Pulling $model ..."
            ollama pull "$model"
            ok "$model pulled"
        fi
    done

    # Python deps — fail fast if requirements cannot be installed; log to file for audit.
    PIP_LOG="${PIP_LOG:-/tmp/feature_validation_pip.log}"
    log "Installing Python requirements (full log → $PIP_LOG)..."
    pip install -q -r "$REPO_ROOT/requirements.txt" >>"$PIP_LOG" 2>&1
    tail -3 "$PIP_LOG"
    pip install -q openai filelock >>"$PIP_LOG" 2>&1
    tail -3 "$PIP_LOG"
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
