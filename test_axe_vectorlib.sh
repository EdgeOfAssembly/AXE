#!/bin/bash
# AXE Multi-Agent Test with vector-lib Repository
# Tests PR #18 and #20 fixes with a real C library project

set -e

# Check for required API keys (should be set in environment)
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$HUGGINGFACE_API_KEY" ]; then
    echo "ERROR: No API keys found. Please set at least one of:"
    echo "  ANTHROPIC_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY"
    exit 1
fi

echo "=== AXE Multi-Agent Test with vector-lib ==="
echo "Date: $(date)"
echo ""

# Setup workspace
WORKSPACE="/tmp/vectorlib_test"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"

# Clone vector-lib repository
echo "Cloning vector-lib repository..."
cd /tmp
rm -rf vector-lib
git clone https://github.com/EdgeOfAssembly/vector-lib.git
cp -r vector-lib/* "$WORKSPACE/"
echo "vector-lib project copied to $WORKSPACE"
ls -la "$WORKSPACE"

# Run AXE in collaborative mode
echo ""
echo "=== Starting AXE Collaborative Mode ==="
echo "Agents: claude,gpt"
echo "Time limit: 5 minutes"
echo ""

cd /home/runner/work/AXE/AXE

# Run with short time limit for testing
./axe.py --collab claude,gpt \
         --workspace "$WORKSPACE" \
         --time 5 \
         --task "Complete these tasks for the vector-lib C library project:

1. READ and analyze all source files:
   - vector.h (main header file)
   - align.h (alignment utilities)
   - example.c (example usage)
   - README.md (documentation)

2. COMPILE the example program:
   - Use: gcc -std=c99 -pthread example.c -o example
   - Verify compilation succeeds

3. RUN the example program:
   - Execute: ./example
   - Capture the output

4. ANALYZE the code for:
   - Thread safety implementation (SRWLOCK/pthread_rwlock_t)
   - Memory management patterns
   - Type-agnostic macro design
   - Any potential bugs or improvements

5. CREATE a CODE_REVIEW.md file that includes:
   - Summary of what the library does
   - Analysis of thread-safety mechanisms
   - Code quality assessment
   - Any bugs or issues found
   - Suggestions for improvements
   - Performance considerations

6. CREATE a TEST_REPORT.md file that includes:
   - Did compilation succeed?
   - Did the example program run successfully?
   - What output did the example produce?
   - Were all files analyzed?
   - List of files in workspace (use: ls -la)

IMPORTANT: Use <exec>command</exec>, <read>file</read>, and <write file=\"path\">content</write> tags to perform your tasks."

echo ""
echo "=== AXE Test Completed ==="
echo ""
echo "Results are in: $WORKSPACE"
echo ""
echo "Checking for created files..."
ls -la "$WORKSPACE"
echo ""

if [ -f "$WORKSPACE/CODE_REVIEW.md" ]; then
    echo "✅ CODE_REVIEW.md was created"
    echo "--- Preview ---"
    head -30 "$WORKSPACE/CODE_REVIEW.md"
else
    echo "❌ CODE_REVIEW.md was NOT created"
fi

echo ""

if [ -f "$WORKSPACE/TEST_REPORT.md" ]; then
    echo "✅ TEST_REPORT.md was created"
    echo "--- Preview ---"
    head -30 "$WORKSPACE/TEST_REPORT.md"
else
    echo "❌ TEST_REPORT.md was NOT created"
fi

echo ""

if [ -f "$WORKSPACE/example" ]; then
    echo "✅ example binary was compiled"
else
    echo "❌ example binary was NOT compiled"
fi

echo ""
echo "=== Collaboration Log Preview ==="
if [ -f "$WORKSPACE/.collab_log.md" ]; then
    tail -100 "$WORKSPACE/.collab_log.md"
else
    echo "No collaboration log found"
fi

echo ""
echo "Full collaboration log: $WORKSPACE/.collab_log.md"
echo "Full results in: $WORKSPACE"
