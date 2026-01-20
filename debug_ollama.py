#!/usr/bin/env python3
"""
Debug script to check Ollama initialization.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core.agent_manager import AgentManager

# Clear any existing Ollama API key
if 'OLLAMA_API_KEY' in os.environ:
    del os.environ['OLLAMA_API_KEY']

print("Creating config...")
config = Config()

print("\nChecking providers configuration:")
providers = config.get('providers', default={})
if 'ollama' in providers:
    ollama_config = providers['ollama']
    print(f"  Ollama enabled: {ollama_config.get('enabled', True)}")
    print(f"  Ollama requires_auth: {ollama_config.get('requires_auth', True)}")
    print(f"  Ollama env_key: {ollama_config.get('env_key', 'None')}")
    print(f"  Ollama base_url: {ollama_config.get('base_url', 'None')}")
else:
    print("  ERROR: Ollama not found in providers!")

print("\nCreating AgentManager...")
manager = AgentManager(config)

print(f"\nInitialized clients: {list(manager.clients.keys())}")

if 'ollama' in manager.clients:
    print("✓ SUCCESS: Ollama client initialized!")
    print(f"  Client type: {type(manager.clients['ollama'])}")
else:
    print("✗ FAILED: Ollama client not initialized")
    
    # Try to check if HAS_OPENAI is True
    try:
        from openai import OpenAI
        print("  OpenAI library is available")
    except ImportError:
        print("  ERROR: OpenAI library not available")
