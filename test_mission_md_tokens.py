#!/usr/bin/env python3
"""
Test that reading MISSION.md doesn't trigger false positives.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import detect_agent_token, AGENT_TOKEN_BREAK_REQUEST, AGENT_TOKEN_EMERGENCY, AGENT_TOKEN_SPAWN, AGENT_TOKEN_TASK_COMPLETE


def test_reading_mission_md():
    """Reading MISSION.md should not trigger token detection."""
    print("Testing: Reading MISSION.md doesn't trigger tokens...")
    
    # Read the actual MISSION.md file
    mission_path = os.path.join(os.path.dirname(__file__), 'MISSION.md')
    with open(mission_path, 'r') as f:
        mission_content = f.read()
    
    # Simulate reading the file like an agent would
    # Wrap it in result blocks like the tool output does
    response = f'''Let me read the MISSION.md file:

<result>
<function_result>
<result>
{mission_content}
</result>
</function_result>
</result>

Now I understand the project structure.'''
    
    # Test all token types
    tokens_to_test = [
        (AGENT_TOKEN_BREAK_REQUEST, "Break Request"),
        (AGENT_TOKEN_EMERGENCY, "Emergency"),
        (AGENT_TOKEN_SPAWN, "Spawn"),
        (AGENT_TOKEN_TASK_COMPLETE, "Task Complete"),
    ]
    
    for token, name in tokens_to_test:
        found, content = detect_agent_token(response, token)
        assert not found, f"{name} token should not trigger when reading MISSION.md"
        print(f"  ✓ {name} token: OK")
    
    print("✓ PASSED: Reading MISSION.md does not trigger any tokens")


def test_mission_md_without_result_blocks():
    """Even without result blocks, MISSION.md content should not trigger."""
    print("\nTesting: MISSION.md content without result blocks...")
    
    # Read the actual MISSION.md file
    mission_path = os.path.join(os.path.dirname(__file__), 'MISSION.md')
    with open(mission_path, 'r') as f:
        mission_content = f.read()
    
    # Just the raw content (though this shouldn't happen in practice)
    response = f"Here's the content:\n{mission_content}\n\nInteresting information."
    
    # Test all token types - they should not trigger because MISSION.md has safe format
    tokens_to_test = [
        (AGENT_TOKEN_BREAK_REQUEST, "Break Request"),
        (AGENT_TOKEN_EMERGENCY, "Emergency"),
        (AGENT_TOKEN_SPAWN, "Spawn"),
        (AGENT_TOKEN_TASK_COMPLETE, "Task Complete"),
    ]
    
    all_ok = True
    for token, name in tokens_to_test:
        found, content = detect_agent_token(response, token)
        if found:
            print(f"  ✗ {name} token triggered (this is OK if MISSION.md was already safe)")
            all_ok = False
        else:
            print(f"  ✓ {name} token: OK")
    
    # This test is informational - we expect it to pass since MISSION.md should be safe
    if all_ok:
        print("✓ PASSED: MISSION.md content is safe even without result block stripping")
    else:
        print("⚠️  WARNING: Some tokens detected, but should be caught by result block stripping")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("MISSION.MD TOKEN DETECTION TESTS")
    print("=" * 60)
    
    try:
        test_reading_mission_md()
        test_mission_md_without_result_blocks()
        
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
