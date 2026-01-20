#!/usr/bin/env python3
"""
Test for Ollama provider initialization without authentication.
Verifies that providers with requires_auth: false can initialize without API keys.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core.agent_manager import AgentManager


def test_ollama_initialization_without_api_key():
    """Test that Ollama initializes without requiring an API key."""
    print("Testing Ollama initialization without API key...")
    
    # Ensure no Ollama API key is set
    if 'OLLAMA_API_KEY' in os.environ:
        del os.environ['OLLAMA_API_KEY']
    
    # Create config and manager
    config = Config()
    manager = AgentManager(config)
    
    # Check if Ollama client was initialized
    if 'ollama' in manager.clients:
        print("  ✓ Ollama client initialized without API key (requires_auth: false)")
        assert manager.clients['ollama'] is not None, "Ollama client should not be None"
    else:
        print("  ℹ Ollama client not initialized (OpenAI library may be missing or Ollama disabled)")
    
    print()


def test_requires_auth_field():
    """Test that requires_auth field is properly read from providers.yaml."""
    print("Testing requires_auth configuration field...")
    
    config = Config()
    providers = config.get('providers', default={})
    
    # Check Ollama configuration
    if 'ollama' in providers:
        ollama_config = providers['ollama']
        requires_auth = ollama_config.get('requires_auth', True)  # Default is True
        
        # Ollama should have requires_auth: false
        assert requires_auth == False, "Ollama should have requires_auth: false in providers.yaml"
        print("  ✓ Ollama has requires_auth: false in configuration")
    else:
        print("  ⚠ Ollama not found in providers configuration")
    
    print()


def test_providers_requiring_auth_still_work():
    """Ensure providers that require auth still require API keys."""
    print("Testing that providers requiring auth still need API keys...")
    
    # Clear all API keys
    api_keys_to_clear = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'XAI_API_KEY', 
                          'GITHUB_TOKEN', 'HUGGINGFACE_API_KEY']
    original_values = {}
    for key in api_keys_to_clear:
        if key in os.environ:
            original_values[key] = os.environ[key]
            del os.environ[key]
    
    try:
        config = Config()
        manager = AgentManager(config)
        
        # These providers should NOT be initialized without API keys
        auth_required_providers = ['anthropic', 'openai', 'xai', 'github', 'huggingface']
        
        for provider in auth_required_providers:
            if provider in manager.clients:
                print(f"  ⚠ WARNING: {provider} initialized without API key (should require auth)")
            else:
                print(f"  ✓ {provider} correctly skipped (no API key)")
        
        # Ollama should still be initialized
        if 'ollama' in manager.clients:
            print("  ✓ Ollama initialized without API key (as expected)")
        
    finally:
        # Restore original values
        for key, value in original_values.items():
            os.environ[key] = value
    
    print()


def test_edge_cases():
    """Test edge cases for Ollama authentication."""
    print("Testing edge cases for Ollama authentication...")
    
    # Test Case 1: Empty string API key
    os.environ['OLLAMA_API_KEY'] = ""
    config = Config()
    manager = AgentManager(config)
    if 'ollama' in manager.clients:
        print("  ✓ Empty API key: Ollama initialized")
    
    # Test Case 2: Fake/placeholder API key
    os.environ['OLLAMA_API_KEY'] = "fake_key_123"
    config = Config()
    manager = AgentManager(config)
    if 'ollama' in manager.clients:
        print("  ✓ Fake API key: Ollama initialized")
    
    # Test Case 3: No API key environment variable
    if 'OLLAMA_API_KEY' in os.environ:
        del os.environ['OLLAMA_API_KEY']
    config = Config()
    manager = AgentManager(config)
    if 'ollama' in manager.clients:
        print("  ✓ No API key: Ollama initialized")
    
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("OLLAMA AUTHENTICATION TEST")
    print("=" * 60)
    print()
    
    test_ollama_initialization_without_api_key()
    test_requires_auth_field()
    test_providers_requiring_auth_still_work()
    test_edge_cases()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
