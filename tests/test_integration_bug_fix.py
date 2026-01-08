#!/usr/bin/env python3
"""
Integration test that simulates the exact bug scenario from the problem statement.
Tests that reading MISSION.md does NOT trigger false positives for any tokens.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import (
    detect_agent_token, 
    AGENT_TOKEN_BREAK_REQUEST, 
    AGENT_TOKEN_EMERGENCY, 
    AGENT_TOKEN_SPAWN, 
    AGENT_TOKEN_TASK_COMPLETE,
    AGENT_TOKEN_PASS
)


def test_problem_statement_scenario():
    """
    Simulate the exact scenario from the problem statement:
    Agent reads MISSION.md (or axe.py) and AXE should NOT detect tokens in the echoed content.
    """
    print("Testing: Problem statement scenario - reading files with token definitions...")
    
    # Simulate reading axe.py with token definitions (like in the problem statement)
    # This is what the agent would see after using a read tool
    response = '''Let me read the token definitions from axe.py:

--- Execution Results ---
<result>
<function_result>
<result>
# Agent communication tokens
AGENT_TOKEN_PASS = "[[AGENT_PASS_TURN]]"
AGENT_TOKEN_TASK_COMPLETE = "[[AGENT_TASK_COMPLETE:"  # Ends with ]]
AGENT_TOKEN_BREAK_REQUEST = "[[AGENT_BREAK_REQUEST:"  # Ends with ]]
AGENT_TOKEN_EMERGENCY = "[[AGENT_EMERGENCY:"  # Ends with ]]
AGENT_TOKEN_SPAWN = "[[AGENT_SPAWN:"  # Ends with ]]
AGENT_TOKEN_STATUS = "[[AGENT_STATUS]]"
</result>
</function_result>
</result>

Now I understand how the tokens work. I'll proceed with the task.'''
    
    # Test each token - NONE should trigger
    print("\n  Testing token detection in file content:")
    
    found, _ = detect_agent_token(response, AGENT_TOKEN_BREAK_REQUEST)
    assert not found, "❌ AGENT_TOKEN_BREAK_REQUEST should NOT trigger (Bug 1 not fixed!)"
    print("    ✓ AGENT_TOKEN_BREAK_REQUEST: not triggered")
    
    found, _ = detect_agent_token(response, AGENT_TOKEN_EMERGENCY)
    assert not found, "❌ AGENT_TOKEN_EMERGENCY should NOT trigger (Bug 1 not fixed!)"
    print("    ✓ AGENT_TOKEN_EMERGENCY: not triggered")
    
    found, _ = detect_agent_token(response, AGENT_TOKEN_SPAWN)
    assert not found, "❌ AGENT_TOKEN_SPAWN should NOT trigger (Bug 1 not fixed!)"
    print("    ✓ AGENT_TOKEN_SPAWN: not triggered")
    
    found, _ = detect_agent_token(response, AGENT_TOKEN_TASK_COMPLETE)
    assert not found, "❌ AGENT_TOKEN_TASK_COMPLETE should NOT trigger (Bug 1 not fixed!)"
    print("    ✓ AGENT_TOKEN_TASK_COMPLETE: not triggered")
    
    found, _ = detect_agent_token(response, AGENT_TOKEN_PASS)
    assert not found, "❌ AGENT_TOKEN_PASS should NOT trigger (Bug 1 not fixed!)"
    print("    ✓ AGENT_TOKEN_PASS: not triggered")
    
    print("\n✓ PASSED: Problem statement scenario - no false positives!")


def test_genuine_tokens_still_work():
    """
    Verify that genuine tokens OUTSIDE of file content still work correctly.
    """
    print("\nTesting: Genuine tokens still trigger correctly...")
    
    # Scenario: Agent reads file, then issues a genuine break request
    response = '''<result>
AGENT_TOKEN_BREAK_REQUEST = "[[AGENT_BREAK_REQUEST:"  # Ends with ]]
</result>

After reading that, I'm tired. [[AGENT_BREAK_REQUEST: coffee, need rest]]'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_BREAK_REQUEST)
    assert found, "Genuine token should still trigger!"
    assert "coffee" in content, f"Content should be extracted: got '{content}'"
    print("  ✓ Genuine break request after reading file: triggers correctly")
    
    # Scenario: Agent reads file, then completes task
    response2 = '''<result>
AGENT_TOKEN_TASK_COMPLETE = "[[AGENT_TASK_COMPLETE:"  # Ends with ]]
</result>

Done! [[AGENT_TASK_COMPLETE: all requirements met]]'''
    
    found, content = detect_agent_token(response2, AGENT_TOKEN_TASK_COMPLETE)
    assert found, "Genuine token should still trigger!"
    assert "requirements met" in content, f"Content should be extracted: got '{content}'"
    print("  ✓ Genuine task complete after reading file: triggers correctly")
    
    print("\n✓ PASSED: Genuine tokens still work!")


def test_multiple_formats():
    """Test various file read formats don't trigger false positives."""
    print("\nTesting: Various file read formats...")
    
    formats = [
        # Format 1: Direct result block
        '''<result>
[[AGENT_BREAK_REQUEST: coffee]]
</result>''',
        
        # Format 2: Function result wrapper
        '''<function_result>
<result>
[[AGENT_EMERGENCY: critical]]
</result>
</function_result>''',
        
        # Format 3: Nested deeply
        '''<result>
<function_result>
<result>
<another>
[[AGENT_SPAWN: claude, help needed]]
</another>
</result>
</function_result>
</result>''',
        
        # Format 4: READ block
        '''[READ axe.py]
[[AGENT_TASK_COMPLETE: done]]

Continuing...''',
        
        # Format 5: Code block
        '''```python
print("[[AGENT_BREAK_REQUEST: tired]]")
```''',
    ]
    
    for i, fmt in enumerate(formats, 1):
        # Test all tokens
        for token in [AGENT_TOKEN_BREAK_REQUEST, AGENT_TOKEN_EMERGENCY, 
                      AGENT_TOKEN_SPAWN, AGENT_TOKEN_TASK_COMPLETE]:
            found, _ = detect_agent_token(fmt, token)
            assert not found, f"Format {i} should not trigger any token"
        print(f"  ✓ Format {i}: no false positives")
    
    print("\n✓ PASSED: All file read formats are safe!")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("INTEGRATION TEST: Problem Statement Bug Scenario")
    print("=" * 70)
    
    try:
        test_problem_statement_scenario()
        test_genuine_tokens_still_work()
        test_multiple_formats()
        
        print("\n" + "=" * 70)
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("=" * 70)
        print("\nBug 1 (False Token Detection) is FIXED:")
        print("  ✓ Reading files with token definitions doesn't trigger false positives")
        print("  ✓ Genuine tokens outside file content still work correctly")
        print("  ✓ All file read formats (result blocks, READ blocks, code blocks) are safe")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
