#!/usr/bin/env python3
"""
Test suite for models.yaml loading and metadata access.
Validates that model metadata is correctly loaded from the YAML file.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.metadata import (
    MODEL_METADATA, 
    DEFAULT_METADATA, 
    USE_MAX_COMPLETION_TOKENS,
    get_model_info, 
    uses_max_completion_tokens,
    format_token_count,
    format_input_modes,
    format_output_modes
)


def test_yaml_loading():
    """Test that models.yaml is loaded correctly."""
    print("Testing YAML loading...")
    
    # Check that MODEL_METADATA is not empty
    assert len(MODEL_METADATA) > 0, "MODEL_METADATA should not be empty"
    print(f"  ✓ Loaded {len(MODEL_METADATA)} models from models.yaml")
    
    # Check that DEFAULT_METADATA exists
    assert DEFAULT_METADATA is not None, "DEFAULT_METADATA should not be None"
    assert 'context_tokens' in DEFAULT_METADATA, "DEFAULT_METADATA should have context_tokens"
    print(f"  ✓ DEFAULT_METADATA loaded: {DEFAULT_METADATA}")
    
    # Check that USE_MAX_COMPLETION_TOKENS is a set and not empty
    assert isinstance(USE_MAX_COMPLETION_TOKENS, set), "USE_MAX_COMPLETION_TOKENS should be a set"
    assert len(USE_MAX_COMPLETION_TOKENS) > 0, "USE_MAX_COMPLETION_TOKENS should not be empty"
    print(f"  ✓ USE_MAX_COMPLETION_TOKENS loaded with {len(USE_MAX_COMPLETION_TOKENS)} entries")
    print()


def test_known_models():
    """Test that known models return correct metadata."""
    print("Testing known models...")
    
    # Test Claude model
    claude_info = get_model_info('claude-opus-4-5-20251101')
    assert claude_info['context_tokens'] == 200000, "Claude Opus 4.5 should have 200k context"
    assert claude_info['max_output_tokens'] == 65536, "Claude Opus 4.5 should have 64k output"
    assert 'text' in claude_info['input_modes'], "Claude should support text input"
    assert 'image' in claude_info['input_modes'], "Claude should support image input"
    print("  ✓ claude-opus-4-5-20251101 metadata correct")
    
    # Test GPT-5.2 model
    gpt52_info = get_model_info('gpt-5.2')
    assert gpt52_info['context_tokens'] == 400000, "GPT-5.2 should have 400k context"
    assert gpt52_info['max_output_tokens'] == 128000, "GPT-5.2 should have 128k output"
    print("  ✓ gpt-5.2 metadata correct")
    
    # Test GitHub models
    github_gpt4o = get_model_info('openai/gpt-4o')
    assert github_gpt4o['context_tokens'] == 131072, "openai/gpt-4o should have 131k context"
    assert 'audio' in github_gpt4o['input_modes'], "openai/gpt-4o should support audio"
    print("  ✓ openai/gpt-4o metadata correct")
    
    # Test xAI Grok model
    grok_info = get_model_info('grok-4-1-fast-reasoning')
    assert grok_info['context_tokens'] == 2000000, "Grok 4.1 should have 2M context"
    print("  ✓ grok-4-1-fast-reasoning metadata correct")
    
    print()


def test_unknown_model():
    """Test that unknown models return default metadata."""
    print("Testing unknown model...")
    
    unknown_info = get_model_info('unknown-model-xyz')
    assert unknown_info == DEFAULT_METADATA.copy(), "Unknown model should return DEFAULT_METADATA"
    assert unknown_info['context_tokens'] == 8000, "Default context should be 8000"
    assert unknown_info['max_output_tokens'] == 2048, "Default output should be 2048"
    print("  ✓ Unknown model returns default metadata")
    print()


def test_uses_max_completion_tokens():
    """Test the uses_max_completion_tokens function."""
    print("Testing uses_max_completion_tokens...")
    
    # Models that should use max_completion_tokens
    assert uses_max_completion_tokens('gpt-5'), "gpt-5 should use max_completion_tokens"
    assert uses_max_completion_tokens('gpt-5.2'), "gpt-5.2 should use max_completion_tokens"
    assert uses_max_completion_tokens('o1'), "o1 should use max_completion_tokens"
    assert uses_max_completion_tokens('o3-mini'), "o3-mini should use max_completion_tokens"
    assert uses_max_completion_tokens('openai/gpt-5'), "openai/gpt-5 should use max_completion_tokens"
    assert uses_max_completion_tokens('openai/o1-preview'), "openai/o1-preview should use max_completion_tokens"
    print("  ✓ Models requiring max_completion_tokens correctly identified")
    
    # Models that should NOT use max_completion_tokens
    assert not uses_max_completion_tokens('gpt-4o'), "gpt-4o should NOT use max_completion_tokens"
    assert not uses_max_completion_tokens('gpt-4.1'), "gpt-4.1 should NOT use max_completion_tokens"
    assert not uses_max_completion_tokens('claude-opus-4-5-20251101'), "Claude should NOT use max_completion_tokens"
    assert not uses_max_completion_tokens('grok-4-1-fast-reasoning'), "Grok should NOT use max_completion_tokens"
    print("  ✓ Models NOT requiring max_completion_tokens correctly identified")
    print()


def test_formatting_functions():
    """Test the formatting helper functions."""
    print("Testing formatting functions...")
    
    # Test format_token_count
    assert format_token_count(200000) == "200,000", "Token count formatting should add commas"
    assert format_token_count(1048576) == "1,048,576", "Large token count formatting"
    print("  ✓ format_token_count works correctly")
    
    # Test format_input_modes
    assert format_input_modes(['text', 'image']) == "text, image", "Input modes formatting"
    print("  ✓ format_input_modes works correctly")
    
    # Test format_output_modes
    assert format_output_modes(['text', 'function_calling']) == "text, function_calling", "Output modes formatting"
    print("  ✓ format_output_modes works correctly")
    print()


def test_model_count():
    """Test that all expected models are present."""
    print("Testing model count...")
    
    # We should have at least 60+ models
    assert len(MODEL_METADATA) >= 60, f"Expected at least 60 models, got {len(MODEL_METADATA)}"
    print(f"  ✓ {len(MODEL_METADATA)} models loaded (expected 60+)")
    
    # Check some key model families are present
    claude_models = [k for k in MODEL_METADATA.keys() if k.startswith('claude')]
    assert len(claude_models) >= 8, f"Expected at least 8 Claude models, got {len(claude_models)}"
    print(f"  ✓ {len(claude_models)} Claude models present")
    
    openai_models = [k for k in MODEL_METADATA.keys() if k.startswith('openai/')]
    assert len(openai_models) >= 15, f"Expected at least 15 OpenAI models, got {len(openai_models)}"
    print(f"  ✓ {len(openai_models)} OpenAI (via GitHub) models present")
    
    grok_models = [k for k in MODEL_METADATA.keys() if 'grok' in k.lower()]
    assert len(grok_models) >= 6, f"Expected at least 6 Grok models, got {len(grok_models)}"
    print(f"  ✓ {len(grok_models)} Grok models present")
    
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("MODELS.YAML LOADING TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_yaml_loading()
        test_known_models()
        test_unknown_model()
        test_uses_max_completion_tokens()
        test_formatting_functions()
        test_model_count()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
