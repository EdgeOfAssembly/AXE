#!/usr/bin/env python3
"""
Test suite for heredoc execution fix.

Tests that heredoc commands execute with content intact after the fix
described in the problem statement. Ensures that _strip_heredoc_content()
is only used for validation and never affects execution.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, ToolRunner


def test_heredoc_execution_with_content():
    """Test that heredoc commands execute with full content intact."""
    print("="*70)
    print("TEST: Heredoc Execution with Content Intact")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        runner.auto_approve = True  # Auto-approve for testing
        
        # Test case from problem statement
        test_file = os.path.join(tmpdir, "test.md")
        cmd = f"""cat >> {test_file} << 'EOF'
- Item 1
- Item 2
1. First priority
---
EOF"""
        
        print(f"\nCommand to execute:\n{cmd}\n")
        
        # Verify validation works (should allow the command)
        allowed, reason = runner.is_tool_allowed(cmd)
        print(f"is_tool_allowed: {allowed} - {reason}")
        assert allowed, f"Heredoc command should be allowed: {reason}"
        
        # Execute the command
        print("\nExecuting command...")
        success, output = runner.run(cmd)
        
        print("\nExecution result:")
        print(f"  Success: {success}")
        print(f"  Output: {output}")
        
        # Verify execution succeeded
        assert success, f"Execution should succeed: {output}"
        
        # Verify file was created
        assert os.path.exists(test_file), f"File should be created at {test_file}"
        
        # Verify file has the correct content
        with open(test_file, 'r') as f:
            content = f.read()
        
        print(f"\nFile content ({len(content)} bytes):\n{content}")
        
        # Check for all expected lines
        expected_lines = ["- Item 1", "- Item 2", "1. First priority", "---"]
        for line in expected_lines:
            assert line in content, f"Expected line missing: {line}"
        
        print("\n✅ TEST PASSED: Heredoc executed with content intact!")
        return True


def test_heredoc_stripping_for_validation_only():
    """Test that _strip_heredoc_content strips content but doesn't affect execution."""
    print("\n" + "="*70)
    print("TEST: Heredoc Stripping for Validation Only")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Original command with heredoc
        cmd = """cat << 'EOF'
line with | pipe
line with && operator
line with || operator
EOF"""
        
        print(f"\nOriginal command:\n{cmd}\n")
        
        # Test that stripping works for validation
        stripped = runner._strip_heredoc_content(cmd)
        print(f"Stripped (for validation):\n{stripped}\n")
        
        # Verify stripped version is different
        assert stripped != cmd, "Stripped should differ from original"
        assert len(stripped) < len(cmd), "Stripped should be shorter"
        assert "<<" in stripped, "Heredoc marker should remain"
        assert "line with" not in stripped, "Content should be removed"
        
        # Verify command names extraction works with stripping
        commands = runner._extract_commands_from_shell(cmd)
        print(f"Commands extracted: {commands}")
        assert commands == ['cat'], f"Should extract only 'cat', got {commands}"
        
        # Verify the original cmd variable is unchanged
        assert "line with" in cmd, "Original cmd should still have content"
        
        print("\n✅ TEST PASSED: Stripping works for validation without modifying original!")
        return True


def test_heredoc_with_special_markdown_content():
    """Test heredoc with markdown content that could trigger false positives."""
    print("\n" + "="*70)
    print("TEST: Heredoc with Special Markdown Content")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        runner.auto_approve = True
        
        test_file = os.path.join(tmpdir, "notes.md")
        
        # Markdown content with potential false positive triggers
        cmd = f"""cat >> {test_file} << 'EOF'
## Tasks
- Task 1: Implement feature
- Task 2: Write tests
- Task 3: Code review

### Priority Areas:
1. Error handling consistency
2. Docstring coverage
3. Type hints

### Shell Examples:
```bash
ls -la | grep test
cat file.txt && echo done
```

---
Notes: Use || for fallback
EOF"""
        
        print(f"\nCommand:\n{cmd}\n")
        
        # Verify validation passes (shouldn't treat content as commands)
        allowed, reason = runner.is_tool_allowed(cmd)
        print(f"is_tool_allowed: {allowed} - {reason}")
        assert allowed, f"Should be allowed: {reason}"
        
        # Execute
        success, output = runner.run(cmd)
        assert success, f"Should execute successfully: {output}"
        assert os.path.exists(test_file), "File should be created"
        
        # Verify all content is present
        with open(test_file, 'r') as f:
            content = f.read()
        
        expected_fragments = [
            "## Tasks",
            "- Task 1",
            "1. Error handling",
            "ls -la | grep test",
            "cat file.txt && echo done",
            "Use || for fallback",
            "---"
        ]
        
        for fragment in expected_fragments:
            assert fragment in content, f"Missing fragment: {fragment}"
        
        print("\n✅ TEST PASSED: Markdown content preserved correctly!")
        return True


def test_heredoc_followed_by_pipe():
    """Test heredoc followed by a pipe operator."""
    print("\n" + "="*70)
    print("TEST: Heredoc Followed by Pipe")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        runner.auto_approve = True
        
        # Heredoc content piped to grep
        cmd = """cat << EOF | grep test
line 1
test line 2
line 3
EOF"""
        
        print(f"\nCommand:\n{cmd}\n")
        
        # Verify both commands are extracted
        commands = runner._extract_commands_from_shell(cmd)
        print(f"Commands extracted: {commands}")
        # Should find 'cat' and possibly 'grep' depending on how heredoc is handled
        assert 'cat' in commands, "Should extract 'cat'"
        
        # Verify validation passes
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Should be allowed: {reason}"
        
        # Execute
        success, output = runner.run(cmd)
        print(f"\nExecution output:\n{output}")
        assert success, f"Should execute successfully: {output}"
        assert "test line 2" in output, "Grep should find the test line"
        
        print("\n✅ TEST PASSED: Heredoc with pipe works correctly!")
        return True


def test_multiple_heredocs():
    """Test command with multiple heredocs."""
    print("\n" + "="*70)
    print("TEST: Multiple Heredocs")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        runner.auto_approve = True
        
        file1 = os.path.join(tmpdir, "file1.txt")
        file2 = os.path.join(tmpdir, "file2.txt")
        
        # Two separate heredoc commands with logical AND
        cmd = f"""cat > {file1} << 'EOF1'
Content for file 1
EOF1
cat > {file2} << 'EOF2'
Content for file 2
EOF2"""
        
        print(f"\nCommand:\n{cmd}\n")
        
        # Verify validation passes
        allowed, reason = runner.is_tool_allowed(cmd)
        print(f"is_tool_allowed: {allowed} - {reason}")
        assert allowed, f"Should be allowed: {reason}"
        
        # Execute
        success, output = runner.run(cmd)
        assert success, f"Should execute successfully: {output}"
        
        # Verify both files were created with correct content
        assert os.path.exists(file1), "File 1 should be created"
        assert os.path.exists(file2), "File 2 should be created"
        
        with open(file1, 'r') as f:
            content1 = f.read()
        with open(file2, 'r') as f:
            content2 = f.read()
        
        assert "Content for file 1" in content1, "File 1 content incorrect"
        assert "Content for file 2" in content2, "File 2 content incorrect"
        
        print("\n✅ TEST PASSED: Multiple heredocs work correctly!")
        return True


def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*70)
    print("RUNNING HEREDOC EXECUTION FIX TESTS")
    print("="*70)
    
    tests = [
        ("Heredoc Execution with Content", test_heredoc_execution_with_content),
        ("Heredoc Stripping for Validation Only", test_heredoc_stripping_for_validation_only),
        ("Heredoc with Markdown Content", test_heredoc_with_special_markdown_content),
        ("Heredoc Followed by Pipe", test_heredoc_followed_by_pipe),
        ("Multiple Heredocs", test_multiple_heredocs),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe fix ensures that:")
        print("  • Heredoc content is stripped only for validation")
        print("  • Original commands with heredocs are executed intact")
        print("  • No false positives from heredoc content")
        print("  • Documentation clearly separates validation from execution")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
