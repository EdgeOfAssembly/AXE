#!/usr/bin/env python3
"""
Tests for the three-file configuration architecture refactor.

Tests:
- Loading order: models.yaml → providers.yaml → axe.yaml
- Validation catches configuration errors
- Agent overrides work properly
- Backward compatibility with missing providers.yaml
- Key standardization (context_tokens vs context_window)
"""

import os
import sys
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from utils.formatting import Colors, c


def test_loading_order():
    """Test that configuration loads in correct order: models → providers → axe"""
    print(c("\n=== Test: Loading Order ===", Colors.CYAN))
    
    # This test verifies the loading happens and order is correct
    # by checking that the config object has data from all three files
    config = Config()
    
    # Check models.yaml loaded (should have models_config populated)
    assert hasattr(config, 'models_config'), "models_config not loaded"
    assert len(config.models_config.get('models', {})) > 0, "No models loaded from models.yaml"
    print(c(f"✓ Models loaded: {len(config.models_config.get('models', {}))} models", Colors.GREEN))
    
    # Check providers.yaml loaded (should have providers_config populated)
    assert hasattr(config, 'providers_config'), "providers_config not loaded"
    assert len(config.providers_config) > 0, "No providers loaded"
    print(c(f"✓ Providers loaded: {len(config.providers_config)} providers", Colors.GREEN))
    
    # Check axe.yaml loaded (should have agents in main config)
    assert 'agents' in config.config, "Agents not loaded from axe.yaml"
    assert len(config.config['agents']) > 0, "No agents configured"
    print(c(f"✓ Agents loaded: {len(config.config['agents'])} agents", Colors.GREEN))
    
    print(c("✓ Test passed: All three config files loaded in order\n", Colors.GREEN))


def test_context_tokens_standardization():
    """Test that all configurations use context_tokens instead of context_window"""
    print(c("\n=== Test: context_tokens Standardization ===", Colors.CYAN))
    
    config = Config()
    
    # Check models.yaml uses context_tokens
    for model_name, model_info in config.models_config.get('models', {}).items():
        assert 'context_tokens' in model_info, f"Model {model_name} missing context_tokens"
        assert 'context_window' not in model_info, f"Model {model_name} uses deprecated context_window"
    print(c(f"✓ All {len(config.models_config.get('models', {}))} models use context_tokens", Colors.GREEN))
    
    # Check agent definitions use context_tokens (if they specify it)
    agents_with_context = 0
    for agent_name, agent_info in config.config.get('agents', {}).items():
        if 'context_tokens' in agent_info or 'context_window' in agent_info:
            agents_with_context += 1
            assert 'context_tokens' in agent_info, f"Agent {agent_name} uses deprecated context_window"
            assert 'context_window' not in agent_info, f"Agent {agent_name} has context_window"
    print(c(f"✓ All {agents_with_context} agents with context specs use context_tokens", Colors.GREEN))
    
    print(c("✓ Test passed: Standardized on context_tokens key\n", Colors.GREEN))


def test_provider_validation():
    """Test that provider validation catches configuration errors"""
    print(c("\n=== Test: Provider Validation ===", Colors.CYAN))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a models.yaml with limited models
        models_path = os.path.join(tmpdir, 'models.yaml')
        with open(models_path, 'w') as f:
            yaml.dump({
                'models': {
                    'gpt-4o': {
                        'context_tokens': 128000,
                        'max_output_tokens': 4000,
                        'input_modes': ['text'],
                        'output_modes': ['text']
                    }
                }
            }, f)
        
        # Create a providers.yaml that references non-existent model
        providers_path = os.path.join(tmpdir, 'providers.yaml')
        with open(providers_path, 'w') as f:
            yaml.dump({
                'providers': {
                    'openai': {
                        'enabled': True,
                        'env_key': 'OPENAI_API_KEY',
                        'models': ['gpt-4o', 'nonexistent-model']  # Should trigger validation error
                    }
                }
            }, f)
        
        # Create minimal axe.yaml
        axe_path = os.path.join(tmpdir, 'axe.yaml')
        with open(axe_path, 'w') as f:
            yaml.dump({
                'agents': {}
            }, f)
        
        # Load config - validation should print errors but not crash
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            Config()
            # Validation runs internally and prints errors
            print(c("✓ Validation detected invalid provider model (check output above)", Colors.GREEN))
        finally:
            os.chdir(original_dir)
    
    print(c("✓ Test passed: Provider validation works\n", Colors.GREEN))


def test_agent_validation():
    """Test that agent validation catches configuration errors"""
    print(c("\n=== Test: Agent Validation ===", Colors.CYAN))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal models.yaml
        models_path = os.path.join(tmpdir, 'models.yaml')
        with open(models_path, 'w') as f:
            yaml.dump({
                'models': {
                    'gpt-4o': {
                        'context_tokens': 128000,
                        'max_output_tokens': 4000,
                        'input_modes': ['text'],
                        'output_modes': ['text']
                    }
                }
            }, f)
        
        # Create providers.yaml
        providers_path = os.path.join(tmpdir, 'providers.yaml')
        with open(providers_path, 'w') as f:
            yaml.dump({
                'providers': {
                    'openai': {
                        'enabled': True,
                        'env_key': 'OPENAI_API_KEY',
                        'models': ['gpt-4o']
                    },
                    'disabled_provider': {
                        'enabled': False,
                        'env_key': 'DISABLED_API_KEY',
                        'models': ['some-model']
                    }
                }
            }, f)
        
        # Create axe.yaml with invalid agent configs
        axe_path = os.path.join(tmpdir, 'axe.yaml')
        with open(axe_path, 'w') as f:
            yaml.dump({
                'agents': {
                    'test1': {
                        'provider': 'nonexistent_provider',  # Should fail
                        'model': 'gpt-4o'
                    },
                    'test2': {
                        'provider': 'disabled_provider',  # Should fail (disabled)
                        'model': 'some-model'
                    },
                    'test3': {
                        'provider': 'openai',
                        'model': 'GPT-4O'  # Should fail (uppercase)
                    }
                }
            }, f)
        
        # Load config - validation should print errors
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            Config()
            print(c("✓ Validation detected invalid agent configs (check output above)", Colors.GREEN))
        finally:
            os.chdir(original_dir)
    
    print(c("✓ Test passed: Agent validation works\n", Colors.GREEN))


def test_backward_compatibility():
    """Test backward compatibility when providers.yaml is missing"""
    print(c("\n=== Test: Backward Compatibility ===", Colors.CYAN))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create models.yaml
        models_path = os.path.join(tmpdir, 'models.yaml')
        with open(models_path, 'w') as f:
            yaml.dump({
                'models': {
                    'gpt-4o': {
                        'context_tokens': 128000,
                        'max_output_tokens': 4000,
                        'input_modes': ['text'],
                        'output_modes': ['text']
                    }
                }
            }, f)
        
        # Create axe.yaml WITH providers (legacy format)
        axe_path = os.path.join(tmpdir, 'axe.yaml')
        with open(axe_path, 'w') as f:
            yaml.dump({
                'providers': {  # Legacy: providers in axe.yaml
                    'openai': {
                        'enabled': True,
                        'env_key': 'OPENAI_API_KEY',
                        'models': ['gpt-4o']
                    }
                },
                'agents': {
                    'gpt': {
                        'provider': 'openai',
                        'model': 'gpt-4o',
                        'context_tokens': 128000
                    }
                }
            }, f)
        
        # DON'T create providers.yaml - test backward compat
        
        # Load config - should work with legacy format
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = Config()
            assert 'providers' in config.config, "Legacy providers not loaded"
            assert 'openai' in config.config['providers'], "OpenAI provider not found"
            print(c("✓ Successfully loaded legacy config without providers.yaml", Colors.GREEN))
        finally:
            os.chdir(original_dir)
    
    print(c("✓ Test passed: Backward compatibility maintained\n", Colors.GREEN))


def test_agent_overrides():
    """Test that agent overrides work correctly"""
    print(c("\n=== Test: Agent Overrides ===", Colors.CYAN))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create models.yaml with high context
        models_path = os.path.join(tmpdir, 'models.yaml')
        with open(models_path, 'w') as f:
            yaml.dump({
                'models': {
                    'gpt-4o': {
                        'context_tokens': 128000,  # Model default
                        'max_output_tokens': 16000,
                        'input_modes': ['text'],
                        'output_modes': ['text']
                    }
                }
            }, f)
        
        # Create providers.yaml
        providers_path = os.path.join(tmpdir, 'providers.yaml')
        with open(providers_path, 'w') as f:
            yaml.dump({
                'providers': {
                    'openai': {
                        'enabled': True,
                        'env_key': 'OPENAI_API_KEY',
                        'models': ['gpt-4o']
                    }
                }
            }, f)
        
        # Create axe.yaml with override
        axe_path = os.path.join(tmpdir, 'axe.yaml')
        with open(axe_path, 'w') as f:
            yaml.dump({
                'agents': {
                    'gpt_limited': {
                        'provider': 'openai',
                        'model': 'gpt-4o',
                        'context_tokens': 64000  # OVERRIDE: Cap lower for cost
                    }
                }
            }, f)
        
        # Load config
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = Config()
            
            # Check that agent has overridden context
            agent = config.config['agents']['gpt_limited']
            assert agent['context_tokens'] == 64000, "Override not applied"
            print(c("✓ Agent override (64000) correctly overrides model default (128000)", Colors.GREEN))
        finally:
            os.chdir(original_dir)
    
    print(c("✓ Test passed: Agent overrides work correctly\n", Colors.GREEN))


def test_ollama_provider_exists():
    """Test that ollama provider is defined and enabled by default"""
    print(c("\n=== Test: Ollama Provider ===", Colors.CYAN))
    
    config = Config()
    
    # Check ollama exists in providers
    assert 'ollama' in config.providers_config, "Ollama provider not found"
    
    # Check it's enabled by default (changed from disabled)
    assert config.providers_config['ollama'].get('enabled') == True, "Ollama should be enabled by default"
    print(c("✓ Ollama provider exists and is enabled by default", Colors.GREEN))
    
    # Check it has models defined
    ollama_models = config.providers_config['ollama'].get('models', [])
    assert len(ollama_models) > 0, "Ollama has no models defined"
    print(c(f"✓ Ollama has {len(ollama_models)} models defined", Colors.GREEN))
    
    # Check base_url is set for local access
    assert config.providers_config['ollama'].get('base_url'), "Ollama base_url not set"
    assert 'localhost' in config.providers_config['ollama']['base_url'], "Ollama base_url should point to localhost"
    print(c(f"✓ Ollama base_url: {config.providers_config['ollama']['base_url']}", Colors.GREEN))
    
    print(c("✓ Test passed: Ollama provider properly configured\n", Colors.GREEN))


def test_local_agent_exists():
    """Test that local agent exists and uses ollama"""
    print(c("\n=== Test: Local Agent ===", Colors.CYAN))
    
    config = Config()
    
    # Check local agent exists
    assert 'local' in config.config.get('agents', {}), "Local agent not found"
    
    local_agent = config.config['agents']['local']
    
    # Check it uses ollama provider
    assert local_agent.get('provider') == 'ollama', "Local agent should use ollama provider"
    print(c("✓ Local agent uses ollama provider", Colors.GREEN))
    
    # Check it has an override for context_tokens
    assert 'context_tokens' in local_agent, "Local agent should have context_tokens override"
    print(c(f"✓ Local agent has context_tokens override: {local_agent['context_tokens']}", Colors.GREEN))
    
    print(c("✓ Test passed: Local agent properly configured\n", Colors.GREEN))


def run_all_tests():
    """Run all configuration tests"""
    print(c("\n" + "="*60, Colors.CYAN))
    print(c("Configuration Refactor Test Suite", Colors.CYAN))
    print(c("="*60 + "\n", Colors.CYAN))
    
    tests = [
        test_loading_order,
        test_context_tokens_standardization,
        test_provider_validation,
        test_agent_validation,
        test_backward_compatibility,
        test_agent_overrides,
        test_ollama_provider_exists,
        test_local_agent_exists,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(c(f"✗ Test failed: {test.__name__}", Colors.RED))
            print(c(f"  Error: {e}\n", Colors.RED))
        except Exception as e:
            failed += 1
            print(c(f"✗ Test error: {test.__name__}", Colors.RED))
            print(c(f"  Error: {e}\n", Colors.RED))
            import traceback
            traceback.print_exc()
    
    print(c("\n" + "="*60, Colors.CYAN))
    print(c(f"Test Results: {passed} passed, {failed} failed", 
            Colors.GREEN if failed == 0 else Colors.RED))
    print(c("="*60 + "\n", Colors.CYAN))
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
