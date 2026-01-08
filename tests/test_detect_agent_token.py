#!/usr/bin/env python3
"""
Test script for detect_agent_token function to prevent false positives from file content.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import detect_agent_token, AGENT_TOKEN_BREAK_REQUEST, AGENT_TOKEN_EMERGENCY, AGENT_TOKEN_SPAWN, AGENT_TOKEN_TASK_COMPLETE


def test_break_request_in_result_block():
    """Break request token in <result> block should not trigger."""
    print("Testing: Break request token in <result> block...")
    response = '''Let me read the file:
    
<result>
<function_result>
<result>
AGENT_TOKEN_BREAK_REQUEST = "[[AGENT_BREAK_REQUEST:"  # Ends with ]]
</result>
</function_result>
</result>

Now analyzing the code...'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_BREAK_REQUEST)
    assert not found, "Token in result block should not trigger"
    print("✓ PASSED: Break request in result block does not trigger")


def test_emergency_in_result_block():
    """Emergency token in <result> block should not trigger."""
    print("\nTesting: Emergency token in <result> block...")
    response = '''<result>
AGENT_TOKEN_EMERGENCY = "[[AGENT_EMERGENCY:"  # Ends with ]]
</result>

Continuing work...'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_EMERGENCY)
    assert not found, "Token in result block should not trigger"
    print("✓ PASSED: Emergency in result block does not trigger")


def test_spawn_in_result_block():
    """Spawn token in <result> block should not trigger."""
    print("\nTesting: Spawn token in <result> block...")
    response = '''<result>
<function_result>
AGENT_TOKEN_SPAWN = "[[AGENT_SPAWN:"  # Ends with ]]
</function_result>
</result>'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_SPAWN)
    assert not found, "Token in result block should not trigger"
    print("✓ PASSED: Spawn in result block does not trigger")


def test_task_complete_in_result_block():
    """Task complete token in <result> block should not trigger."""
    print("\nTesting: Task complete token in <result> block...")
    response = '''Reading MISSION.md:
<result>
AGENT_TOKEN_TASK_COMPLETE = "[[AGENT_TASK_COMPLETE:"  # Ends with ]]
</result>'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_TASK_COMPLETE)
    assert not found, "Token in result block should not trigger"
    print("✓ PASSED: Task complete in result block does not trigger")


def test_token_in_code_block():
    """Token in markdown code block should not trigger."""
    print("\nTesting: Token in markdown code block...")
    response = '''Here's the token definition:
```python
AGENT_TOKEN_BREAK_REQUEST = "[[AGENT_BREAK_REQUEST:"
```

Not a real request.'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_BREAK_REQUEST)
    assert not found, "Token in code block should not trigger"
    print("✓ PASSED: Token in code block does not trigger")


def test_token_in_read_block():
    """Token in [READ ...] block should not trigger."""
    print("\nTesting: Token in [READ ...] block...")
    response = '''[READ axe.py]
AGENT_TOKEN_EMERGENCY = "[[AGENT_EMERGENCY:"  # Ends with ]]

That's just the definition.'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_EMERGENCY)
    assert not found, "Token in READ block should not trigger"
    print("✓ PASSED: Token in READ block does not trigger")


def test_genuine_break_request_triggers():
    """Genuine break request should trigger."""
    print("\nTesting: Genuine break request...")
    response = "I need a break. [[AGENT_BREAK_REQUEST: coffee, need rest]]"
    
    found, content = detect_agent_token(response, AGENT_TOKEN_BREAK_REQUEST)
    assert found, "Genuine break request should trigger"
    assert content == "coffee, need rest", f"Expected 'coffee, need rest', got '{content}'"
    print("✓ PASSED: Genuine break request triggers correctly")


def test_genuine_emergency_triggers():
    """Genuine emergency should trigger."""
    print("\nTesting: Genuine emergency...")
    response = "[[AGENT_EMERGENCY: critical bug detected]]"
    
    found, content = detect_agent_token(response, AGENT_TOKEN_EMERGENCY)
    assert found, "Genuine emergency should trigger"
    assert content == "critical bug detected", f"Expected 'critical bug detected', got '{content}'"
    print("✓ PASSED: Genuine emergency triggers correctly")


def test_genuine_spawn_triggers():
    """Genuine spawn should trigger."""
    print("\nTesting: Genuine spawn request...")
    response = "[[AGENT_SPAWN: claude, need help with testing]]"
    
    found, content = detect_agent_token(response, AGENT_TOKEN_SPAWN)
    assert found, "Genuine spawn should trigger"
    assert "claude" in content, f"Expected 'claude' in content, got '{content}'"
    print("✓ PASSED: Genuine spawn triggers correctly")


def test_genuine_task_complete_triggers():
    """Genuine task complete should trigger."""
    print("\nTesting: Genuine task complete...")
    response = "All done! [[AGENT_TASK_COMPLETE: finished all requirements]]"
    
    found, content = detect_agent_token(response, AGENT_TOKEN_TASK_COMPLETE)
    assert found, "Genuine task complete should trigger"
    assert content == "finished all requirements", f"Expected 'finished all requirements', got '{content}'"
    print("✓ PASSED: Genuine task complete triggers correctly")


def test_nested_result_blocks():
    """Token in nested result blocks should not trigger."""
    print("\nTesting: Nested result blocks...")
    response = '''<result>
<function_result>
<result>
<another>
[[AGENT_BREAK_REQUEST: coffee break]]
</another>
</result>
</function_result>
</result>

Real work continues...'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_BREAK_REQUEST)
    assert not found, "Token in nested result blocks should not trigger"
    print("✓ PASSED: Nested result blocks do not trigger")


def test_mixed_content_and_genuine():
    """File content with token + genuine token outside should trigger."""
    print("\nTesting: Mixed content (file + genuine)...")
    response = '''<result>
AGENT_TOKEN_EMERGENCY = "[[AGENT_EMERGENCY:"
</result>

After analysis, I need to report:
[[AGENT_EMERGENCY: found security issue]]'''
    
    found, content = detect_agent_token(response, AGENT_TOKEN_EMERGENCY)
    assert found, "Genuine token outside result block should trigger"
    assert "security issue" in content, f"Expected 'security issue', got '{content}'"
    print("✓ PASSED: Mixed content correctly detects genuine token")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("DETECT_AGENT_TOKEN TESTS")
    print("=" * 60)
    
    try:
        # Tests that should NOT trigger
        test_break_request_in_result_block()
        test_emergency_in_result_block()
        test_spawn_in_result_block()
        test_task_complete_in_result_block()
        test_token_in_code_block()
        test_token_in_read_block()
        test_nested_result_blocks()
        
        # Tests that SHOULD trigger
        test_genuine_break_request_triggers()
        test_genuine_emergency_triggers()
        test_genuine_spawn_triggers()
        test_genuine_task_complete_triggers()
        
        # Edge cases
        test_mixed_content_and_genuine()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
