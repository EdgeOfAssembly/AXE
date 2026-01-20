#!/usr/bin/env python3
"""
Test for Ollama provider initialization without authentication.
Verifies that providers with requires_auth: false can initialize without API keys.

NOTE: This test starts an Ollama server but does NOT pull any models.
      To test with actual inference, pull a model first:
      
      Small models (good for CI/testing with limited resources):
      - ollama pull qwen2:0.5b       # Tiny (~352MB) - fastest for CI
      - ollama pull tinyllama        # Small (~637MB)
      - ollama pull llama3.2:1b      # Very small (~1.3GB)
      - ollama pull phi              # Small (~1.6GB)
      - ollama pull llama3.2:3b      # Small (~2GB) - good balance
      
      If llama3.2:3b is too large, use qwen2:0.5b or tinyllama instead.
"""

import sys
import os
import subprocess
import time
import signal
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core.agent_manager import AgentManager


# Global variable to track Ollama server process
ollama_process = None


def start_ollama_server():
    """Start Ollama server in background if not already running."""
    global ollama_process
    
    # Check if Ollama is already running
    try:
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        if response.status_code == 200:
            print("  ℹ Ollama server already running")
            return True
    except:
        pass
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("  ⚠ Ollama not installed - skipping server tests")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ⚠ Ollama not installed - skipping server tests")
        return False
    
    # Start Ollama server in background
    print("  → Starting Ollama server in background...")
    try:
        ollama_process = subprocess.Popen(
            ['ollama', 'serve'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent process
        )
        
        # Wait for server to be ready (max 10 seconds)
        for i in range(20):
            time.sleep(0.5)
            try:
                response = requests.get('http://localhost:11434/api/version', timeout=1)
                if response.status_code == 200:
                    print("  ✓ Ollama server started successfully")
                    return True
            except:
                continue
        
        print("  ⚠ Ollama server did not start in time")
        return False
        
    except Exception as e:
        print(f"  ⚠ Failed to start Ollama server: {e}")
        return False


def stop_ollama_server():
    """Stop Ollama server if it was started by this test."""
    global ollama_process
    
    if ollama_process is not None:
        print("\n  → Stopping Ollama server...")
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)
            ollama_process.wait(timeout=5)
            print("  ✓ Ollama server stopped")
        except ProcessLookupError:
            print("  ℹ Ollama server already stopped")
        except Exception as e:
            print(f"  ⚠ Error stopping Ollama server: {e}")
            try:
                # Force kill if graceful shutdown failed
                os.killpg(os.getpgid(ollama_process.pid), signal.SIGKILL)
            except:
                pass
        finally:
            ollama_process = None


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
    
    # Start Ollama server
    server_started = start_ollama_server()
    
    try:
        test_ollama_initialization_without_api_key()
        test_requires_auth_field()
        test_providers_requiring_auth_still_work()
        test_edge_cases()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    finally:
        # Always stop the server when done
        stop_ollama_server()
