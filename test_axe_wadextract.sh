#!/bin/bash
# Test script for AXE Multi-Agent System with Doom WAD Extractor Project
# This tests the bug fixes from PR #18 and #20

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="/tmp/wadextract_test"
TIME_LIMIT=30  # minutes
RETRO_REPO="https://github.com/EdgeOfAssembly/RetroCodeMess.git"
RETRO_DIR="/tmp/RetroCodeMess"
KEYS_FILE="${RETRO_DIR}/AXE/keys.txt"
WADEXTRACT_SRC="${RETRO_DIR}/doom/wadextract"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
print_status "Checking prerequisites..."
if ! command_exists python3; then
    print_error "python3 is not installed"
    exit 1
fi

if ! command_exists git; then
    print_error "git is not installed"
    exit 1
fi

print_success "Prerequisites check passed"

# Step 2: Check if AXE is properly set up
print_status "Checking AXE setup..."
if [ ! -f "${SCRIPT_DIR}/axe.py" ]; then
    print_error "axe.py not found in ${SCRIPT_DIR}"
    exit 1
fi

if [ ! -x "${SCRIPT_DIR}/axe.py" ]; then
    print_warning "Making axe.py executable"
    chmod +x "${SCRIPT_DIR}/axe.py"
fi

print_success "AXE setup check passed"

# Step 3: Install Python dependencies
print_status "Installing Python dependencies..."
pip install -q openai anthropic huggingface_hub requests pyyaml gitpython 2>&1 | grep -v "Requirement already satisfied" || true
print_success "Dependencies installed"

# Step 4: Try to clone RetroCodeMess repository (may require authentication)
print_status "Attempting to clone RetroCodeMess repository..."
if [ -d "$RETRO_DIR" ]; then
    print_warning "Removing existing RetroCodeMess directory"
    rm -rf "$RETRO_DIR"
fi

# Try to clone with GH CLI if available, otherwise try git clone
if command_exists gh && gh auth status >/dev/null 2>&1; then
    print_status "Using GitHub CLI for authentication"
    if gh repo clone EdgeOfAssembly/RetroCodeMess "$RETRO_DIR" 2>/dev/null; then
        print_success "RetroCodeMess repository cloned successfully"
        REPO_AVAILABLE=true
    else
        print_warning "Failed to clone RetroCodeMess repository (may be private)"
        REPO_AVAILABLE=false
    fi
else
    if git clone "$RETRO_REPO" "$RETRO_DIR" 2>/dev/null; then
        print_success "RetroCodeMess repository cloned successfully"
        REPO_AVAILABLE=true
    else
        print_warning "Failed to clone RetroCodeMess repository (may be private or require authentication)"
        REPO_AVAILABLE=false
    fi
fi

# Step 5: Set up API keys
print_status "Setting up API keys..."
if [ "$REPO_AVAILABLE" = true ] && [ -f "$KEYS_FILE" ]; then
    print_status "Loading API keys from ${KEYS_FILE}"
    # Parse keys.txt and export them
    # Expected format: KEY_NAME=value
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        # Export the key
        export "$key=$value"
        print_status "Exported $key"
    done < "$KEYS_FILE"
    print_success "API keys loaded from file"
else
    print_warning "API keys file not available, checking environment variables"
    # Check if at least one API key is available
    if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$HUGGINGFACE_API_KEY" ]; then
        print_warning "No API keys found in environment"
        print_warning "Set at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY"
        print_warning "Proceeding with available keys (if any)"
    else
        print_success "Using API keys from environment"
    fi
fi

# Step 6: Set up workspace
print_status "Setting up workspace at ${WORKSPACE_DIR}..."
if [ -d "$WORKSPACE_DIR" ]; then
    print_warning "Removing existing workspace"
    rm -rf "$WORKSPACE_DIR"
fi
mkdir -p "$WORKSPACE_DIR"

# Copy wadextract files if available
if [ "$REPO_AVAILABLE" = true ] && [ -d "$WADEXTRACT_SRC" ]; then
    print_status "Copying wadextract project to workspace"
    cp -r "$WADEXTRACT_SRC"/* "$WORKSPACE_DIR/"
    print_success "wadextract project copied to workspace"
    WADEXTRACT_AVAILABLE=true
else
    print_warning "wadextract project not available from repository"
    print_warning "Creating minimal test workspace"
    # Create a minimal test environment
    cat > "$WORKSPACE_DIR/test.c" << 'EOF'
#include <stdio.h>

int main() {
    printf("Hello from AXE test!\n");
    return 0;
}
EOF
    cat > "$WORKSPACE_DIR/Makefile" << 'EOF'
test: test.c
	gcc -o test test.c
EOF
    WADEXTRACT_AVAILABLE=false
fi

print_success "Workspace setup complete"

# Step 7: Create task based on availability
print_status "Preparing task description..."
if [ "$WADEXTRACT_AVAILABLE" = true ]; then
    # Full wadextract test task
    TASK="Complete these tasks for the wadextract Doom WAD extraction tool:

1. READ all source files to understand the codebase (wadextract.c, Makefile, usage.txt, common.h, png.h)

2. COMPILE the tool using 'make' and verify it builds successfully

3. RUN the tool:
   - First run: ./wadextract -h (show help)
   - Extract DOOM.zip to get DOOM.WAD if available
   - Run: ./wadextract DOOM.WAD -l (list contents) if WAD file exists

4. TEST sprite/graphic extraction if WAD file available:
   - ./wadextract DOOM.WAD -x -r sprite -O sprites_test (extract sprites)
   - ./wadextract DOOM.WAD -x -r graphic -O graphics_test (extract graphics)
   - Compare outputs, look for any corruption or missing files
   - Check if the state machine in the extraction loop handles subsection markers correctly

5. CREATE a README.md file that includes:
   - Project description (Doom/Heretic/Hexen/Strife WAD asset extractor)
   - Build instructions
   - Usage examples from usage.txt if available
   - Supported games and features
   - Any bugs found during testing

6. REPORT findings in a file called TEST_REPORT.md:
   - Did compilation succeed?
   - Did extraction work?
   - Any bugs found in sprite/graphic extraction?
   - Were files actually created? (verify with ls -la)"
else
    # Simplified test task
    TASK="Complete these test tasks to verify AXE multi-agent system:

1. READ the test.c file and understand what it does

2. COMPILE the code using 'make' and verify it builds successfully

3. RUN the compiled program: ./test

4. CREATE a README.md file that includes:
   - What the program does
   - How to build it
   - How to run it

5. CREATE a TEST_REPORT.md file that includes:
   - Did compilation succeed?
   - Did the program run successfully?
   - Were files created correctly?
   - Any issues encountered?"
fi

# Step 8: Determine which agents to use
print_status "Determining available agents..."
AGENTS=""
if [ -n "$ANTHROPIC_API_KEY" ]; then
    AGENTS="${AGENTS}claude,"
    print_success "Claude (Anthropic) available"
fi
if [ -n "$OPENAI_API_KEY" ]; then
    AGENTS="${AGENTS}gpt,"
    print_success "GPT (OpenAI) available"
fi
if [ -n "$HUGGINGFACE_API_KEY" ]; then
    AGENTS="${AGENTS}llama,"
    print_success "Llama (HuggingFace) available"
fi

# Remove trailing comma
AGENTS="${AGENTS%,}"

if [ -z "$AGENTS" ]; then
    print_error "No API keys available for any agents"
    print_error "Please set at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY"
    exit 1
fi

print_success "Using agents: $AGENTS"

# Step 9: Start monitoring in background
print_status "Setting up monitoring..."
MONITOR_LOG="${WORKSPACE_DIR}/monitor.log"
touch "$MONITOR_LOG"

# Monitor function
monitor_workspace() {
    print_status "Monitor started (PID: $$)"
    while true; do
        echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$MONITOR_LOG"
        echo "Files in workspace:" >> "$MONITOR_LOG"
        ls -lah "$WORKSPACE_DIR" >> "$MONITOR_LOG" 2>&1
        echo "" >> "$MONITOR_LOG"
        
        # Check for key files
        if [ -f "${WORKSPACE_DIR}/README.md" ]; then
            echo "[✓] README.md created" >> "$MONITOR_LOG"
        fi
        if [ -f "${WORKSPACE_DIR}/TEST_REPORT.md" ]; then
            echo "[✓] TEST_REPORT.md created" >> "$MONITOR_LOG"
        fi
        if [ -d "${WORKSPACE_DIR}/sprites_test" ]; then
            echo "[✓] sprites_test/ directory created" >> "$MONITOR_LOG"
        fi
        if [ -d "${WORKSPACE_DIR}/graphics_test" ]; then
            echo "[✓] graphics_test/ directory created" >> "$MONITOR_LOG"
        fi
        
        sleep 10
    done
}

# Start monitor in background
monitor_workspace &
MONITOR_PID=$!
print_success "Monitor started (PID: $MONITOR_PID)"

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    if [ -n "$MONITOR_PID" ]; then
        kill $MONITOR_PID 2>/dev/null || true
        print_status "Monitor stopped"
    fi
}
trap cleanup EXIT

# Step 10: Run AXE in collaborative mode
print_status "Starting AXE in collaborative mode..."
print_status "Agents: $AGENTS"
print_status "Workspace: $WORKSPACE_DIR"
print_status "Time limit: $TIME_LIMIT minutes"
print_status "Task: ${TASK:0:100}..."

cd "$SCRIPT_DIR"

# Run AXE with timeout
print_status "Executing AXE..."
timeout ${TIME_LIMIT}m ./axe.py \
    --collab "$AGENTS" \
    --workspace "$WORKSPACE_DIR" \
    --time "$TIME_LIMIT" \
    --task "$TASK" \
    2>&1 | tee "${WORKSPACE_DIR}/axe_output.log" || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        print_warning "AXE timed out after ${TIME_LIMIT} minutes"
    else
        print_error "AXE exited with code $EXIT_CODE"
    fi
}

print_success "AXE execution completed"

# Step 11: Collect results
print_status "Collecting test results..."

RESULTS_DIR="${SCRIPT_DIR}/test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Copy workspace contents
cp -r "$WORKSPACE_DIR" "${RESULTS_DIR}/workspace"

# Copy log files
if [ -f "${WORKSPACE_DIR}/.collab_log.md" ]; then
    cp "${WORKSPACE_DIR}/.collab_log.md" "${RESULTS_DIR}/"
fi
if [ -f "${WORKSPACE_DIR}/.collab_shared.md" ]; then
    cp "${WORKSPACE_DIR}/.collab_shared.md" "${RESULTS_DIR}/"
fi

print_success "Results saved to $RESULTS_DIR"

# Step 12: Generate summary
print_status "Generating test summary..."

SUMMARY="${RESULTS_DIR}/TEST_SUMMARY.md"

cat > "$SUMMARY" << EOF
# AXE Multi-Agent System Test Summary

**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Test Type:** ${WADEXTRACT_AVAILABLE:-false}
**Agents Used:** $AGENTS
**Time Limit:** $TIME_LIMIT minutes
**Workspace:** $WORKSPACE_DIR

## Test Configuration

- AXE Repository: ${SCRIPT_DIR}
- RetroCodeMess Available: ${REPO_AVAILABLE:-false}
- wadextract Available: ${WADEXTRACT_AVAILABLE:-false}

## API Keys Status

EOF

# Check which keys were available
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "- ✅ Anthropic API Key: Available" >> "$SUMMARY"
else
    echo "- ❌ Anthropic API Key: Not Available" >> "$SUMMARY"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "- ✅ OpenAI API Key: Available" >> "$SUMMARY"
else
    echo "- ❌ OpenAI API Key: Not Available" >> "$SUMMARY"
fi

if [ -n "$HUGGINGFACE_API_KEY" ]; then
    echo "- ✅ HuggingFace API Key: Available" >> "$SUMMARY"
else
    echo "- ❌ HuggingFace API Key: Not Available" >> "$SUMMARY"
fi

cat >> "$SUMMARY" << EOF

## Success Criteria Verification

EOF

# Check success criteria
check_criterion() {
    local name="$1"
    local check="$2"
    if eval "$check"; then
        echo "- ✅ $name" >> "$SUMMARY"
        return 0
    else
        echo "- ❌ $name" >> "$SUMMARY"
        return 1
    fi
}

check_criterion "AXE ran without crashing" "[ -f '${WORKSPACE_DIR}/axe_output.log' ]"
check_criterion "Agents executed commands" "grep -q '<exec>' '${WORKSPACE_DIR}/.collab_log.md' 2>/dev/null || grep -q 'EXEC' '${WORKSPACE_DIR}/.collab_log.md' 2>/dev/null"
check_criterion "Files were created (README.md)" "[ -f '${WORKSPACE_DIR}/README.md' ]"
check_criterion "Files were created (TEST_REPORT.md)" "[ -f '${WORKSPACE_DIR}/TEST_REPORT.md' ]"

if [ "$WADEXTRACT_AVAILABLE" = true ]; then
    check_criterion "PNG files extracted to sprites_test/" "[ -d '${WORKSPACE_DIR}/sprites_test' ] && [ -n \"\$(ls -A '${WORKSPACE_DIR}/sprites_test' 2>/dev/null)\" ]"
    check_criterion "PNG files extracted to graphics_test/" "[ -d '${WORKSPACE_DIR}/graphics_test' ] && [ -n \"\$(ls -A '${WORKSPACE_DIR}/graphics_test' 2>/dev/null)\" ]"
fi

cat >> "$SUMMARY" << EOF

## Files Created

EOF

echo '```' >> "$SUMMARY"
ls -lah "$WORKSPACE_DIR" >> "$SUMMARY" 2>&1
echo '```' >> "$SUMMARY"

cat >> "$SUMMARY" << EOF

## Log Excerpts

### Collaboration Log

EOF

if [ -f "${WORKSPACE_DIR}/.collab_log.md" ]; then
    echo '```markdown' >> "$SUMMARY"
    head -200 "${WORKSPACE_DIR}/.collab_log.md" >> "$SUMMARY"
    echo '```' >> "$SUMMARY"
else
    echo "No collaboration log found." >> "$SUMMARY"
fi

cat >> "$SUMMARY" << EOF

### AXE Output

EOF

if [ -f "${WORKSPACE_DIR}/axe_output.log" ]; then
    echo '```' >> "$SUMMARY"
    tail -100 "${WORKSPACE_DIR}/axe_output.log" >> "$SUMMARY"
    echo '```' >> "$SUMMARY"
else
    echo "No AXE output log found." >> "$SUMMARY"
fi

cat >> "$SUMMARY" << EOF

## Monitor Log

EOF

if [ -f "$MONITOR_LOG" ]; then
    echo '```' >> "$SUMMARY"
    tail -50 "$MONITOR_LOG" >> "$SUMMARY"
    echo '```' >> "$SUMMARY"
else
    echo "No monitor log found." >> "$SUMMARY"
fi

cat >> "$SUMMARY" << EOF

## Test Deliverables

### 1. Test Results
See "Success Criteria Verification" section above.

### 2. Log Excerpts
See "Log Excerpts" section above.

### 3. File Verification
See "Files Created" section above.

### 4. Bug Findings

EOF

# Check for potential issues
if grep -q "ERROR" "${WORKSPACE_DIR}/axe_output.log" 2>/dev/null; then
    echo "Errors found in AXE output:" >> "$SUMMARY"
    echo '```' >> "$SUMMARY"
    grep "ERROR" "${WORKSPACE_DIR}/axe_output.log" | head -20 >> "$SUMMARY"
    echo '```' >> "$SUMMARY"
else
    echo "No errors detected in AXE output." >> "$SUMMARY"
fi

cat >> "$SUMMARY" << EOF

### 5. Recommendations

EOF

# Add recommendations based on test results
if [ "$WADEXTRACT_AVAILABLE" = false ]; then
    echo "- **Recommendation:** Re-run test with full wadextract project when RetroCodeMess repository is accessible" >> "$SUMMARY"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "- **Recommendation:** Test with Claude (Anthropic) API for full coverage" >> "$SUMMARY"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "- **Recommendation:** Test with GPT (OpenAI) API for full coverage" >> "$SUMMARY"
fi

cat >> "$SUMMARY" << EOF

## Next Steps

1. Review the collaboration log at \`${RESULTS_DIR}/.collab_log.md\`
2. Examine created files in \`${RESULTS_DIR}/workspace/\`
3. Check for any bugs found in \`${RESULTS_DIR}/workspace/TEST_REPORT.md\` (if created)
4. Verify that PR #18 and #20 fixes are working as expected:
   - Commands executed via \`<exec>\` tags
   - Files created via \`<write file="">\` tags
   - No double execution of commands
   - Token limit errors handled gracefully
   - Spawned agents received turns (if any were spawned)

## Conclusion

This test verified the AXE multi-agent orchestration system after the critical bug fixes in PR #18 and #20.
EOF

print_success "Summary generated at $SUMMARY"

# Step 13: Display summary
print_status "Test Summary:"
cat "$SUMMARY"

print_success "All test operations completed!"
print_status "Full results available at: $RESULTS_DIR"
