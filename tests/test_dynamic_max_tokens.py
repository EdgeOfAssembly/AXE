#!/usr/bin/env python3
"""
Test suite for dynamic max_output_tokens implementation.
Validates that models use their actual max output token limits from metadata.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.metadata import get_max_output_tokens, get_model_info


def test_get_max_output_tokens_helper():
    """Test the new get_max_output_tokens helper function."""
    print("Testing get_max_output_tokens helper...")
    
    # Test Claude Opus 4.5 - should return 64000
    assert get_max_output_tokens('claude-opus-4-5-20251101') == 64000, \
        "Claude Opus 4.5 should return 64000 tokens"
    print("  ✓ Claude Opus 4.5: 64,000 tokens")
    
    # Test GPT-4o - should return 16000
    assert get_max_output_tokens('gpt-4o') == 16000, \
        "GPT-4o should return 16000 tokens"
    print("  ✓ GPT-4o: 16,000 tokens")
    
    # Test GPT-5.2 - should return 128000
    assert get_max_output_tokens('gpt-5.2') == 128000, \
        "GPT-5.2 should return 128000 tokens"
    print("  ✓ GPT-5.2: 128,000 tokens")
    
    # Test unknown model - should return DEFAULT_METADATA's max_output_tokens (4000)
    # Note: The default parameter is only used when 'max_output_tokens' key is missing
    # from the model metadata dict. Unknown models return DEFAULT_METADATA which 
    # contains the key, so the default parameter doesn't apply in that case.
    assert get_max_output_tokens('unknown-model-xyz') == 4000, \
        "Unknown model should return DEFAULT_METADATA's 4000"
    print("  ✓ Unknown model: 4,000 tokens (from DEFAULT_METADATA)")
    
    # Test with different default parameter - doesn't affect result since 
    # unknown models get DEFAULT_METADATA which has max_output_tokens
    result = get_max_output_tokens('unknown-model', default=8192)
    assert result == 4000, \
        "Unknown model still returns DEFAULT_METADATA's 4000 (default param only used if key missing)"
    print("  ✓ Unknown model with default=8192: 4,000 tokens (DEFAULT_METADATA takes precedence)")
    
    print()


def test_various_model_limits():
    """Test that different models have correct max output limits."""
    print("Testing various model token limits...")
    
    test_cases = [
        ('claude-haiku-4-5-20251001', 8000, "Claude Haiku 4.5"),
        ('claude-sonnet-4-5-20250929', 64000, "Claude Sonnet 4.5"),
        ('gpt-4.1', 64000, "GPT-4.1"),
        ('gpt-4.1-mini', 32000, "GPT-4.1 Mini"),
        ('gpt-4o-mini', 16000, "GPT-4o Mini"),
        ('o3', 100000, "o3"),
        ('o4-mini', 100000, "o4-mini"),
        ('openai/gpt-4o', 16000, "GitHub OpenAI GPT-4o"),
        ('openai/gpt-4o-mini', 4000, "GitHub OpenAI GPT-4o Mini"),
        ('openai/gpt-5', 100000, "GitHub OpenAI GPT-5"),
        ('grok-4-1-fast-reasoning', 32000, "Grok 4.1 Fast Reasoning"),
        ('grok-code-fast-1', 16000, "Grok Code Fast"),
        ('meta/llama-3.2-11b-vision-instruct', 4000, "Llama 3.2 11B Vision"),
        ('deepseek-ai/DeepSeek-V3.2', 4000, "DeepSeek V3.2"),
    ]
    
    for model, expected_tokens, display_name in test_cases:
        actual = get_max_output_tokens(model)
        assert actual == expected_tokens, \
            f"{display_name} should have {expected_tokens} tokens, got {actual}"
        print(f"  ✓ {display_name}: {actual:,} tokens")
    
    print()


def test_no_hardcoded_32768():
    """Ensure we're not using hardcoded 32768 in the code."""
    print("Checking for hardcoded max_tokens values...")
    
    # Get the repository root (parent of tests directory)
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    
    files_to_check = [
        os.path.join(repo_root, 'core', 'agent_manager.py'),
        os.path.join(repo_root, 'axe.py')
    ]
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            print(f"  ⚠ File not found: {filepath}")
            continue
            
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for hardcoded max_tokens=32768
        if 'max_tokens=32768' in content:
            raise AssertionError(f"Found hardcoded max_tokens=32768 in {filepath}")
        
        # Check for hardcoded max_completion_tokens=32768
        if 'max_completion_tokens=32768' in content:
            raise AssertionError(f"Found hardcoded max_completion_tokens=32768 in {filepath}")
        
        print(f"  ✓ No hardcoded token limits in {os.path.basename(filepath)}")
    
    print()


def test_dynamic_lookup_presence():
    """Verify that dynamic lookup code is present."""
    print("Verifying dynamic token lookup implementation...")
    
    # Get the repository root (parent of tests directory)
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    
    # Check agent_manager.py
    agent_manager_path = os.path.join(repo_root, 'core', 'agent_manager.py')
    with open(agent_manager_path, 'r') as f:
        agent_manager_content = f.read()
    
    # Should import get_max_output_tokens
    assert 'get_max_output_tokens' in agent_manager_content, \
        "agent_manager.py should import get_max_output_tokens"
    print("  ✓ agent_manager.py imports get_max_output_tokens")
    
    # Should use max_output variable
    assert 'max_output' in agent_manager_content, \
        "agent_manager.py should use max_output variable"
    print("  ✓ agent_manager.py uses max_output variable")
    
    # Should use streaming for Anthropic
    assert 'client.messages.stream' in agent_manager_content, \
        "agent_manager.py should use streaming for Anthropic"
    print("  ✓ agent_manager.py uses streaming for Anthropic")
    
    # Check axe.py
    axe_path = os.path.join(repo_root, 'axe.py')
    with open(axe_path, 'r') as f:
        axe_content = f.read()
    
    # Should import get_max_output_tokens
    assert 'get_max_output_tokens' in axe_content, \
        "axe.py should import get_max_output_tokens"
    print("  ✓ axe.py imports get_max_output_tokens")
    
    # Should use max_output variable
    assert 'max_output' in axe_content, \
        "axe.py should use max_output variable"
    print("  ✓ axe.py uses max_output variable")
    
    # Should use streaming for Anthropic
    assert 'client.messages.stream' in axe_content, \
        "axe.py should use streaming for Anthropic"
    print("  ✓ axe.py uses streaming for Anthropic")
    
    print()


def test_safe_default_fallback():
    """Test that unknown models fallback to safe default."""
    print("Testing safe default fallback...")
    
    # Test various unknown model names
    unknown_models = [
        'future-model-2027',
        'gpt-42',
        'claude-ultra-5',
        'random-llm',
    ]
    
    for model in unknown_models:
        max_tokens = get_max_output_tokens(model)
        assert max_tokens == 4000, \
            f"Unknown model '{model}' should default to 4000, got {max_tokens}"
    
    print(f"  ✓ All unknown models default to 4,000 tokens")
    print()


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("Testing edge cases...")
    
    # Empty string model name
    assert get_max_output_tokens('') == 4000, \
        "Empty model name should return default"
    print("  ✓ Empty model name returns default")
    
    # Model with special characters (shouldn't exist, but shouldn't crash)
    assert get_max_output_tokens('model-with-@#$%') == 4000, \
        "Model with special chars should return default"
    print("  ✓ Model with special characters returns default")
    
    # Very long model name
    long_name = 'x' * 1000
    assert get_max_output_tokens(long_name) == 4000, \
        "Very long model name should return default"
    print("  ✓ Very long model name returns default")
    
    print()


def test_metadata_consistency():
    """Ensure get_max_output_tokens is consistent with get_model_info."""
    print("Testing consistency with get_model_info...")
    
    test_models = [
        'claude-opus-4-5-20251101',
        'gpt-5.2',
        'gpt-4o',
        'openai/gpt-5',
        'grok-4-1-fast-reasoning',
    ]
    
    for model in test_models:
        # Get via helper function
        via_helper = get_max_output_tokens(model)
        
        # Get via get_model_info
        model_info = get_model_info(model)
        via_direct = model_info.get('max_output_tokens', 4000)
        
        assert via_helper == via_direct, \
            f"Inconsistent results for {model}: helper={via_helper}, direct={via_direct}"
    
    print(f"  ✓ Helper function consistent with get_model_info for all {len(test_models)} models")
    print()


if __name__ == '__main__':
    print("=" * 70)
    print("DYNAMIC MAX_OUTPUT_TOKENS TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        test_get_max_output_tokens_helper()
        test_various_model_limits()
        test_no_hardcoded_32768()
        test_dynamic_lookup_presence()
        test_safe_default_fallback()
        test_edge_cases()
        test_metadata_consistency()
        
        print("=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
