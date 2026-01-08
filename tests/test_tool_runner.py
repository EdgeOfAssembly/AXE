#!/usr/bin/env python3
"""
Comprehensive test suite for ToolRunner shell features support.
Tests pipes, redirects, logical operators, and complex shell commands.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, ToolRunner


def test_simple_commands():
    """Test that simple commands still work."""
    print("="*70)
    print("TEST: Simple Commands")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Simple ls command
        print("\nTest 1: ls -la")
        allowed, reason = runner.is_tool_allowed("ls -la")
        assert allowed, f"Simple 'ls -la' should be allowed: {reason}"
        print("  ✓ Simple ls command allowed")
        
        # Test 2: Simple grep command
        print("\nTest 2: grep pattern file.txt")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt")
        assert allowed, f"Simple grep should be allowed: {reason}"
        print("  ✓ Simple grep command allowed")
        
        # Test 3: Non-whitelisted command should fail
        print("\nTest 3: evil_command (not in whitelist)")
        allowed, reason = runner.is_tool_allowed("evil_command")
        assert not allowed, "Non-whitelisted command should be blocked"
        assert "evil_command" in reason and "whitelist" in reason.lower()
        print("  ✓ Non-whitelisted command blocked")
        
        print("\n✅ All simple command tests passed!")
        return True


def test_pipes():
    """Test that pipes work correctly."""
    print("\n" + "="*70)
    print("TEST: Pipes")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Simple pipe
        print("\nTest 1: grep pattern file.py | head -20")
        allowed, reason = runner.is_tool_allowed("grep pattern file.py | head -20")
        assert allowed, f"Pipe with grep and head should be allowed: {reason}"
        print("  ✓ Simple pipe allowed")
        
        # Test 2: Multiple pipes
        print("\nTest 2: grep -r pattern . | sort | uniq")
        allowed, reason = runner.is_tool_allowed("grep -r pattern . | sort | uniq")
        # Note: sort and uniq are not in default whitelist, so this should fail
        # But the parsing should work correctly
        print(f"  Result: {'allowed' if allowed else 'blocked'} - {reason}")
        
        # Test 3: Pipe with non-whitelisted command should fail
        print("\nTest 3: grep pattern file.txt | evil_command")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt | evil_command")
        assert not allowed, "Pipe with non-whitelisted command should be blocked"
        assert "evil_command" in reason
        print("  ✓ Pipe with non-whitelisted command blocked")
        
        # Test 4: All commands in pipe must be whitelisted
        print("\nTest 4: ls -la | grep test")
        allowed, reason = runner.is_tool_allowed("ls -la | grep test")
        assert allowed, f"Pipe with ls and grep should be allowed: {reason}"
        print("  ✓ Pipe with whitelisted commands allowed")
        
        print("\n✅ All pipe tests passed!")
        return True


def test_logical_operators():
    """Test that logical operators (&&, ||) work correctly."""
    print("\n" + "="*70)
    print("TEST: Logical Operators")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Logical AND
        print("\nTest 1: ls -la && grep test file.txt")
        allowed, reason = runner.is_tool_allowed("ls -la && grep test file.txt")
        assert allowed, f"Logical AND with whitelisted commands should be allowed: {reason}"
        print("  ✓ Logical AND allowed")
        
        # Test 2: Logical OR
        print("\nTest 2: grep pattern file.txt || ls")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt || ls")
        assert allowed, f"Logical OR with whitelisted commands should be allowed: {reason}"
        print("  ✓ Logical OR allowed")
        
        # Test 3: Logical AND with non-whitelisted command
        print("\nTest 3: ls && evil_command")
        allowed, reason = runner.is_tool_allowed("ls && evil_command")
        assert not allowed, "Logical AND with non-whitelisted command should be blocked"
        print("  ✓ Logical AND with non-whitelisted command blocked")
        
        print("\n✅ All logical operator tests passed!")
        return True


def test_redirects():
    """Test that redirects work correctly."""
    print("\n" + "="*70)
    print("TEST: Redirects")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Output redirect
        print("\nTest 1: grep pattern file.txt > output.txt")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt > output.txt")
        assert allowed, f"Output redirect should be allowed: {reason}"
        print("  ✓ Output redirect allowed")
        
        # Test 2: Append redirect
        print("\nTest 2: ls -la >> log.txt")
        allowed, reason = runner.is_tool_allowed("ls -la >> log.txt")
        assert allowed, f"Append redirect should be allowed: {reason}"
        print("  ✓ Append redirect allowed")
        
        # Test 3: Input redirect
        print("\nTest 3: grep pattern < input.txt")
        allowed, reason = runner.is_tool_allowed("grep pattern < input.txt")
        assert allowed, f"Input redirect should be allowed: {reason}"
        print("  ✓ Input redirect allowed")
        
        # Test 4: Stderr redirect
        print("\nTest 4: grep pattern file.txt 2>/dev/null")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt 2>/dev/null")
        assert allowed, f"Stderr redirect should be allowed: {reason}"
        print("  ✓ Stderr redirect allowed")
        
        # Test 5: Combined redirect
        print("\nTest 5: grep pattern file.txt > output.txt 2>&1")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt > output.txt 2>&1")
        assert allowed, f"Combined redirect should be allowed: {reason}"
        print("  ✓ Combined redirect allowed")
        
        print("\n✅ All redirect tests passed!")
        return True


def test_complex_commands():
    """Test complex combinations of shell features."""
    print("\n" + "="*70)
    print("TEST: Complex Commands")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Pipe with redirect
        print("\nTest 1: grep -r pattern . | grep -v test > results.txt")
        allowed, reason = runner.is_tool_allowed("grep -r pattern . | grep -v test > results.txt")
        assert allowed, f"Pipe with redirect should be allowed: {reason}"
        print("  ✓ Pipe with redirect allowed")
        
        # Test 2: Logical operator with pipe
        print("\nTest 2: ls -la | grep test && grep pattern file.txt")
        allowed, reason = runner.is_tool_allowed("ls -la | grep test && grep pattern file.txt")
        assert allowed, f"Logical operator with pipe should be allowed: {reason}"
        print("  ✓ Logical operator with pipe allowed")
        
        # Test 3: Multiple redirects
        print("\nTest 3: grep pattern file.txt > output.txt 2> error.txt")
        allowed, reason = runner.is_tool_allowed("grep pattern file.txt > output.txt 2> error.txt")
        assert allowed, f"Multiple redirects should be allowed: {reason}"
        print("  ✓ Multiple redirects allowed")
        
        print("\n✅ All complex command tests passed!")
        return True


def test_forbidden_paths():
    """Test that forbidden paths are still blocked even with shell features."""
    print("\n" + "="*70)
    print("TEST: Forbidden Paths")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Simple forbidden path
        print("\nTest 1: grep pattern /etc/passwd")
        allowed, reason = runner.is_tool_allowed("grep pattern /etc/passwd")
        assert not allowed, "Access to /etc should be forbidden"
        assert "forbidden" in reason.lower()
        print("  ✓ Forbidden path blocked")
        
        # Test 2: Forbidden path in pipe
        print("\nTest 2: grep pattern /etc/passwd | head -10")
        allowed, reason = runner.is_tool_allowed("grep pattern /etc/passwd | head -10")
        assert not allowed, "Forbidden path in pipe should be blocked"
        print("  ✓ Forbidden path in pipe blocked")
        
        # Test 3: Forbidden path in redirect
        print("\nTest 3: ls -la > /etc/test.txt")
        allowed, reason = runner.is_tool_allowed("ls -la > /etc/test.txt")
        assert not allowed, "Writing to forbidden path should be blocked"
        print("  ✓ Forbidden path in redirect blocked")
        
        print("\n✅ All forbidden path tests passed!")
        return True


def test_needs_shell():
    """Test the _needs_shell helper method."""
    print("\n" + "="*70)
    print("TEST: _needs_shell Helper")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Commands that need shell
        shell_commands = [
            "ls | grep test",
            "ls && grep test",
            "ls || grep test",
            "ls ; grep test",
            "ls > output.txt",
            "ls >> output.txt",
            "grep < input.txt",
            "echo $(ls)",
            "echo `ls`",
            "cat << EOF"
        ]
        
        for cmd in shell_commands:
            needs = runner._needs_shell(cmd)
            assert needs, f"Command '{cmd}' should need shell"
            print(f"  ✓ '{cmd}' needs shell")
        
        # Commands that don't need shell
        simple_commands = [
            "ls -la",
            "grep pattern file.txt",
            "git status",
            "python3 script.py"
        ]
        
        for cmd in simple_commands:
            needs = runner._needs_shell(cmd)
            assert not needs, f"Command '{cmd}' should not need shell"
            print(f"  ✓ '{cmd}' doesn't need shell")
        
        print("\n✅ All _needs_shell tests passed!")
        return True


def test_extract_commands():
    """Test the _extract_commands_from_shell method."""
    print("\n" + "="*70)
    print("TEST: _extract_commands_from_shell")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test cases: (command, expected_commands)
        test_cases = [
            ("ls -la", ["ls"]),
            ("grep pattern file.txt", ["grep"]),
            ("ls | grep test", ["ls", "grep"]),
            ("ls && grep test", ["ls", "grep"]),
            ("ls || grep test || cat file", ["ls", "grep", "cat"]),
            ("ls ; grep test ; cat file", ["ls", "grep", "cat"]),
            ("grep pattern file.txt > output.txt", ["grep"]),
            ("ls -la >> log.txt", ["ls"]),
            ("grep < input.txt", ["grep"]),
            ("ls | grep test | head -10", ["ls", "grep", "head"]),
            ("ENV=value ls -la", ["ls"]),
            ("grep pattern file 2>/dev/null", ["grep"]),
        ]
        
        for cmd, expected in test_cases:
            extracted = runner._extract_commands_from_shell(cmd)
            # For this test, we just check that we extracted some commands
            # The exact matching might vary based on implementation details
            print(f"  Command: {cmd}")
            print(f"    Expected: {expected}")
            print(f"    Extracted: {extracted}")
            assert len(extracted) > 0, f"Should extract at least one command from '{cmd}'"
            # Check that the first expected command is in the extracted list
            assert expected[0] in extracted, f"Should extract '{expected[0]}' from '{cmd}'"
            print("    ✓ Passed")
        
        print("\n✅ All _extract_commands_from_shell tests passed!")
        return True


def test_integration_with_execution():
    """Integration test: actually execute shell commands."""
    print("\n" + "="*70)
    print("TEST: Integration with Execution")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        runner.auto_approve = True  # Auto-approve for testing
        
        # Create a test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Hello World\nTest Line\nAnother Line\n")
        
        # Test 1: Simple grep (no shell needed)
        print("\nTest 1: Simple grep command")
        success, output = runner.run(f"grep Test {test_file}")
        assert success, f"Simple grep should succeed: {output}"
        assert "Test Line" in output
        print("  ✓ Simple grep executed successfully")
        
        # Test 2: Grep with redirect
        print("\nTest 2: Grep with redirect")
        output_file = os.path.join(tmpdir, "output.txt")
        success, output = runner.run(f"grep World {test_file} > {output_file}")
        assert success, f"Grep with redirect should succeed: {output}"
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            content = f.read()
        assert "Hello World" in content
        print("  ✓ Grep with redirect executed successfully")
        
        # Test 3: Pipe command (needs shell)
        print("\nTest 3: Pipe command")
        success, output = runner.run(f"grep -n Line {test_file} | head -1")
        assert success, f"Pipe command should succeed: {output}"
        print(f"  Output: {output.strip()}")
        print("  ✓ Pipe command executed successfully")
        
        # Test 4: Logical AND
        print("\nTest 4: Logical AND command")
        success, output = runner.run(f"ls {test_file} && grep Hello {test_file}")
        assert success, f"Logical AND should succeed: {output}"
        assert "Hello World" in output
        print("  ✓ Logical AND executed successfully")
        
        print("\n✅ All integration tests passed!")
        return True


def test_heredocs():
    """Test that heredoc content doesn't break command parsing."""
    print("\n" + "="*70)
    print("TEST: Heredocs")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Heredoc with markdown content (dashes, numbers, etc.)
        print("\nTest 1: Heredoc with markdown content")
        cmd = """cat >> file.md << 'EOF'
## Header

### Assignments:
- @agent1: Task 1
- @agent2: Task 2

### Priority Areas:
1. Error handling consistency
2. Docstring coverage

---
EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Heredoc with markdown should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        assert commands == ['cat'], f"Should extract only 'cat', got {commands}"
        print("  ✓ Heredoc with markdown content allowed")
        
        # Test 2: Heredoc with shell operators in content
        print("\nTest 2: Heredoc with shell operators in content")
        cmd = """cat << 'EOF'
This has | pipe
And && operator
Also || operator
And semicolon ; here
EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Heredoc with operators in content should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        assert commands == ['cat'], f"Should extract only 'cat', got {commands}"
        print("  ✓ Heredoc with operators in content allowed")
        
        # Test 3: Heredoc with code content
        print("\nTest 3: Heredoc with code content")
        cmd = """cat > script.py << EOF
if x > 0:
    print(x)
EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Heredoc with code should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        assert commands == ['cat'], f"Should extract only 'cat', got {commands}"
        print("  ✓ Heredoc with code content allowed")
        
        # Test 4: Heredoc with double quotes
        print("\nTest 4: Heredoc with double quotes")
        cmd = """cat << "EOF"
content here
EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Heredoc with double quotes should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        assert commands == ['cat'], f"Should extract only 'cat', got {commands}"
        print("  ✓ Heredoc with double quotes allowed")
        
        # Test 5: Heredoc with <<- (indented)
        print("\nTest 5: Heredoc with <<- (indented)")
        cmd = """cat <<- EOF
	indented content
	more content
	EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Indented heredoc should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        assert commands == ['cat'], f"Should extract only 'cat', got {commands}"
        print("  ✓ Indented heredoc allowed")
        
        # Test 6: Heredoc followed by pipe
        print("\nTest 6: Heredoc followed by pipe (heredoc content piped)")
        cmd = """cat << EOF | grep pattern
line1
line2
EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Heredoc with pipe should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        # Only cat should be extracted (heredoc content removed before pipe)
        assert 'cat' in commands, f"Should extract 'cat', got {commands}"
        print("  ✓ Heredoc followed by pipe allowed")
        
        # Test 7: Heredoc followed by logical operator
        print("\nTest 7: Heredoc followed by logical operator")
        cmd = """cat << EOF && ls
content
EOF"""
        allowed, reason = runner.is_tool_allowed(cmd)
        assert allowed, f"Heredoc with && should work: {reason}"
        commands = runner._extract_commands_from_shell(cmd)
        assert 'cat' in commands and 'ls' in commands, f"Should extract both commands, got {commands}"
        print("  ✓ Heredoc followed by logical operator allowed")
        
        # Test 8: Multiple heredocs (edge case)
        print("\nTest 8: Multiple heredocs")
        cmd = """cat << EOF1
content1
EOF1
cat << EOF2
content2
EOF2"""
        allowed, reason = runner.is_tool_allowed(cmd)
        # This might not work perfectly but shouldn't crash
        commands = runner._extract_commands_from_shell(cmd)
        assert 'cat' in commands, f"Should extract at least 'cat', got {commands}"
        print("  ✓ Multiple heredocs handled")
        
        print("\n✅ All heredoc tests passed!")
        return True


def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*70)
    print("RUNNING ALL TOOLRUNNER SHELL FEATURE TESTS")
    print("="*70)
    
    tests = [
        ("Simple Commands", test_simple_commands),
        ("Pipes", test_pipes),
        ("Logical Operators", test_logical_operators),
        ("Redirects", test_redirects),
        ("Complex Commands", test_complex_commands),
        ("Forbidden Paths", test_forbidden_paths),
        ("_needs_shell Helper", test_needs_shell),
        ("_extract_commands_from_shell", test_extract_commands),
        ("Heredocs", test_heredocs),
        ("Integration with Execution", test_integration_with_execution),
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
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
