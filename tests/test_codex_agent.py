#!/usr/bin/env python3
"""
Test suite for GPT-5.2 Codex agent configuration.
Tests the Responses API integration and agent configuration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.metadata import get_model_info, uses_responses_api
from core.config import Config


def test_codex_model_metadata():
    """Test that gpt-5.2-codex model has correct metadata."""
    print("Testing gpt-5.2-codex model metadata...")
    
    model_info = get_model_info('gpt-5.2-codex')
    assert model_info['context_tokens'] == 400000, "Codex should have 400k context"
    assert model_info['max_output_tokens'] == 128000, "Codex should have 128k output"
    assert model_info['api_type'] == 'responses', "Codex should use responses API"
    assert 'text' in model_info['input_modes'], "Codex should support text input"
    assert 'image' in model_info['input_modes'], "Codex should support image input"
    assert 'function_calling' in model_info['output_modes'], "Codex should support function calling"
    print("  ✓ gpt-5.2-codex metadata correct")


def test_codex_uses_responses_api():
    """Test that codex model correctly identified as using Responses API."""
    print("Testing uses_responses_api detection...")
    
    assert uses_responses_api('gpt-5.2-codex') == True, "Codex should use responses API"
    assert uses_responses_api('gpt-5.2') == False, "GPT-5.2 should use chat completions"
    assert uses_responses_api('claude-opus-4-5-20251101') == False, "Claude should use chat completions"
    print("  ✓ Responses API detection works correctly")


def test_codex_agent_config():
    """Test that gpt_codex agent is configured correctly."""
    print("Testing gpt_codex agent configuration...")
    
    config = Config()
    agents = config.get('agents', default={})
    
    assert 'gpt_codex' in agents, "gpt_codex agent should exist"
    
    codex_agent = agents['gpt_codex']
    assert codex_agent['provider'] == 'openai', "Provider should be openai"
    assert codex_agent['model'] == 'gpt-5.2-codex', "Model should be gpt-5.2-codex"
    assert 'codex' in codex_agent.get('alias', []), "Should have 'codex' alias"
    assert codex_agent.get('api_endpoint') == 'responses', "Should specify responses API endpoint"
    assert codex_agent['context_tokens'] == 400000, "Should have 400k context"
    print("  ✓ gpt_codex agent configured correctly")


def test_existing_agents_unchanged():
    """Test that existing agents still work correctly."""
    print("Testing existing agents are unchanged...")
    
    config = Config()
    agents = config.get('agents', default={})
    
    # Test GPT agent
    assert 'gpt' in agents, "gpt agent should still exist"
    assert agents['gpt']['model'] == 'gpt-5.2-2025-12-11', "gpt model unchanged"
    
    # Test Claude agent
    assert 'claude' in agents, "claude agent should still exist"
    assert agents['claude']['provider'] == 'anthropic', "claude provider unchanged"
    
    print("  ✓ Existing agents unchanged")


if __name__ == '__main__':
    print("=" * 60)
    print("CODEX AGENT TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_codex_model_metadata()
        test_codex_uses_responses_api()
        test_codex_agent_config()
        test_existing_agents_unchanged()
        
        print()
        print("=" * 60)
        print("✅ ALL CODEX AGENT TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
