#!/usr/bin/env python3
"""
Test suite for EXEC blocks with heredoc content.
This test verifies the fix for the heredoc execution issue where heredoc
content was being lost when EXEC blocks were parsed.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, ResponseProcessor, ToolRunner


def test_exec_block_with_heredoc():
    """Test EXEC blocks with heredoc content are executed correctly."""
    print("\n" + "="*70)
    print("Testing EXEC blocks with heredocs...")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Test 1: EXEC with heredoc (command on same line as EXEC)
        print("\nTest 1: Heredoc with command on EXEC line")
        response1 = """I'll create a file using a heredoc:

```EXEC cat > notes.md << 'EOF'
# Notes
- Item 1
- Item 2
1. First priority
2. Second priority
---
EOF
```

Done!"""
        
        result1 = processor.process_response(response1, "test_agent")
        print(f"Result includes: {repr(result1[:200])}")
        
        # Verify file was created
        notes_file = os.path.join(tmpdir, "notes.md")
        assert os.path.exists(notes_file), "notes.md should be created"
        
        with open(notes_file, 'r') as f:
            content1 = f.read()
        
        print(f"File content:\n{content1}")
        assert "# Notes" in content1, "Should contain header"
        assert "- Item 1" in content1, "Should contain first item"
        assert "- Item 2" in content1, "Should contain second item"
        assert "1. First priority" in content1, "Should contain numbered list"
        assert "---" in content1, "Should contain separator"
        
        print("  ✓ EXEC with heredoc on same line works correctly")
        
        # Test 2: EXEC with heredoc (command on content line)
        print("\nTest 2: Heredoc with command on content line")
        response2 = """Creating another file:

```EXEC
cat > script.sh << 'EOF'
#!/bin/bash
echo "Test script"
exit 0
EOF
```

Script created!"""
        
        result2 = processor.process_response(response2, "test_agent")
        
        # Verify file was created
        script_file = os.path.join(tmpdir, "script.sh")
        assert os.path.exists(script_file), "script.sh should be created"
        
        with open(script_file, 'r') as f:
            content2 = f.read()
        
        print(f"File content:\n{content2}")
        assert "#!/bin/bash" in content2, "Should contain shebang"
        assert 'echo "Test script"' in content2, "Should contain echo command"
        assert "exit 0" in content2, "Should contain exit command"
        
        print("  ✓ EXEC with heredoc on content line works correctly")
        
        # Test 3: Multiple heredocs in sequence
        print("\nTest 3: Multiple EXEC blocks with heredocs")
        response3 = """Creating multiple files:

```EXEC cat > file1.txt << EOF
Content 1
EOF
```

```EXEC cat > file2.txt << EOF
Content 2
EOF
```

Both files created!"""
        
        result3 = processor.process_response(response3, "test_agent")
        
        # Verify both files were created
        file1 = os.path.join(tmpdir, "file1.txt")
        file2 = os.path.join(tmpdir, "file2.txt")
        assert os.path.exists(file1), "file1.txt should be created"
        assert os.path.exists(file2), "file2.txt should be created"
        
        with open(file1, 'r') as f:
            assert "Content 1" in f.read()
        with open(file2, 'r') as f:
            assert "Content 2" in f.read()
        
        print("  ✓ Multiple EXEC blocks with heredocs work correctly")
        
        # Test 4: Simple EXEC without heredoc (regression test)
        print("\nTest 4: Simple EXEC without heredoc (regression test)")
        response4 = """```EXEC ls -la```"""
        
        result4 = processor.process_response(response4, "test_agent")
        
        # Just verify it doesn't error
        assert "ERROR" not in result4 or "not in whitelist" not in result4
        print("  ✓ Simple EXEC commands still work")
        
        print("\n✅ All EXEC heredoc tests passed!")
        return True


if __name__ == '__main__':
    print("="*70)
    print("RUNNING EXEC HEREDOC TEST")
    print("="*70)
    
    try:
        test_exec_block_with_heredoc()
        print("\n" + "="*70)
        print("TEST PASSED ✅")
        print("="*70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
