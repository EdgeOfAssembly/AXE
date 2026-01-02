# Heredoc Execution Fix Summary

## Problem

PR #12 successfully fixed heredoc parsing for **VALIDATION** (preventing false positives from heredoc content being parsed as commands), but inadvertently broke heredoc **EXECUTION**.

### The Issue

When an EXEC block contained a heredoc, only the first line was being executed, causing the heredoc content to be lost:

```markdown
```EXEC cat > file.md << 'EOF'
- Item 1
1. First
EOF
```
```

This would execute only: `cat > file.md << 'EOF'`

The heredoc content (`- Item 1`, `1. First`, `EOF`) was being ignored, resulting in:
- Shell warnings: `here-document at line 1 delimited by end-of-file (wanted 'EOF')`
- Empty or incorrect file output

## Root Cause

In `axe.py`, the `ResponseProcessor.process_response()` method parses EXEC blocks using this regex:

```python
pattern = r'```(READ|EXEC|WRITE)\s*([^\n]*)\n(.*?)```'
```

This correctly splits the block into:
- `group(1)`: Block type (EXEC)
- `group(2)`: Args/first line (`cat > file.md << 'EOF'`)
- `group(3)`: Content/remaining lines (`- Item 1\n1. First\nEOF`)

However, the code at line 1478 was:

```python
command = args or content  # BUG!
```

This used only `args` when both were present, losing the heredoc content.

## Solution

Changed the EXEC block handling to combine `args` and `content` when both are present:

```python
if args and content:
    # Both present: combine with newline (e.g., "cat << EOF" + "\nlines\nEOF")
    command = args + '\n' + content
else:
    # Only one present: use whichever exists
    command = args or content
```

### Why This Works

1. **Heredocs on same line as EXEC**: `args` contains the command start, `content` contains the heredoc body → combine them
2. **Heredocs on content line**: `args` is empty, `content` contains the full command → use content
3. **Simple commands**: Either `args` has everything (use args) or `content` has everything (use content)
4. **Backward compatible**: Doesn't break any existing EXEC block patterns

## Validation

The fix maintains the correct validation behavior from PR #12:

- ✅ Heredoc content is still stripped during validation (via `_strip_heredoc_content()`)
- ✅ No false positives from markdown symbols (`-`, `1.`, `---`) in heredoc content
- ✅ Shell operators in heredoc content don't cause false command splits
- ✅ Operators after heredoc markers (e.g., `cat << EOF | grep`) are correctly parsed

## Testing

### New Tests Added
- `test_exec_heredoc.py`: Comprehensive test suite covering:
  - Heredoc with command on EXEC line
  - Heredoc with command on content line
  - Multiple EXEC blocks with heredocs
  - Regression test for simple EXEC commands

### Existing Tests
- All 10 ToolRunner tests pass
- All validation demos work correctly
- No regressions in any existing functionality

## Impact

This fix ensures that:
1. **Validation works correctly**: Heredoc content is stripped before whitelist checking
2. **Execution works correctly**: Original command with heredoc content is passed to shell
3. **No breaking changes**: All existing EXEC block patterns continue to work

## Files Changed

- `axe.py`: Fixed `ResponseProcessor.process_response()` EXEC handling (7 lines)
- `test_exec_heredoc.py`: Added comprehensive test coverage (165 lines)
