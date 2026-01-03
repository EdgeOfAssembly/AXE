# Quick Start Guide: Testing AXE Multi-Agent System

This guide provides quick instructions for testing the AXE multi-agent system with the test infrastructure created for PR #18 and #20 verification.

## Prerequisites

### 1. Install Dependencies
```bash
pip install gnureadline openai anthropic huggingface_hub requests pyyaml gitpython
```

### 2. Set API Keys
You need at least ONE of these API keys:

```bash
# Option 1: Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: OpenAI GPT
export OPENAI_API_KEY="sk-proj-..."

# Option 3: HuggingFace Llama
export HUGGINGFACE_API_KEY="hf_..."
```

### 3. Verify Network Access
```bash
# Test connectivity
curl -I https://api.anthropic.com
curl -I https://api.openai.com
```

## Running the Tests

### Test 1: Vector-lib (Recommended)
Tests with a real C library project from GitHub.

```bash
cd /home/runner/work/AXE/AXE
./test_axe_vectorlib.sh
```

**What it tests:**
- Code reading and analysis
- C compilation with gcc
- Program execution
- File creation (CODE_REVIEW.md, TEST_REPORT.md)
- PR #18/#20 fixes (XML tags, no double execution)

**Expected output:**
- ✅ CODE_REVIEW.md created
- ✅ TEST_REPORT.md created
- ✅ example binary compiled
- ✅ Collaboration log shows agent turns

### Test 2: Simple Mock Project
Quick test with minimal C program.

```bash
cd /home/runner/work/AXE/AXE
./run_axe_test.sh
```

**What it tests:**
- Basic compilation
- Basic file operations
- Agent collaboration
- Quick verification (5 minute limit)

**Expected output:**
- ✅ README.md created
- ✅ TEST_REPORT.md created
- ✅ test binary compiled

### Test 3: Full Monitoring (Advanced)
Comprehensive test with background monitoring.

```bash
cd /home/runner/work/AXE/AXE
./test_axe_wadextract.sh
```

**What it tests:**
- Full monitoring of file creation
- Detailed logging
- Complete test report generation
- All PR #18/#20 fixes

## Monitoring During Test

### Watch Files Being Created
```bash
# In a separate terminal
watch -n 5 'ls -lah /tmp/vectorlib_test/'
```

### Follow Collaboration Log
```bash
# In a separate terminal
tail -f /tmp/vectorlib_test/.collab_log.md
```

### Check Progress
```bash
# See what agents are doing
grep "Turn:" /tmp/vectorlib_test/.collab_log.md | tail -10
```

## Verifying PR #18/#20 Fixes

### Fix #1: XML Tag Support
Look for these in `.collab_log.md`:

```markdown
<exec>gcc -o example example.c</exec>
<read>vector.h</read>
<write file="CODE_REVIEW.md">content</write>
```

✅ If you see these tags being processed, the fix works!

### Fix #2: No Double Execution
Commands should appear ONCE, not twice:

```bash
# Check for duplicates
grep -A2 "<exec>make" /tmp/vectorlib_test/.collab_log.md
```

✅ Each command should execute only once!

### Fix #3: Token Error Handling
If token errors occur, they should be handled gracefully:

```markdown
⚠️  API Error: Token limit exceeded
[Agent put to sleep after 3 errors]
[Session continues with remaining agents]
```

✅ Session should continue, not crash!

### Fix #4: Spawned Agents
If supervisor spawns agents, they should get turns:

```bash
# Look for spawned agents
grep "Spawned" /tmp/vectorlib_test/.collab_log.md
grep "Turn:" /tmp/vectorlib_test/.collab_log.md | grep UUID
```

✅ Spawned agents should receive turns!

## Results Location

After test completes, check:

```bash
# Main workspace
ls -la /tmp/vectorlib_test/

# Created reports
cat /tmp/vectorlib_test/CODE_REVIEW.md
cat /tmp/vectorlib_test/TEST_REPORT.md

# Collaboration log
less /tmp/vectorlib_test/.collab_log.md

# Compiled binary
./tmp/vectorlib_test/example
```

## Quick Verification Commands

```bash
# Verify files were created
ls /tmp/vectorlib_test/*.md

# Count exec commands (should see many)
grep -c "<exec>" /tmp/vectorlib_test/.collab_log.md

# Count write commands (should see at least 2)
grep -c "<write" /tmp/vectorlib_test/.collab_log.md

# Check for errors
grep -i "error" /tmp/vectorlib_test/.collab_log.md

# Check compilation success
ls -lh /tmp/vectorlib_test/example
```

## Troubleshooting

### No API Connection
```
ERROR: Connection error
```

**Solution:** 
- Check network connectivity
- Verify API keys are set
- Try different API provider
- Check firewall/proxy settings

### Files Not Created
```
❌ CODE_REVIEW.md was NOT created
```

**Solution:**
- Check `.collab_log.md` for errors
- Verify agents received turns
- Increase time limit
- Check API quota/limits

### Compilation Failed
```
ERROR: gcc command failed
```

**Solution:**
- Check gcc is installed: `gcc --version`
- Check source files exist
- Review error messages in log

## Success Criteria Checklist

After running test, verify:

- [ ] ✅ AXE started without crashing
- [ ] ✅ Agents received turns (check log)
- [ ] ✅ Commands executed (grep for `<exec>`)
- [ ] ✅ Files created (README.md, TEST_REPORT.md)
- [ ] ✅ Compilation succeeded (binary exists)
- [ ] ✅ No double execution (commands appear once)
- [ ] ✅ No crashes from errors
- [ ] ✅ Collaboration log complete

## Example: Complete Test Run

```bash
#!/bin/bash

# 1. Set up environment
export ANTHROPIC_API_KEY="your-key-here"
cd /home/runner/work/AXE/AXE

# 2. Run test
./test_axe_vectorlib.sh

# 3. Wait for completion (5 minutes)
# Watch in another terminal:
# tail -f /tmp/vectorlib_test/.collab_log.md

# 4. Check results
ls -la /tmp/vectorlib_test/
cat /tmp/vectorlib_test/CODE_REVIEW.md
cat /tmp/vectorlib_test/TEST_REPORT.md

# 5. Verify fixes
echo "=== Checking PR #18/#20 Fixes ==="
echo "XML tag usage:"
grep -c "<exec>" /tmp/vectorlib_test/.collab_log.md
grep -c "<write" /tmp/vectorlib_test/.collab_log.md

echo "No double execution:"
grep "<exec>gcc" /tmp/vectorlib_test/.collab_log.md | wc -l

echo "Files created:"
ls /tmp/vectorlib_test/*.md

echo "✅ Test complete!"
```

## Getting Help

If tests fail or behave unexpectedly:

1. Check `AXE_TEST_SUMMARY.md` for detailed information
2. Review `.collab_log.md` in workspace for detailed execution log
3. Check GitHub issues: https://github.com/EdgeOfAssembly/AXE/issues
4. Review bug fix documentation: `BUG_FIX_SUMMARY.md`

## Related Documentation

- `AXE_TEST_SUMMARY.md` - Complete test documentation
- `BUG_FIX_SUMMARY.md` - PR #18/#20 bug fixes explained
- `DUPLICATE_EXECUTION_FIX_SUMMARY.md` - Double execution fix
- `README.md` - AXE general documentation

---

**Ready to test?** Run: `./test_axe_vectorlib.sh`
