#!/usr/bin/env python3
"""
Test suite for Anthropic-specific features.
Tests prompt caching, extended thinking, token counting, and Files API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.anthropic_features import AnthropicFeatures, FilesAPIManager
from models.metadata import (
    supports_extended_thinking, 
    get_extended_thinking_budget,
    is_anthropic_model,
    get_anthropic_config
)
from utils.token_stats import TokenStats


def test_anthropic_model_detection():
    """Test detection of Anthropic models."""
    print("Testing Anthropic model detection...")
    
    # Claude models should be detected
    assert is_anthropic_model('claude-opus-4-5-20251101'), "Claude Opus 4.5 should be detected"
    assert is_anthropic_model('claude-sonnet-4-5-20250929'), "Claude Sonnet 4.5 should be detected"
    assert is_anthropic_model('claude-haiku-4-5-20251001'), "Claude Haiku 4.5 should be detected"
    
    # Non-Claude models should not be detected
    assert not is_anthropic_model('gpt-5.2'), "GPT-5.2 should not be detected as Claude"
    assert not is_anthropic_model('grok-4-1-fast-reasoning'), "Grok should not be detected as Claude"
    
    print("  ✓ Anthropic model detection works correctly")
    print()


def test_extended_thinking_support():
    """Test extended thinking support detection."""
    print("Testing extended thinking support...")
    
    # Claude 4.x models should support extended thinking
    assert supports_extended_thinking('claude-opus-4-5-20251101'), "Opus 4.5 should support extended thinking"
    assert supports_extended_thinking('claude-sonnet-4-5-20250929'), "Sonnet 4.5 should support extended thinking"
    assert supports_extended_thinking('claude-haiku-4-5-20251001'), "Haiku 4.5 should support extended thinking"
    
    # Get budget tokens
    opus_budget = get_extended_thinking_budget('claude-opus-4-5-20251101')
    assert opus_budget == 32000, f"Opus 4.5 budget should be 32000, got {opus_budget}"
    
    sonnet_budget = get_extended_thinking_budget('claude-sonnet-4-5-20250929')
    assert sonnet_budget == 16000, f"Sonnet 4.5 budget should be 16000, got {sonnet_budget}"
    
    haiku_budget = get_extended_thinking_budget('claude-haiku-4-5-20251001')
    assert haiku_budget == 10000, f"Haiku 4.5 budget should be 10000, got {haiku_budget}"
    
    # Non-supporting models
    assert not supports_extended_thinking('gpt-5.2'), "GPT-5.2 should not support extended thinking"
    assert get_extended_thinking_budget('gpt-5.2') == 0, "GPT-5.2 should have 0 budget"
    
    print("  ✓ Extended thinking support detection works")
    print()


def test_anthropic_config_loading():
    """Test loading of Anthropic configuration."""
    print("Testing Anthropic config loading...")
    
    config = get_anthropic_config()
    assert isinstance(config, dict), "Config should be a dictionary"
    
    # Check prompt caching config
    assert 'prompt_caching' in config, "Should have prompt_caching config"
    assert config['prompt_caching'].get('enabled', False), "Prompt caching should be enabled"
    
    # Check token counting config
    assert 'token_counting' in config, "Should have token_counting config"
    assert config['token_counting'].get('enabled', False), "Token counting should be enabled"
    
    # Check files API config
    assert 'files_api' in config, "Should have files_api config"
    
    print(f"  ✓ Anthropic config loaded: {len(config)} sections")
    print()


def test_anthropic_features_initialization():
    """Test AnthropicFeatures class initialization."""
    print("Testing AnthropicFeatures initialization...")
    
    # Test with default config
    features = AnthropicFeatures(client=None, config=None)
    assert not features.is_files_api_enabled(), "Files API should be disabled by default"
    
    # Test with custom config
    custom_config = {
        'prompt_caching': {'enabled': True, 'cache_breakpoints': ['system', 'tools', 'context']},
        'files_api': {'enabled': True, 'upload_threshold_kb': 100},
        'token_counting': {'enabled': False}
    }
    features = AnthropicFeatures(client=None, config=custom_config)
    
    assert features.is_prompt_caching_enabled(), "Prompt caching should be enabled"
    assert features.is_files_api_enabled(), "Files API should be enabled"
    assert not features.is_token_counting_enabled(), "Token counting should be disabled"
    
    breakpoints = features.get_cache_breakpoints()
    assert len(breakpoints) == 3, f"Should have 3 breakpoints, got {len(breakpoints)}"
    assert 'context' in breakpoints, "Should include 'context' breakpoint"
    
    print("  ✓ AnthropicFeatures initialization works")
    print()


def test_cache_control_addition():
    """Test adding cache_control to content blocks."""
    print("Testing cache_control addition...")
    
    config = {'prompt_caching': {'enabled': True}}
    features = AnthropicFeatures(client=None, config=config)
    
    # Test with single content block
    content = [{'type': 'text', 'text': 'System prompt'}]
    result = features.add_cache_control(content)
    
    assert len(result) == 1, "Should have 1 block"
    assert 'cache_control' in result[0], "Should have cache_control"
    assert result[0]['cache_control']['type'] == 'ephemeral', "Should be ephemeral type"
    
    # Test with multiple blocks
    content = [
        {'type': 'text', 'text': 'First block'},
        {'type': 'text', 'text': 'Second block'},
        {'type': 'text', 'text': 'Third block'}
    ]
    result = features.add_cache_control(content)
    
    assert len(result) == 3, "Should have 3 blocks"
    assert 'cache_control' in result[-1], "Last block should have cache_control"
    assert 'cache_control' not in result[0], "First block should not have cache_control"
    assert 'cache_control' not in result[1], "Middle block should not have cache_control"
    
    # Test with caching disabled
    config_disabled = {'prompt_caching': {'enabled': False}}
    features_disabled = AnthropicFeatures(client=None, config=config_disabled)
    result = features_disabled.add_cache_control(content)
    
    assert 'cache_control' not in result[-1], "Should not add cache_control when disabled"
    
    print("  ✓ Cache control addition works")
    print()


def test_token_estimation():
    """Test token estimation."""
    print("Testing token estimation...")
    
    features = AnthropicFeatures(client=None, config=None)
    
    # Test simple text
    text = "Hello, world!"
    estimated = features.estimate_tokens(text)
    assert estimated == len(text) // 4, f"Should estimate {len(text) // 4} tokens, got {estimated}"
    
    # Test larger text
    large_text = "a" * 10000
    estimated = features.estimate_tokens(large_text)
    assert estimated == 2500, f"Should estimate 2500 tokens for 10000 chars, got {estimated}"
    
    print("  ✓ Token estimation works")
    print()


def test_precise_counting_threshold():
    """Test threshold for precise token counting."""
    print("Testing precise counting threshold...")
    
    # Default threshold is 10000
    config = {'token_counting': {'enabled': True, 'threshold_estimated_tokens': 10000}}
    features = AnthropicFeatures(client=None, config=config)
    
    assert not features.should_use_precise_counting(5000), "Should not use precise counting for 5000 tokens"
    assert not features.should_use_precise_counting(9999), "Should not use precise counting for 9999 tokens"
    assert features.should_use_precise_counting(10001), "Should use precise counting for 10001 tokens"
    assert features.should_use_precise_counting(50000), "Should use precise counting for 50000 tokens"
    
    # Custom threshold
    config_custom = {'token_counting': {'enabled': True, 'threshold_estimated_tokens': 5000}}
    features_custom = AnthropicFeatures(client=None, config=config_custom)
    
    assert features_custom.should_use_precise_counting(5001), "Should use precise counting above custom threshold"
    
    # Disabled
    config_disabled = {'token_counting': {'enabled': False}}
    features_disabled = AnthropicFeatures(client=None, config=config_disabled)
    
    assert not features_disabled.should_use_precise_counting(100000), "Should not use when disabled"
    
    print("  ✓ Precise counting threshold works")
    print()


def test_files_api_manager():
    """Test FilesAPIManager functionality."""
    print("Testing FilesAPIManager...")
    
    # Test initialization
    config = {'enabled': False, 'upload_threshold_kb': 50}
    manager = FilesAPIManager(client=None, config=config)
    
    assert not manager.is_enabled(), "Files API should be disabled"
    assert manager.get_upload_threshold_kb() == 50, "Threshold should be 50KB"
    
    # Test file size threshold
    assert not manager.should_upload_file(40 * 1024), "40KB should not trigger upload"
    assert not manager.should_upload_file(50 * 1024), "50KB should not trigger upload (disabled)"
    
    # Enable and test
    config_enabled = {'enabled': True, 'upload_threshold_kb': 50}
    manager_enabled = FilesAPIManager(client=None, config=config_enabled)
    
    assert not manager_enabled.should_upload_file(40 * 1024), "40KB should not trigger upload"
    assert manager_enabled.should_upload_file(51 * 1024), "51KB should trigger upload"
    assert manager_enabled.should_upload_file(100 * 1024), "100KB should trigger upload"
    
    print("  ✓ FilesAPIManager works")
    print()


def test_token_stats_with_cache():
    """Test TokenStats with cache tracking."""
    print("Testing TokenStats with cache...")
    
    stats = TokenStats()
    
    # Add usage without cache
    stats.add_usage('agent1', 'claude-opus-4-5-20251101', 1000, 500)
    agent_stats = stats.get_agent_stats('agent1')
    
    assert agent_stats['input'] == 1000, "Input tokens should be 1000"
    assert agent_stats['output'] == 500, "Output tokens should be 500"
    assert 'cache' not in agent_stats, "Should not have cache stats yet"
    
    # Add usage with cache
    stats.add_usage('agent1', 'claude-opus-4-5-20251101', 500, 300, 
                   cache_creation_tokens=2000, cache_read_tokens=0)
    agent_stats = stats.get_agent_stats('agent1')
    
    assert 'cache' in agent_stats, "Should have cache stats"
    assert agent_stats['cache']['creation'] == 2000, "Cache creation should be 2000"
    assert agent_stats['cache']['read'] == 0, "Cache read should be 0"
    
    # Add usage with cache hit
    stats.add_usage('agent1', 'claude-opus-4-5-20251101', 300, 200,
                   cache_creation_tokens=0, cache_read_tokens=1800)
    agent_stats = stats.get_agent_stats('agent1')
    
    assert agent_stats['cache']['read'] == 1800, "Cache read should be 1800"
    assert agent_stats['cache']['hits'] == 1, "Should have 1 cache hit"
    
    # Test total stats
    total = stats.get_total_stats()
    assert 'cache' in total, "Total should have cache stats"
    assert total['cache']['creation'] == 2000, "Total cache creation"
    assert total['cache']['read'] == 1800, "Total cache read"
    assert total['cache']['hits'] == 1, "Total cache hits"
    
    # Calculate hit rate
    hit_rate = total['cache']['hit_rate']
    expected_rate = 1 / 3  # 1 hit out of 3 messages
    assert abs(hit_rate - expected_rate) < 0.01, f"Hit rate should be ~{expected_rate:.2f}, got {hit_rate:.2f}"
    
    print("  ✓ TokenStats cache tracking works")
    print()


def test_backward_compatibility():
    """Test that new features don't break existing functionality."""
    print("Testing backward compatibility...")
    
    # Test that stats work without cache parameters
    stats = TokenStats()
    stats.add_usage('agent1', 'gpt-4o', 1000, 500)
    
    agent_stats = stats.get_agent_stats('agent1')
    assert agent_stats['input'] == 1000, "Standard usage tracking should work"
    assert agent_stats['output'] == 500, "Standard usage tracking should work"
    
    # Test that non-Anthropic models return False for Anthropic checks
    assert not is_anthropic_model('gpt-5.2'), "Non-Anthropic model check"
    assert not supports_extended_thinking('gpt-5.2'), "Extended thinking check"
    assert get_extended_thinking_budget('unknown-model') == 0, "Unknown model budget"
    
    print("  ✓ Backward compatibility maintained")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("ANTHROPIC FEATURES TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_anthropic_model_detection()
        test_extended_thinking_support()
        test_anthropic_config_loading()
        test_anthropic_features_initialization()
        test_cache_control_addition()
        test_token_estimation()
        test_precise_counting_threshold()
        test_files_api_manager()
        test_token_stats_with_cache()
        test_backward_compatibility()
        
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
