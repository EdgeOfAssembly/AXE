#!/usr/bin/env python3
"""
Test suite for ACP (Agent Communication Protocol) benchmark.

This is a gatekeeper test that ensures ACP provides sufficient token savings
before implementation. The test FAILS if savings < 50%.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.benchmark_acp import (
    create_verbose_message,
    create_compact_message,
    estimate_tokens,
    benchmark_message_formats,
    run_benchmark,
)
from core.acp_validator import ACPValidator


def test_validator_basic():
    """Test ACPValidator basic functionality."""
    print("\n" + "="*60)
    print("Testing ACP Validator")
    print("="*60)
    
    with ACPValidator() as validator:
        # Test standard abbreviation detection
        assert validator.conflicts_with_standard("BOF"), "Should detect BOF as standard"
        assert validator.conflicts_with_standard("XSS"), "Should detect XSS as standard"
        assert validator.conflicts_with_standard("TCP"), "Should detect TCP as standard"
        
        # Test case-insensitive detection
        assert validator.conflicts_with_standard("bof"), "Should be case-insensitive"
        assert validator.conflicts_with_standard("Bof"), "Should be case-insensitive"
        
        # Test non-standard abbreviations
        assert not validator.conflicts_with_standard("ANA"), "ANA should not conflict"
        assert not validator.conflicts_with_standard("FIX"), "FIX should not conflict"
        assert not validator.conflicts_with_standard("TST"), "TST should not conflict"
        
        # Test getting standard meanings
        meaning = validator.get_standard_meaning("BOF")
        assert meaning == "Buffer Overflow", f"Expected 'Buffer Overflow', got '{meaning}'"
        
        meaning = validator.get_standard_meaning("XSS")
        assert meaning == "Cross-Site Scripting", f"Expected 'Cross-Site Scripting', got '{meaning}'"
        
        # Test validation of custom abbreviations
        custom = {
            "ANA": "Analyze",
            "FIX": "Fix",
            "TST": "Test",
            "BOF": "Buffer Overflow",  # This should conflict
        }
        
        conflicts = validator.validate_custom_abbreviations(custom)
        assert len(conflicts) == 1, f"Expected 1 conflict, got {len(conflicts)}"
        assert "BOF" in conflicts[0], f"Expected BOF in conflicts: {conflicts}"
        
        print("  ✓ All validator tests passed")
    
    print()


def test_message_format_comparison():
    """Test verbose vs compact message formats."""
    print("\n" + "="*60)
    print("Testing Message Format Comparison")
    print("="*60)
    
    # Test single message
    verbose = create_verbose_message(
        "Claude", "Analyze", "parser.c:247", 
        "found buffer overflow in memcpy", "fix and test"
    )
    compact = create_compact_message(
        "C", "ANA", "parser.c:247", 
        "BOF: memcpy", "FIX+TST"
    )
    
    v_tokens = estimate_tokens(verbose)
    c_tokens = estimate_tokens(compact)
    
    print(f"\nSingle message comparison:")
    print(f"  Verbose ({v_tokens} tokens): {verbose}")
    print(f"  Compact ({c_tokens} tokens): {compact}")
    
    assert c_tokens < v_tokens, "Compact should use fewer tokens"
    savings = ((v_tokens - c_tokens) / v_tokens * 100)
    print(f"  Savings: {savings:.1f}%")
    
    # Should save at least 40% per message
    assert savings >= 40, f"Expected >= 40% savings per message, got {savings:.1f}%"
    
    print("  ✓ Message format test passed")
    print()


def test_realistic_multi_agent_session():
    """Test realistic multi-agent collaboration session."""
    print("\n" + "="*60)
    print("Testing Realistic Multi-Agent Session")
    print("="*60)
    
    # Simulate a realistic security audit session
    session_messages = [
        {
            "agent": "Claude",
            "agent_abbrev": "C",
            "action": "Analyze",
            "action_abbrev": "ANA",
            "target": "main.c:156",
            "details": "buffer overflow vulnerability in string copy",
            "details_compact": "BOF: strcpy",
            "next_action": "fix",
            "next_action_abbrev": "FIX",
        },
        {
            "agent": "GPT",
            "agent_abbrev": "G",
            "action": "Review",
            "action_abbrev": "REV",
            "target": "auth.py:89",
            "details": "cross-site scripting in user input validation",
            "details_compact": "XSS: validation",
            "next_action": "refactor",
            "next_action_abbrev": "REF",
        },
        {
            "agent": "Llama",
            "agent_abbrev": "L",
            "action": "Fix",
            "action_abbrev": "FIX",
            "target": "db.cpp:234",
            "details": "SQL injection in query builder",
            "details_compact": "SQLI: query",
            "next_action": "test",
            "next_action_abbrev": "TST",
        },
        {
            "agent": "Grok",
            "agent_abbrev": "X",
            "action": "Test",
            "action_abbrev": "TST",
            "target": "tests/",
            "details": "test-driven development for security fixes",
            "details_compact": "TDD: security",
            "next_action": "verify",
            "next_action_abbrev": "VFY",
        },
        {
            "agent": "Claude",
            "agent_abbrev": "C",
            "action": "Verify",
            "action_abbrev": "VFY",
            "target": "0x401000",
            "details": "address space layout randomization enabled",
            "details_compact": "ASLR: OK",
            "next_action": "document",
            "next_action_abbrev": "DOC",
        },
    ]
    
    verbose_total = 0
    compact_total = 0
    
    for msg in session_messages:
        verbose = create_verbose_message(
            msg["agent"],
            msg["action"],
            msg["target"],
            msg["details"],
            msg["next_action"]
        )
        
        compact = create_compact_message(
            msg["agent_abbrev"],
            msg["action_abbrev"],
            msg["target"],
            msg["details_compact"],
            msg["next_action_abbrev"]
        )
        
        verbose_total += estimate_tokens(verbose)
        compact_total += estimate_tokens(compact)
    
    savings = ((verbose_total - compact_total) / verbose_total * 100)
    
    print(f"\nSession simulation:")
    print(f"  Messages: {len(session_messages)}")
    print(f"  Verbose tokens: {verbose_total}")
    print(f"  Compact tokens: {compact_total}")
    print(f"  Savings: {savings:.1f}%")
    
    # Session should save at least 50%
    assert savings >= 50, f"Expected >= 50% savings for session, got {savings:.1f}%"
    
    print("  ✓ Multi-agent session test passed")
    print()


def test_benchmark_gatekeeper():
    """
    GATEKEEPER TEST: Verify ACP provides sufficient token savings.
    
    This test FAILS if savings < 50%, blocking implementation of
    an ineffective optimization.
    """
    print("\n" + "="*60)
    print("GATEKEEPER TEST: ACP TOKEN SAVINGS THRESHOLD")
    print("="*60)
    
    # Run full benchmark
    results = run_benchmark()
    
    # Extract results
    savings_percent = results["savings_percent"]
    threshold = results["threshold"]
    recommendation = results["recommendation"]
    
    print(f"\n{'='*60}")
    print(f"GATEKEEPER RESULT")
    print(f"{'='*60}")
    print(f"Savings: {savings_percent:.1f}%")
    print(f"Threshold: {threshold}%")
    print(f"Recommendation: {recommendation}")
    
    # CRITICAL: Test fails if savings below threshold
    if savings_percent < threshold:
        print(f"\n✗ GATEKEEPER TEST FAILED")
        print(f"  Savings of {savings_percent:.1f}% is below {threshold}% threshold")
        print(f"  ACP does not provide sufficient benefit to implement")
        print(f"{'='*60}\n")
        assert False, f"ACP savings {savings_percent:.1f}% below threshold {threshold}%"
    else:
        print(f"\n✓ GATEKEEPER TEST PASSED")
        print(f"  Savings of {savings_percent:.1f}% exceeds {threshold}% threshold")
        print(f"  ACP provides sufficient benefit to implement")
        print(f"{'='*60}\n")


def run_all_tests():
    """Run all ACP benchmark tests."""
    print("\n" + "="*60)
    print("ACP BENCHMARK TEST SUITE")
    print("="*60)
    
    try:
        test_validator_basic()
        test_message_format_comparison()
        test_realistic_multi_agent_session()
        test_benchmark_gatekeeper()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        print()
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
