#!/usr/bin/env python3
"""
Integration test for Anthropic features with AgentManager.
Demonstrates prompt caching, extended thinking, and token counting working together.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core.agent_manager import AgentManager
from utils.token_stats import TokenStats


def test_agent_manager_anthropic_initialization():
    """Test that AgentManager initializes Anthropic features correctly."""
    print("Testing AgentManager Anthropic initialization...")
    
    # Create a minimal config
    config = Config()
    manager = AgentManager(config)
    
    # Check if anthropic features were initialized
    if 'anthropic' in manager.clients:
        assert manager.anthropic_features is not None, "AnthropicFeatures should be initialized"
        print("  ✓ AnthropicFeatures initialized with Anthropic client")
    else:
        print("  ℹ Anthropic client not available (missing API key or library)")
    
    print()


def test_token_callback_compatibility():
    """Test that token callbacks work with and without cache parameters."""
    print("Testing token callback compatibility...")
    
    stats = TokenStats()
    
    # Standard callback (4 parameters)
    def standard_callback(agent_name, model, input_tokens, output_tokens):
        stats.add_usage(agent_name, model, input_tokens, output_tokens)
    
    # Enhanced callback (6 parameters) - supports cache
    def enhanced_callback(agent_name, model, input_tokens, output_tokens, 
                         cache_creation, cache_read):
        stats.add_usage(agent_name, model, input_tokens, output_tokens,
                       cache_creation, cache_read)
    
    # Test standard callback
    standard_callback('test_agent', 'claude-opus-4-5-20251101', 1000, 500)
    agent_stats = stats.get_agent_stats('test_agent')
    assert agent_stats['input'] == 1000, "Standard callback should work"
    
    # Test enhanced callback
    enhanced_callback('test_agent', 'claude-opus-4-5-20251101', 800, 400, 2000, 1500)
    agent_stats = stats.get_agent_stats('test_agent')
    assert 'cache' in agent_stats, "Enhanced callback should track cache"
    assert agent_stats['cache']['creation'] == 2000, "Cache creation tracked"
    assert agent_stats['cache']['read'] == 1500, "Cache read tracked"
    
    print("  ✓ Both callback types work correctly")
    print()


def test_extended_thinking_configuration():
    """Test that extended thinking is properly configured for Claude models."""
    print("Testing extended thinking configuration...")
    
    from models.metadata import get_model_info, supports_extended_thinking, get_extended_thinking_budget
    
    # Test all Claude 4.x models that should have extended thinking
    test_models = [
        ('claude-opus-4-5-20251101', 32000),
        ('claude-sonnet-4-5-20250929', 16000),
        ('claude-haiku-4-5-20251001', 10000),
        ('claude-opus-4-1-20250805', 24000),
        ('claude-opus-4-20250514', 24000),
        ('claude-sonnet-4-20250514', 16000),
    ]
    
    for model, expected_budget in test_models:
        model_info = get_model_info(model)
        assert 'extended_thinking' in model_info, f"{model} should have extended_thinking config"
        assert supports_extended_thinking(model), f"{model} should support extended thinking"
        
        budget = get_extended_thinking_budget(model)
        assert budget == expected_budget, f"{model} should have budget {expected_budget}, got {budget}"
    
    print(f"  ✓ Extended thinking configured for {len(test_models)} models")
    print()


def test_cache_control_structure():
    """Test that cache_control blocks are properly structured."""
    print("Testing cache_control structure...")
    
    from core.anthropic_features import AnthropicFeatures
    
    config = {
        'prompt_caching': {
            'enabled': True,
            'cache_breakpoints': ['system', 'tools'],
            'default_ttl': '5m'
        }
    }
    
    features = AnthropicFeatures(client=None, config=config)
    
    # Test system prompt conversion to cacheable format
    system_blocks = [
        {'type': 'text', 'text': 'You are a helpful assistant.'}
    ]
    
    cached_blocks = features.add_cache_control(system_blocks)
    
    assert len(cached_blocks) == 1, "Should have 1 block"
    assert cached_blocks[0]['type'] == 'text', "Should preserve type"
    assert cached_blocks[0]['text'] == 'You are a helpful assistant.', "Should preserve text"
    assert 'cache_control' in cached_blocks[0], "Should add cache_control"
    assert cached_blocks[0]['cache_control']['type'] == 'ephemeral', "Should be ephemeral"
    
    print("  ✓ Cache control structure is correct")
    print()


def test_token_counting_configuration():
    """Test token counting configuration."""
    print("Testing token counting configuration...")
    
    from models.metadata import get_anthropic_config
    
    config = get_anthropic_config()
    token_config = config.get('token_counting', {})
    
    assert token_config.get('enabled', False), "Token counting should be enabled"
    threshold = token_config.get('threshold_estimated_tokens', 0)
    assert threshold == 10000, f"Threshold should be 10000, got {threshold}"
    
    print(f"  ✓ Token counting enabled with threshold: {threshold}")
    print()


def test_prompt_caching_configuration():
    """Test prompt caching configuration."""
    print("Testing prompt caching configuration...")
    
    from models.metadata import get_anthropic_config
    
    config = get_anthropic_config()
    cache_config = config.get('prompt_caching', {})
    
    assert cache_config.get('enabled', False), "Prompt caching should be enabled"
    breakpoints = cache_config.get('cache_breakpoints', [])
    assert 'system' in breakpoints, "Should have 'system' breakpoint"
    assert 'tools' in breakpoints, "Should have 'tools' breakpoint"
    
    ttl = cache_config.get('default_ttl', '')
    assert ttl == '5m', f"Default TTL should be '5m', got '{ttl}'"
    
    print(f"  ✓ Prompt caching enabled with {len(breakpoints)} breakpoints and TTL: {ttl}")
    print()


def test_files_api_configuration():
    """Test Files API configuration."""
    print("Testing Files API configuration...")
    
    from models.metadata import get_anthropic_config
    
    config = get_anthropic_config()
    files_config = config.get('files_api', {})
    
    # Files API should be disabled by default (beta)
    assert not files_config.get('enabled', True), "Files API should be disabled by default"
    
    threshold = files_config.get('upload_threshold_kb', 0)
    assert threshold == 50, f"Upload threshold should be 50KB, got {threshold}"
    
    print(f"  ✓ Files API configured (disabled by default, threshold: {threshold}KB)")
    print()


def test_complete_workflow_simulation():
    """Simulate a complete workflow with all features."""
    print("Testing complete workflow simulation...")
    
    from core.anthropic_features import AnthropicFeatures
    from models.metadata import supports_extended_thinking, get_extended_thinking_budget
    
    # Initialize features
    config = {
        'prompt_caching': {'enabled': True, 'cache_breakpoints': ['system', 'tools']},
        'token_counting': {'enabled': True, 'threshold_estimated_tokens': 10000},
        'files_api': {'enabled': False}
    }
    features = AnthropicFeatures(client=None, config=config)
    stats = TokenStats()
    
    # Step 1: Check if model supports extended thinking
    model = 'claude-opus-4-5-20251101'
    assert supports_extended_thinking(model), "Model should support extended thinking"
    budget = get_extended_thinking_budget(model)
    assert budget > 0, "Should have thinking budget"
    
    # Step 2: Prepare cacheable content
    system_prompt = [{'type': 'text', 'text': 'Large system context here...'}]
    cached_system = features.add_cache_control(system_prompt)
    assert 'cache_control' in cached_system[0], "System should be cacheable"
    
    # Step 3: Estimate tokens to decide on precise counting
    large_prompt = "a" * 50000  # 50k characters ~ 12.5k tokens
    estimated = features.estimate_tokens(large_prompt)
    assert features.should_use_precise_counting(estimated), "Should use precise counting"
    
    # Step 4: Track usage with cache (simulating first call - cache creation)
    stats.add_usage('test_workflow', model, 5000, 2000, cache_creation_tokens=10000, cache_read_tokens=0)
    
    # Step 5: Track usage with cache hit (simulating second call)
    stats.add_usage('test_workflow', model, 3000, 1800, cache_creation_tokens=0, cache_read_tokens=9500)
    
    # Step 6: Verify results
    agent_stats = stats.get_agent_stats('test_workflow')
    assert agent_stats['cache']['creation'] == 10000, "Cache creation tracked"
    assert agent_stats['cache']['read'] == 9500, "Cache read tracked"
    assert agent_stats['cache']['hits'] == 1, "Cache hit recorded"
    
    total_stats = stats.get_total_stats()
    assert 'cache' in total_stats, "Total should include cache stats"
    
    # Calculate savings
    total_input_without_cache = agent_stats['input'] + agent_stats['cache']['creation']
    total_saved = agent_stats['cache']['read']
    savings_pct = (total_saved / total_input_without_cache) * 100 if total_input_without_cache > 0 else 0
    
    print(f"  ✓ Complete workflow simulation successful")
    print(f"    - Extended thinking: enabled (budget: {budget} tokens)")
    print(f"    - Prompt caching: enabled")
    print(f"    - Cache creation: {agent_stats['cache']['creation']} tokens")
    print(f"    - Cache reads: {agent_stats['cache']['read']} tokens")
    print(f"    - Cache hit rate: {agent_stats['cache']['hits']}/{agent_stats['messages']}")
    print(f"    - Token savings: {savings_pct:.1f}%")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("ANTHROPIC FEATURES INTEGRATION TEST")
    print("=" * 60)
    print()
    
    try:
        test_agent_manager_anthropic_initialization()
        test_token_callback_compatibility()
        test_extended_thinking_configuration()
        test_cache_control_structure()
        test_token_counting_configuration()
        test_prompt_caching_configuration()
        test_files_api_configuration()
        test_complete_workflow_simulation()
        
        print("=" * 60)
        print("ALL INTEGRATION TESTS PASSED ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
