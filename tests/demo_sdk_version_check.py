#!/usr/bin/env python3
"""
Demo script to show the SDK version check error message.
This simulates what happens when a user has an old OpenAI SDK version.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock
from core.agent_manager import AgentManager
from core.config import Config
from test_utils import create_mock_openai_client_without_responses


def demo_sdk_version_error():
    """Demonstrate the error message when SDK is too old."""
    print("=" * 70)
    print("DEMO: OpenAI SDK Version Check")
    print("=" * 70)
    print()
    print("Scenario: User has OpenAI SDK version 2.15.0 (too old for Codex)")
    print("Expected: Clear error message with upgrade instructions")
    print()
    print("-" * 70)
    print()
    
    # Setup
    config = Config()
    manager = AgentManager(config)
    
    # Simulate old SDK without responses API
    mock_client = create_mock_openai_client_without_responses()
    
    manager.clients['openai'] = mock_client
    
    # Try to use Codex
    print("Attempting to call GPT-5.2 Codex agent...")
    print()
    result = manager.call_agent(
        agent_name='gpt_codex',
        prompt='Write a hello world program',
        context='',
        token_callback=None
    )
    
    # Show result
    print("RESULT:")
    print()
    print(result)
    print()
    print("-" * 70)
    print()
    
    # Verify it's the right error
    if "Responses API" in result and "upgrade" in result.lower():
        print("✅ SUCCESS: User gets clear error message with upgrade instructions")
    else:
        print("❌ FAIL: Error message is not clear enough")
        return False
    
    print()
    print("=" * 70)
    print()
    return True


def demo_sdk_version_success():
    """Demonstrate successful call with proper SDK."""
    print("=" * 70)
    print("DEMO: OpenAI SDK with Responses API Support")
    print("=" * 70)
    print()
    print("Scenario: User has OpenAI SDK version 1.58.0+ (supports Codex)")
    print("Expected: Successful API call to Responses endpoint")
    print()
    print("-" * 70)
    print()
    
    # Setup
    config = Config()
    manager = AgentManager(config)
    
    # Simulate new SDK with responses API
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "def hello():\n    print('Hello, World!')"
    mock_response.usage = MagicMock()
    mock_response.usage.input_tokens = 15
    mock_response.usage.output_tokens = 12
    
    mock_client.responses.create.return_value = mock_response
    manager.clients['openai'] = mock_client
    
    # Try to use Codex
    print("Attempting to call GPT-5.2 Codex agent...")
    print()
    result = manager.call_agent(
        agent_name='gpt_codex',
        prompt='Write a hello world program',
        context='',
        token_callback=None
    )
    
    # Show result
    print("RESULT:")
    print()
    print(result)
    print()
    print("-" * 70)
    print()
    
    # Verify success
    if not result.startswith("API error"):
        print("✅ SUCCESS: API call succeeded with proper SDK version")
    else:
        print("❌ FAIL: Got error when SDK should work")
        return False
    
    print()
    print("=" * 70)
    print()
    return True


if __name__ == '__main__':
    print()
    success = demo_sdk_version_error()
    print()
    success &= demo_sdk_version_success()
    
    if success:
        print()
        print("🎉 All demos passed! SDK version check is working correctly.")
        print()
        sys.exit(0)
    else:
        print()
        print("❌ Some demos failed.")
        print()
        sys.exit(1)
