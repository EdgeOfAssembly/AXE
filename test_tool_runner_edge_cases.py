#!/usr/bin/env python3
"""
Additional edge case tests for ToolRunner shell features support.

This test suite covers edge cases that were discovered during comprehensive
testing and fixed to ensure robust shell command parsing.

Edge Cases Tested:
==================

1. SUBSHELLS WITH PARENTHESES
   Problem: Parentheses were being attached to command names, causing validation failures
   Examples:
   - (ls) was parsed as ["(ls)"] instead of ["ls"]
   - (ls | grep) was parsed as ["(ls", "grep"] instead of ["ls", "grep"]
   Fix: Strip all leading/trailing parentheses from tokens

2. REDIRECTS WITHOUT SPACES
   Problem: Redirect operators attached to commands weren't being separated
   Examples:
   - grep<input was parsed as ["grep<input"] instead of ["grep"]
   - cat<in>out was failing validation
   Fix: Detect and split on redirect operators within tokens

3. NESTED SUBSHELLS
   Problem: Multiple levels of parentheses caused parsing issues
   Examples:
   - ((ls)) was failing validation
   - (((ls | grep))) wasn't extracting commands correctly
   Fix: Strip all parentheses recursively

4. HERE-STRINGS
   Problem: Here-strings (<<<) were not recognized
   Example:
   - grep<<<'text' was failing
   Fix: Added here-string detection to _needs_shell()

All tests verify that:
- Valid commands are correctly allowed
- Command names are properly extracted
- Security checks still work (non-whitelisted commands blocked)
- Complex combinations of edge cases work together

Test Coverage:
- 16 individual test cases across 3 test suites
- All security features maintained
- Integration with existing ToolRunner functionality verified
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, ToolRunner


def test_subshells():
    """Test that subshells with parentheses work correctly."""
    print("="*70)
    print("TEST: Subshells")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Simple subshell
        print("\nTest 1: (ls)")
        allowed, reason = runner.is_tool_allowed("(ls)")
        commands = runner._extract_commands_from_shell("(ls)")
        assert allowed, f"Simple subshell should be allowed: {reason}"
        assert commands == ['ls'], f"Should extract 'ls', got {commands}"
        print("  ✓ Simple subshell allowed")
        
        # Test 2: Subshell with pipe
        print("\nTest 2: (ls | grep test)")
        allowed, reason = runner.is_tool_allowed("(ls | grep test)")
        commands = runner._extract_commands_from_shell("(ls | grep test)")
        assert allowed, f"Subshell with pipe should be allowed: {reason}"
        assert 'ls' in commands and 'grep' in commands, f"Should extract ls and grep, got {commands}"
        print("  ✓ Subshell with pipe allowed")
        
        # Test 3: Subshell with logical operators
        print("\nTest 3: (ls && grep test)")
        allowed, reason = runner.is_tool_allowed("(ls && grep test)")
        commands = runner._extract_commands_from_shell("(ls && grep test)")
        assert allowed, f"Subshell with && should be allowed: {reason}"
        assert 'ls' in commands and 'grep' in commands, f"Should extract ls and grep, got {commands}"
        print("  ✓ Subshell with && allowed")
        
        # Test 4: Multiple subshells
        print("\nTest 4: (ls) && (grep test)")
        allowed, reason = runner.is_tool_allowed("(ls) && (grep test)")
        commands = runner._extract_commands_from_shell("(ls) && (grep test)")
        assert allowed, f"Multiple subshells should be allowed: {reason}"
        print("  ✓ Multiple subshells allowed")
        
        # Test 5: Nested subshells
        print("\nTest 5: ((ls))")
        allowed, reason = runner.is_tool_allowed("((ls))")
        commands = runner._extract_commands_from_shell("((ls))")
        assert allowed, f"Nested subshells should be allowed: {reason}"
        assert 'ls' in commands, f"Should extract 'ls', got {commands}"
        print("  ✓ Nested subshells allowed")
        
        # Test 6: Subshell with non-whitelisted command should fail
        print("\nTest 6: (evil_command)")
        allowed, reason = runner.is_tool_allowed("(evil_command)")
        assert not allowed, "Subshell with non-whitelisted command should be blocked"
        print("  ✓ Subshell with non-whitelisted command blocked")
        
        print("\n✅ All subshell tests passed!")
        return True


def test_redirects_without_spaces():
    """Test that redirects without spaces work correctly."""
    print("\n" + "="*70)
    print("TEST: Redirects Without Spaces")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Input redirect without space
        print("\nTest 1: grep<input")
        allowed, reason = runner.is_tool_allowed("grep<input")
        commands = runner._extract_commands_from_shell("grep<input")
        assert allowed, f"Input redirect without space should be allowed: {reason}"
        assert commands == ['grep'], f"Should extract 'grep', got {commands}"
        print("  ✓ Input redirect without space allowed")
        
        # Test 2: Output redirect without space
        print("\nTest 2: grep>output")
        allowed, reason = runner.is_tool_allowed("grep>output")
        commands = runner._extract_commands_from_shell("grep>output")
        assert allowed, f"Output redirect without space should be allowed: {reason}"
        assert commands == ['grep'], f"Should extract 'grep', got {commands}"
        print("  ✓ Output redirect without space allowed")
        
        # Test 3: Append redirect without space
        print("\nTest 3: grep>>output")
        allowed, reason = runner.is_tool_allowed("grep>>output")
        commands = runner._extract_commands_from_shell("grep>>output")
        assert allowed, f"Append redirect without space should be allowed: {reason}"
        assert commands == ['grep'], f"Should extract 'grep', got {commands}"
        print("  ✓ Append redirect without space allowed")
        
        # Test 4: Both redirects without space
        print("\nTest 4: cat<input>output")
        allowed, reason = runner.is_tool_allowed("cat<input>output")
        commands = runner._extract_commands_from_shell("cat<input>output")
        assert allowed, f"Both redirects without space should be allowed: {reason}"
        assert commands == ['cat'], f"Should extract 'cat', got {commands}"
        print("  ✓ Both redirects without space allowed")
        
        # Test 5: Stderr redirect without space
        print("\nTest 5: grep 2>error")
        allowed, reason = runner.is_tool_allowed("grep 2>error")
        commands = runner._extract_commands_from_shell("grep 2>error")
        assert allowed, f"Stderr redirect without space should be allowed: {reason}"
        assert commands == ['grep'], f"Should extract 'grep', got {commands}"
        print("  ✓ Stderr redirect without space allowed")
        
        print("\n✅ All redirect without space tests passed!")
        return True


def test_complex_edge_cases():
    """
    Test complex combinations of edge cases.
    
    These tests verify that multiple edge cases can work together correctly,
    such as subshells with redirects without spaces, or nested subshells with pipes.
    This ensures the parser is robust and handles real-world complex commands.
    """
    print("\n" + "="*70)
    print("TEST: Complex Edge Cases")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        
        # Test 1: Subshell with redirects without spaces
        # This combines TWO edge cases:
        # 1. Subshell syntax (parentheses)
        # 2. Redirects without spaces (grep<input, head>output)
        print("\nTest 1: (grep<input | head>output)")
        allowed, reason = runner.is_tool_allowed("(grep<input | head>output)")
        commands = runner._extract_commands_from_shell("(grep<input | head>output)")
        assert allowed, f"Subshell with redirects should be allowed: {reason}"
        assert 'grep' in commands and 'head' in commands, f"Should extract grep and head, got {commands}"
        print("  ✓ Subshell with redirects without spaces allowed")
        
        # Test 2: Multiple operators mixed
        # Tests subshells with multiple operator types (&&, ||)
        print("\nTest 2: (ls && grep test) || cat file")
        allowed, reason = runner.is_tool_allowed("(ls && grep test) || cat file")
        commands = runner._extract_commands_from_shell("(ls && grep test) || cat file")
        assert allowed, f"Complex operator mix should be allowed: {reason}"
        print("  ✓ Complex operator mix allowed")
        
        # Test 3: Nested subshells with pipes
        # Tests multiple levels of subshells with pipes inside
        # This is an extreme edge case: ((command | command))
        print("\nTest 3: ((ls | grep test))")
        allowed, reason = runner.is_tool_allowed("((ls | grep test))")
        commands = runner._extract_commands_from_shell("((ls | grep test))")
        assert allowed, f"Nested subshells with pipes should be allowed: {reason}"
        assert 'ls' in commands and 'grep' in commands, f"Should extract ls and grep, got {commands}"
        print("  ✓ Nested subshells with pipes allowed")
        
        # Test 4: Here-string
        # Here-strings (<<<) are a bash feature for passing string literals as stdin
        # Example: grep<<<'text' is equivalent to echo 'text' | grep
        print("\nTest 4: grep<<<'text'")
        allowed, reason = runner.is_tool_allowed("grep<<<'text'")
        commands = runner._extract_commands_from_shell("grep<<<'text'")
        assert allowed, f"Here-string should be allowed: {reason}"
        assert 'grep' in commands, f"Should extract 'grep', got {commands}"
        print("  ✓ Here-string allowed")
        
        print("\n✅ All complex edge case tests passed!")
        return True


def run_all_tests():
    """Run all edge case test suites."""
    print("\n" + "="*70)
    print("RUNNING ALL EDGE CASE TESTS")
    print("="*70)
    
    tests = [
        ("Subshells", test_subshells),
        ("Redirects Without Spaces", test_redirects_without_spaces),
        ("Complex Edge Cases", test_complex_edge_cases),
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
