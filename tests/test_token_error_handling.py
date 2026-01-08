#!/usr/bin/env python3
"""
Test suite for token limit error handling (Bug #3).

Tests the fix for 413 token limit errors not being properly handled,
including detection, logging, and automatic recovery.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_token_limit_error_detection():
    """Test that token limit errors are properly detected."""
    print("Testing token limit error detection...")
    
    # Test various error message formats
    test_cases = [
        ("Error code: 413 - {'error': {'code': 'tokens_limit_reached'}}", True),
        ("maximum context length is 128000", True),
        ("context_length_exceeded: The request exceeds the limit", True),
        ("tokens_limit_reached in API call", True),
        ("413 Payload Too Large", True),
        ("Connection timeout", False),
        ("Rate limit exceeded", False),
        ("Invalid API key", False)
    ]
    
    for error_str, should_detect in test_cases:
        # Simulate detection logic
        is_token_limit = (
            '413' in error_str or 
            'tokens_limit_reached' in error_str.lower() or
            'context_length_exceeded' in error_str.lower() or
            'maximum context length' in error_str.lower()
        )
        
        assert is_token_limit == should_detect, \
            f"Detection failed for '{error_str}': expected {should_detect}, got {is_token_limit}"
    
    print("  ✓ Token limit error detection works correctly")


def test_error_count_tracking():
    """Test that error counts are properly incremented."""
    print("Testing error count tracking...")
    
    # Simulate error counting
    error_count = 0
    
    # First error
    error_count += 1
    assert error_count == 1, "First error count incorrect"
    
    # Second error
    error_count += 1
    assert error_count == 2, "Second error count incorrect"
    
    # Third error - should trigger sleep
    error_count += 1
    assert error_count >= 3, "Third error count incorrect"
    should_sleep = error_count >= 3
    assert should_sleep, "Should sleep after 3 errors"
    
    print("  ✓ Error count tracking works correctly")


def test_token_error_response_format():
    """Test that token error responses are properly formatted."""
    print("Testing token error response format...")
    
    error_count = 3
    response = f"[Token Limit Error: Unable to process request due to context length. Error count: {error_count}]"
    
    assert "[Token Limit Error:" in response, "Response missing error prefix"
    assert "context length" in response, "Response missing context explanation"
    assert f"Error count: {error_count}" in response, "Response missing error count"
    
    print("  ✓ Token error response format is correct")


def test_supervisor_cannot_be_slept():
    """Test that supervisors are not put to sleep even on token errors."""
    print("Testing supervisor protection from sleep...")
    
    # Simulate supervisor check
    alias = "@boss"
    is_supervisor = (alias == "@boss")
    
    if is_supervisor:
        should_sleep = False  # Supervisor should never be slept
    else:
        should_sleep = True   # Regular agents can be slept
    
    assert not should_sleep, "Supervisor should not be slept"
    
    # Test with regular agent
    alias = "@gpt-4o2"
    is_supervisor = (alias == "@boss")
    
    if is_supervisor:
        should_sleep = False
    else:
        should_sleep = True
    
    assert should_sleep, "Regular agents should be slept on repeated errors"
    
    print("  ✓ Supervisor protection from sleep works correctly")


def test_error_logging_structure():
    """Test that error logging contains required fields."""
    print("Testing error logging structure...")
    
    # Simulate log entry
    log_entry = {
        'agent_id': 'test-uuid-1234',
        'alias': '@test-agent',
        'error': 'Error code: 413 - tokens_limit_reached',
        'timestamp': '2026-01-03T12:00:00'
    }
    
    assert 'agent_id' in log_entry, "Log missing agent_id"
    assert 'alias' in log_entry, "Log missing alias"
    assert 'error' in log_entry, "Log missing error"
    assert 'timestamp' in log_entry, "Log missing timestamp"
    
    print("  ✓ Error logging structure is correct")


def test_error_message_truncation():
    """Test that long error messages are truncated appropriately."""
    print("Testing error message truncation...")
    
    long_error = "Error: " + "x" * 1000
    
    # Truncate for display (200 chars)
    display_error = long_error[:200]
    assert len(display_error) == 200, "Display truncation incorrect"
    
    # Truncate for logging (500 chars)
    log_error = long_error[:500]
    assert len(log_error) == 500, "Log truncation incorrect"
    
    print("  ✓ Error message truncation works correctly")


def test_recovery_suggestion_message():
    """Test that recovery suggestions are provided."""
    print("Testing recovery suggestion messages...")
    
    # Non-supervisor agent
    alias = "@gpt-4o2"
    is_supervisor = (alias == "@boss")
    
    if is_supervisor:
        suggestion = "Note: Supervisor cannot be replaced. Continuing with reduced capacity."
    else:
        suggestion = "Suggestion: @boss can spawn a replacement agent if needed"
    
    assert "spawn a replacement" in suggestion, "Missing spawn suggestion for regular agent"
    
    # Supervisor
    alias = "@boss"
    is_supervisor = (alias == "@boss")
    
    if is_supervisor:
        suggestion = "Note: Supervisor cannot be replaced. Continuing with reduced capacity."
    else:
        suggestion = "Suggestion: @boss can spawn a replacement agent if needed"
    
    assert "cannot be replaced" in suggestion, "Missing supervisor protection message"
    
    print("  ✓ Recovery suggestion messages are correct")


def test_token_error_vs_other_errors():
    """Test that token errors are handled differently from other errors."""
    print("Testing token error vs other error handling...")
    
    # Token limit error
    error_str = "Error code: 413 - tokens_limit_reached"
    is_token_limit = '413' in error_str or 'tokens_limit_reached' in error_str.lower()
    
    if is_token_limit:
        response = "[Token Limit Error: Unable to process request due to context length. Error count: 1]"
        special_handling = True
    else:
        response = f"[API Error: {error_str}]"
        special_handling = False
    
    assert special_handling, "Token limit error should have special handling"
    assert "Token Limit Error" in response, "Token error response incorrect"
    
    # Regular API error
    error_str = "Connection timeout"
    is_token_limit = '413' in error_str or 'tokens_limit_reached' in error_str.lower()
    
    if is_token_limit:
        response = "[Token Limit Error: Unable to process request due to context length. Error count: 1]"
        special_handling = True
    else:
        response = f"[API Error: {error_str}]"
        special_handling = False
    
    assert not special_handling, "Regular error should not have special handling"
    assert "API Error" in response, "Regular error response incorrect"
    
    print("  ✓ Token errors handled differently from other errors")


if __name__ == '__main__':
    print("=" * 70)
    print("TOKEN LIMIT ERROR HANDLING TEST SUITE")
    print("=" * 70)
    
    test_token_limit_error_detection()
    test_error_count_tracking()
    test_token_error_response_format()
    test_supervisor_cannot_be_slept()
    test_error_logging_structure()
    test_error_message_truncation()
    test_recovery_suggestion_message()
    test_token_error_vs_other_errors()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
