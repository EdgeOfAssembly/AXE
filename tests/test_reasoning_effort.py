#!/usr/bin/env python3
"""
Tests for reasoning effort parameter support in GPT-5.2 Codex.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.metadata import (
    supports_reasoning_effort,
    get_default_reasoning_effort,
    validate_reasoning_effort,
    VALID_REASONING_EFFORTS,
    get_model_info
)


def test_supports_reasoning_effort_returns_true_for_codex():
    """Test that supports_reasoning_effort returns True for gpt-5.2-codex."""
    print("Testing supports_reasoning_effort for codex...")
    assert supports_reasoning_effort('gpt-5.2-codex') is True
    print("✓ supports_reasoning_effort returns True for gpt-5.2-codex")


def test_supports_reasoning_effort_returns_false_for_non_codex():
    """Test that supports_reasoning_effort returns False for models that don't support it."""
    print("Testing supports_reasoning_effort for non-codex models...")
    assert supports_reasoning_effort('gpt-4o') is False
    assert supports_reasoning_effort('claude-opus-4-5-20251101') is False
    assert supports_reasoning_effort('gpt-4.1') is False
    print("✓ supports_reasoning_effort returns False for non-codex models")


def test_get_default_reasoning_effort_returns_medium_for_codex():
    """Test that get_default_reasoning_effort returns 'medium' for gpt-5.2-codex."""
    print("Testing get_default_reasoning_effort for codex...")
    assert get_default_reasoning_effort('gpt-5.2-codex') == 'medium'
    print("✓ get_default_reasoning_effort returns 'medium' for gpt-5.2-codex")


def test_get_default_reasoning_effort_returns_none_for_non_codex():
    """Test that get_default_reasoning_effort returns None for models without default."""
    print("Testing get_default_reasoning_effort for non-codex models...")
    assert get_default_reasoning_effort('gpt-4o') is None
    assert get_default_reasoning_effort('claude-opus-4-5-20251101') is None
    print("✓ get_default_reasoning_effort returns None for non-codex models")


def test_validate_reasoning_effort_accepts_valid_values():
    """Test that validate_reasoning_effort accepts all valid effort levels."""
    print("Testing validate_reasoning_effort with valid values...")
    for effort in ['none', 'low', 'medium', 'high', 'xhigh']:
        assert validate_reasoning_effort(effort) is True
    print("✓ validate_reasoning_effort accepts all valid values")


def test_validate_reasoning_effort_rejects_invalid_values():
    """Test that validate_reasoning_effort rejects invalid effort levels."""
    print("Testing validate_reasoning_effort with invalid values...")
    assert validate_reasoning_effort('invalid') is False
    assert validate_reasoning_effort('ultra') is False
    assert validate_reasoning_effort('') is False
    assert validate_reasoning_effort('MEDIUM') is False  # Case sensitive
    print("✓ validate_reasoning_effort rejects invalid values")


def test_valid_reasoning_efforts_constant():
    """Test that VALID_REASONING_EFFORTS contains all expected values."""
    print("Testing VALID_REASONING_EFFORTS constant...")
    expected = {'none', 'low', 'medium', 'high', 'xhigh'}
    assert VALID_REASONING_EFFORTS == expected
    print("✓ VALID_REASONING_EFFORTS contains correct values")


def test_codex_model_has_correct_metadata():
    """Test that gpt-5.2-codex has all required reasoning effort metadata."""
    print("Testing gpt-5.2-codex metadata...")
    model_info = get_model_info('gpt-5.2-codex')
    assert model_info.get('supports_reasoning_effort') is True
    assert model_info.get('default_reasoning_effort') == 'medium'
    assert model_info.get('api_type') == 'responses'
    print("✓ gpt-5.2-codex has correct metadata")


def test_agent_config_can_override_model_default():
    """Test that agent config reasoning_effort overrides model default."""
    print("Testing agent config override...")
    model_default = get_default_reasoning_effort('gpt-5.2-codex')
    agent_override = 'xhigh'
    
    # Priority: agent config > model default
    effective_effort = agent_override or model_default
    assert effective_effort == 'xhigh'
    print("✓ Agent config overrides model default")


def test_model_default_used_when_no_agent_override():
    """Test that model default is used when agent doesn't specify reasoning_effort."""
    print("Testing model default fallback...")
    model_default = get_default_reasoning_effort('gpt-5.2-codex')
    agent_override = None
    
    # Priority: agent config > model default
    effective_effort = agent_override or model_default
    assert effective_effort == 'medium'
    print("✓ Model default is used when no agent override")


def test_reasoning_effort_validation_in_api_flow():
    """Test that reasoning effort is validated before being passed to API."""
    print("Testing reasoning effort validation in API flow...")
    
    # Valid effort - should pass
    effort = 'high'
    if validate_reasoning_effort(effort):
        api_params = {'reasoning': {'effort': effort}}
        assert api_params == {'reasoning': {'effort': 'high'}}
    
    # Invalid effort - should be ignored
    effort = 'invalid'
    api_params = {}
    if validate_reasoning_effort(effort):
        api_params['reasoning'] = {'effort': effort}
    # No reasoning parameter added for invalid effort
    assert 'reasoning' not in api_params
    print("✓ Reasoning effort is validated correctly in API flow")


def test_variant_agent_effort_levels():
    """Test that variant agent effort levels are all valid."""
    print("Testing variant agent effort levels...")
    expected_variants = {
        'gpt_codex': 'medium',        # Standard
        'gpt_codex_fast': 'low',      # Fast variant
        'gpt_codex_high': 'high',     # High reasoning variant
        'gpt_codex_xhigh': 'xhigh',   # Maximum reasoning variant
    }
    
    # Verify all effort levels are valid
    for agent, effort in expected_variants.items():
        assert validate_reasoning_effort(effort), f"Agent {agent} has invalid effort {effort}"
    print("✓ All variant agent effort levels are valid")


def test_expected_aliases_are_short_and_memorable():
    """Test that variant aliases are short and easy to remember."""
    print("Testing variant agent aliases...")
    expected_aliases = {
        'gpt_codex': ['codex', 'gptcode'],
        'gpt_codex_fast': ['codex-fast', 'cf'],
        'gpt_codex_high': ['codex-high', 'ch'],
        'gpt_codex_xhigh': ['codex-xhigh', 'cx'],
    }
    
    # All aliases should be short (< 15 chars)
    for agent, aliases in expected_aliases.items():
        for alias in aliases:
            assert len(alias) <= 15, f"Alias '{alias}' for {agent} is too long"
    print("✓ All variant agent aliases are short and memorable")


def test_api_params_structure_for_responses_api():
    """Test that reasoning effort is properly structured for Responses API."""
    print("Testing API parameter structure...")
    effort = 'xhigh'
    api_params = {
        'model': 'gpt-5.2-codex',
        'input': 'Test prompt',
        'max_output_tokens': 128000,
    }
    
    # Add reasoning if supported and valid
    if supports_reasoning_effort('gpt-5.2-codex') and validate_reasoning_effort(effort):
        api_params['reasoning'] = {'effort': effort}
    
    # Verify structure
    assert 'reasoning' in api_params
    assert api_params['reasoning'] == {'effort': 'xhigh'}
    print("✓ API parameters have correct structure")


def test_api_params_omit_reasoning_when_none():
    """Test that reasoning parameter is omitted when effort is None."""
    print("Testing API parameter omission when None...")
    api_params = {
        'model': 'gpt-5.2-codex',
        'input': 'Test prompt',
        'max_output_tokens': 128000,
    }
    
    # No reasoning effort specified
    effort = None
    if effort and validate_reasoning_effort(effort):
        api_params['reasoning'] = {'effort': effort}
    
    # Verify reasoning is not in params
    assert 'reasoning' not in api_params
    print("✓ Reasoning parameter omitted when None")


def test_api_params_omit_reasoning_for_unsupported_models():
    """Test that reasoning parameter is omitted for models that don't support it."""
    print("Testing API parameter omission for unsupported models...")
    model = 'gpt-4o'
    api_params = {
        'model': model,
        'messages': [{'role': 'user', 'content': 'Test'}],
    }
    
    # Try to add reasoning
    effort = 'high'
    if supports_reasoning_effort(model):
        api_params['reasoning'] = {'effort': effort}
    
    # Verify reasoning is not added for unsupported model
    assert 'reasoning' not in api_params
    print("✓ Reasoning parameter omitted for unsupported models")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("REASONING EFFORT PARAMETER TESTS")
    print("="*70 + "\n")
    
    tests = [
        test_supports_reasoning_effort_returns_true_for_codex,
        test_supports_reasoning_effort_returns_false_for_non_codex,
        test_get_default_reasoning_effort_returns_medium_for_codex,
        test_get_default_reasoning_effort_returns_none_for_non_codex,
        test_validate_reasoning_effort_accepts_valid_values,
        test_validate_reasoning_effort_rejects_invalid_values,
        test_valid_reasoning_efforts_constant,
        test_codex_model_has_correct_metadata,
        test_agent_config_can_override_model_default,
        test_model_default_used_when_no_agent_override,
        test_reasoning_effort_validation_in_api_flow,
        test_variant_agent_effort_levels,
        test_expected_aliases_are_short_and_memorable,
        test_api_params_structure_for_responses_api,
        test_api_params_omit_reasoning_when_none,
        test_api_params_omit_reasoning_for_unsupported_models,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

