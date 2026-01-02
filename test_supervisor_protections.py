#!/usr/bin/env python3
"""
Test script to verify supervisor protections.
Ensures supervisor cannot take breaks or sleep during active sessions.
"""
import os
import sys
from unittest.mock import MagicMock, Mock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_supervisor_cannot_request_break():
    """Supervisor should not be able to request breaks."""
    print("Testing: Supervisor cannot request break...")
    
    # Create a mock session object
    session = MagicMock()
    session.supervisor_alias = "@boss"
    session.supervisor_name = "claude"
    session.agent_aliases = {"claude": "@boss", "gpt": "@dev"}
    session.agent_ids = {"claude": "id-boss", "gpt": "id-dev"}
    
    # Mock break system
    session.break_system = MagicMock()
    break_request_called = []
    def track_break_request(agent_id, alias, break_type, reason):
        break_request_called.append((agent_id, alias))
        return {'id': 'test-break-123'}
    session.break_system.request_break = track_break_request
    
    # Import the actual method and bind it to our mock
    from axe import CollaborativeSession
    method = CollaborativeSession._handle_break_request
    
    # Test: Supervisor tries to request a break
    method(session, "claude", "I need a break", "coffee, tired")
    
    # Verify break was NOT requested (supervisor blocked)
    assert len(break_request_called) == 0, "Supervisor should not be able to request breaks"
    print("✓ PASSED: Supervisor break request was blocked")


def test_non_supervisor_can_request_break():
    """Non-supervisor agents should be able to request breaks."""
    print("\nTesting: Non-supervisor can request break...")
    
    # Create a mock session object
    session = MagicMock()
    session.supervisor_alias = "@boss"
    session.supervisor_name = "claude"
    session.agent_aliases = {"claude": "@boss", "gpt": "@dev"}
    session.agent_ids = {"claude": "id-boss", "gpt": "id-dev"}
    
    # Mock break system
    session.break_system = MagicMock()
    break_request_called = []
    def track_break_request(agent_id, alias, break_type, reason):
        break_request_called.append((agent_id, alias))
        return {'id': 'test-break-123'}
    session.break_system.request_break = track_break_request
    
    # Import the actual method and bind it to our mock
    from axe import CollaborativeSession
    method = CollaborativeSession._handle_break_request
    
    # Test: Non-supervisor agent requests a break
    method(session, "gpt", "I need a break", "coffee, tired")
    
    # Verify break was requested
    assert len(break_request_called) == 1, "Non-supervisor should be able to request breaks"
    assert break_request_called[0] == ("id-dev", "@dev"), "Correct agent should make break request"
    print("✓ PASSED: Non-supervisor break request was allowed")


def test_supervisor_with_boss_alias_blocked():
    """Supervisor with @boss alias should also be blocked from breaks."""
    print("\nTesting: @boss alias is blocked from breaks...")
    
    # Create a mock session object
    session = MagicMock()
    session.supervisor_alias = "@boss"
    session.supervisor_name = "claude"
    session.agent_aliases = {"claude": "@boss", "gpt": "@dev"}
    session.agent_ids = {"claude": "id-boss", "gpt": "id-dev"}
    
    # Mock break system
    session.break_system = MagicMock()
    break_request_called = []
    def track_break_request(agent_id, alias, break_type, reason):
        break_request_called.append((agent_id, alias))
        return {'id': 'test-break-123'}
    session.break_system.request_break = track_break_request
    
    # Import the actual method and bind it to our mock
    from axe import CollaborativeSession
    method = CollaborativeSession._handle_break_request
    
    # Test: Try break request (alias should be checked)
    method(session, "claude", "Need break", "tired")
    
    # Verify break was NOT requested
    assert len(break_request_called) == 0, "@boss alias should be blocked from breaks"
    print("✓ PASSED: @boss alias was blocked from breaks")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("SUPERVISOR PROTECTION TESTS")
    print("=" * 60)
    
    try:
        test_supervisor_cannot_request_break()
        test_non_supervisor_can_request_break()
        test_supervisor_with_boss_alias_blocked()
        
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
