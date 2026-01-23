#!/usr/bin/env python3
"""
Test suite for OpenAI SDK version check with Responses API.
Verifies that the system properly handles cases where the OpenAI SDK
doesn't support the Responses API.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, PropertyMock
from core.agent_manager import AgentManager
from core.config import Config


def create_mock_client_without_responses():
    """Helper to create a mock OpenAI client without responses API."""
    mock_client = MagicMock(spec_set=['chat'])  # Only has 'chat', not 'responses'
    mock_client.chat = MagicMock()
    return mock_client


def test_responses_api_sdk_version_check():
    """Test that SDK version check works when responses API is not available."""
    print("Testing OpenAI SDK version check for Responses API...")
    
    config = Config()
    manager = AgentManager(config)
    
    # Create a mock OpenAI client without 'responses' attribute
    mock_client = create_mock_client_without_responses()
    
    # Replace the actual client with our mock
    manager.clients['openai'] = mock_client
    
    # Try to make a call - should return error message
    result = manager.call_agent(
        agent_name='gpt_codex',  # Use the actual codex agent from config
        prompt='Test prompt',
        context='',
        token_callback=None
    )
    
    # Verify error message is returned
    assert isinstance(result, str), "Should return a string error message"
    assert "API error" in result, f"Error message should mention API error, got: {result}"
    assert "Responses API" in result, f"Error message should mention Responses API, got: {result}"
    assert "OpenAI" in result or "openai" in result.lower(), f"Error message should mention OpenAI SDK, got: {result}"
    assert "upgrade" in result.lower() or "install" in result.lower(), f"Error message should mention upgrade, got: {result}"
    
    print("  ✓ SDK version check correctly detects missing Responses API")
    print(f"  ✓ Error message: {result[:150]}...")


def test_responses_api_with_valid_sdk():
    """Test that Responses API works when SDK supports it."""
    print("Testing OpenAI SDK with valid Responses API support...")
    
    config = Config()
    manager = AgentManager(config)
    
    # Create a mock OpenAI client WITH 'responses' attribute
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "Test response from Codex"
    mock_response.usage = MagicMock()
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 20
    
    # Set up the mock responses API properly
    mock_client.responses.create.return_value = mock_response
    
    # Replace the actual client with our mock
    manager.clients['openai'] = mock_client
    
    # Try to make a call - should work without errors
    result = manager.call_agent(
        agent_name='gpt_codex',  # Use the actual codex agent from config
        prompt='Test prompt',
        context='',
        token_callback=None
    )
    
    # Verify successful response
    assert isinstance(result, str), "Should return a string response"
    assert result == "Test response from Codex", f"Should return the mock response text, got: {result}"
    assert not result.startswith("API error"), f"Should not return an error message, got: {result}"
    
    # Verify the API was called with correct parameters
    mock_client.responses.create.assert_called_once()
    call_kwargs = mock_client.responses.create.call_args[1]
    assert call_kwargs['model'] == 'gpt-5.2-codex', f"Should use correct model, got: {call_kwargs.get('model')}"
    assert 'input' in call_kwargs, "Should have 'input' parameter"
    assert 'instructions' in call_kwargs, "Should have 'instructions' parameter"
    assert call_kwargs['max_output_tokens'] > 0, "Should have max_output_tokens parameter"
    
    print("  ✓ Responses API works correctly with valid SDK")


def test_regular_chat_completion_unaffected():
    """Test that regular chat completion models are not affected by the SDK check."""
    print("Testing that regular Chat Completions are unaffected...")
    
    config = Config()
    manager = AgentManager(config)
    
    # Create a mock OpenAI client without 'responses' attribute
    mock_client = create_mock_client_without_responses()
    
    # Set up chat.completions mock
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Test response from GPT"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    
    mock_client.chat.completions.create.return_value = mock_response
    
    # Replace the actual client with our mock
    manager.clients['openai'] = mock_client
    
    # Try to make a call with a regular GPT agent - should work fine
    result = manager.call_agent(
        agent_name='gpt',  # Use the actual gpt agent from config
        prompt='Test prompt',
        context='',
        token_callback=None
    )
    
    # Verify successful response
    assert isinstance(result, str), "Should return a string response"
    assert result == "Test response from GPT", f"Should return the mock response text, got: {result}"
    assert not result.startswith("API error"), f"Should not return an error message, got: {result}"
    
    # Verify chat completions was called
    mock_client.chat.completions.create.assert_called_once()
    
    print("  ✓ Regular Chat Completions work correctly without Responses API")


if __name__ == '__main__':
    print("=" * 70)
    print("OPENAI SDK VERSION CHECK TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        test_responses_api_sdk_version_check()
        test_responses_api_with_valid_sdk()
        test_regular_chat_completion_unaffected()
        
        print()
        print("=" * 70)
        print("✅ ALL OPENAI SDK VERSION CHECK TESTS PASSED!")
        print("=" * 70)
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
