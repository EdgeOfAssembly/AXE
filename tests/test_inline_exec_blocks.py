#!/usr/bin/env python3
"""
Test suite for inline EXEC block parsing bug (Issue #22).

Verifies that the ResponseProcessor correctly parses multiple inline code blocks
on the same line as markdown text, without incorrectly matching the wrong closing
backticks.

Bug description:
When agents write inline blocks like:
```EXEC mkdir -p patches```
### Next step
```EXEC ls -la```

The old regex would match from the first ```EXEC to the SECOND ``` (after ls -la),
creating one broken command instead of two separate commands.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, ResponseProcessor, ToolRunner


def test_inline_exec_blocks_bug():
    """Test the specific bug case from the issue report."""
    print("\n" + "="*70)
    print("Testing inline EXEC blocks bug fix...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Exact test case from the bug report
        response = """### Step 1: Create the `patches` directory
```EXEC mkdir -p patches```

### Step 2: Generate the patch file
```EXEC diff -u wadextract.old wadextract.c > patches/0001-wadextract-update.patch```
"""
        
        result = processor.process_response(response, "test_agent")
        print(f"Result:\n{result}\n")
        
        # Extract the execution results section
        exec_results = result.split("--- Execution Results ---")[1] if "--- Execution Results ---" in result else result
        
        # Verify both commands were executed
        assert result.count("[EXEC:") == 2, f"Expected 2 EXEC blocks, result: {result}"
        
        # Verify first command doesn't include garbage from markdown in the EXECUTION
        assert "mkdir -p patches```" not in exec_results, \
            "First command execution should not include closing backticks"
        assert "### Step 2" not in exec_results.split("[EXEC:")[1].split("]")[0], \
            "First command execution should not include markdown headings"
        
        # Verify the directory was actually created
        patches_dir = os.path.join(tmpdir, "patches")
        assert os.path.exists(patches_dir), "patches directory should be created"
        
        print("  ✓ Inline EXEC blocks parsed correctly")
        print("  ✓ Both commands executed separately")
        print("  ✓ No garbage from markdown in commands")


def test_multiple_inline_blocks():
    """Test multiple inline blocks in sequence."""
    print("\n" + "="*70)
    print("Testing multiple inline EXEC blocks...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        response = """Let's run some commands:

```EXEC mkdir -p dir1```
```EXEC mkdir -p dir2```
```EXEC mkdir -p dir3```

All directories created!"""
        
        result = processor.process_response(response, "test_agent")
        
        # Verify all three commands were executed
        assert result.count("[EXEC:") == 3, f"Expected 3 EXEC blocks, got: {result}"
        
        # Verify all directories were created
        assert os.path.exists(os.path.join(tmpdir, "dir1"))
        assert os.path.exists(os.path.join(tmpdir, "dir2"))
        assert os.path.exists(os.path.join(tmpdir, "dir3"))
        
        print("  ✓ Multiple inline blocks work correctly")


def test_mixed_inline_and_multiline():
    """Test mixing inline and multiline block formats."""
    print("\n" + "="*70)
    print("Testing mixed inline and multiline blocks...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        response = """First, inline:
```EXEC mkdir -p testdir```

Then, multiline:
```EXEC
echo "Hello" > testdir/hello.txt
```

And another inline:
```EXEC ls -la testdir```

Done!"""
        
        result = processor.process_response(response, "test_agent")
        
        # Verify all three commands were executed
        assert result.count("[EXEC:") == 3, f"Expected 3 EXEC blocks, got: {result}"
        
        # Verify the file was created
        hello_file = os.path.join(tmpdir, "testdir", "hello.txt")
        assert os.path.exists(hello_file), "hello.txt should be created"
        
        with open(hello_file, 'r') as f:
            content = f.read()
        assert "Hello" in content, "File should contain Hello"
        
        print("  ✓ Mixed inline and multiline blocks work correctly")


def test_inline_read_blocks():
    """Test inline READ blocks."""
    print("\n" + "="*70)
    print("Testing inline READ blocks...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Create test files
        file1 = os.path.join(tmpdir, "file1.txt")
        file2 = os.path.join(tmpdir, "file2.txt")
        with open(file1, 'w') as f:
            f.write("Content 1")
        with open(file2, 'w') as f:
            f.write("Content 2")
        
        response = f"""Let's read files:
```READ {file1}```
```READ {file2}```
Done!"""
        
        result = processor.process_response(response, "test_agent")
        
        # Verify both files were read
        assert result.count("[READ") == 2, f"Expected 2 READ blocks, got: {result}"
        assert "Content 1" in result
        assert "Content 2" in result
        
        print("  ✓ Inline READ blocks work correctly")


def test_inline_write_blocks():
    """Test inline WRITE blocks (edge case - usually multiline)."""
    print("\n" + "="*70)
    print("Testing inline WRITE blocks...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Inline WRITE with empty content
        response = """```WRITE empty.txt```
More text here."""
        
        result = processor.process_response(response, "test_agent")
        
        # Verify file was created (even if empty)
        empty_file = os.path.join(tmpdir, "empty.txt")
        assert os.path.exists(empty_file), "empty.txt should be created"
        
        print("  ✓ Inline WRITE blocks work correctly")


def test_backticks_in_markdown():
    """Test that backticks in markdown text don't interfere."""
    print("\n" + "="*70)
    print("Testing backticks in markdown text...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        response = """Here's a file called `patches` directory:
```EXEC mkdir -p patches```

The `ls` command:
```EXEC ls -la```

All done!"""
        
        result = processor.process_response(response, "test_agent")
        
        # Verify both commands executed correctly
        assert result.count("[EXEC:") == 2, f"Expected 2 EXEC blocks, got: {result}"
        
        # Verify commands don't include the inline markdown backticks
        first_exec = result.split("[EXEC:")[1].split("]")[0]
        assert "`patches`" not in first_exec
        assert "mkdir -p patches" in first_exec
        
        print("  ✓ Backticks in markdown don't interfere with block parsing")


def test_heredoc_still_works():
    """Regression test: ensure heredoc support still works."""
    print("\n" + "="*70)
    print("Testing heredoc support (regression)...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        response = """```EXEC cat > notes.md << 'EOF'
# Notes
- Item 1
- Item 2
EOF
```"""
        
        result = processor.process_response(response, "test_agent")
        
        # Verify file was created with correct content
        notes_file = os.path.join(tmpdir, "notes.md")
        assert os.path.exists(notes_file), "notes.md should be created"
        
        with open(notes_file, 'r') as f:
            content = f.read()
        
        assert "# Notes" in content
        assert "- Item 1" in content
        assert "- Item 2" in content
        
        print("  ✓ Heredoc support still works correctly")


def main():
    """Run all tests."""
    print("="*70)
    print("INLINE EXEC BLOCKS TEST SUITE")
    print("="*70)
    
    try:
        test_inline_exec_blocks_bug()
        test_multiple_inline_blocks()
        test_mixed_inline_and_multiline()
        test_inline_read_blocks()
        test_inline_write_blocks()
        test_backticks_in_markdown()
        test_heredoc_still_works()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
