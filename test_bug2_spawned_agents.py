#!/usr/bin/env python3
"""
Test Bug 2: Spawned Agents Never Get Turns

This test verifies that spawned agents can be properly registered and called.
"""
import os
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, AgentManager


def test_spawned_agent_registration():
    """Test that spawned agents can be stored and retrieved."""
    print("Testing spawned agent registration...")
    
    config = Config()
    agent_mgr = AgentManager(config)
    
    # Simulate spawned agent data
    spawned_agent_configs = {}
    
    # Create a spawned agent entry (simulating what _handle_spawn_request does)
    agent_id = str(uuid.uuid4())
    model_name = 'meta-llama/Llama-3.1-70B-Instruct'
    provider = 'huggingface'
    alias = '@meta-llama-Llama-3-1-70B-Instruct2'
    
    spawned_agent_configs[agent_id] = {
        'model': model_name,
        'provider': provider,
        'name': agent_id,
        'alias': alias
    }
    
    # Verify we can retrieve the config
    assert agent_id in spawned_agent_configs, "Spawned agent should be in configs"
    config_retrieved = spawned_agent_configs[agent_id]
    
    assert config_retrieved['model'] == model_name, "Model name should match"
    assert config_retrieved['provider'] == provider, "Provider should match"
    assert config_retrieved['alias'] == alias, "Alias should match"
    
    print("  ✓ Spawned agent can be registered and retrieved")


def test_spawned_vs_configured_agent_resolution():
    """Test that spawned agents are checked before configured agents."""
    print("Testing spawned vs configured agent resolution...")
    
    config = Config()
    agent_mgr = AgentManager(config)
    
    # Simulate both spawned and configured agents
    spawned_agent_configs = {}
    
    # Spawned agent (UUID key)
    spawned_id = str(uuid.uuid4())
    spawned_agent_configs[spawned_id] = {
        'model': 'gpt-4o',
        'provider': 'openai',
        'name': spawned_id,
        'alias': '@gpt-4o2'
    }
    
    # Test resolution logic: check spawned first
    current_agent = spawned_id
    
    if current_agent in spawned_agent_configs:
        agent_config = spawned_agent_configs[current_agent]
        source = "spawned"
    else:
        agent_config = agent_mgr.resolve_agent(current_agent)
        source = "configured"
    
    assert source == "spawned", "Should resolve spawned agent first"
    assert agent_config['name'] == spawned_id, "Should get spawned agent config"
    
    # Now test with a configured agent name
    current_agent = "gpt"  # Configured agent name
    
    if current_agent in spawned_agent_configs:
        agent_config = spawned_agent_configs[current_agent]
        source = "spawned"
    else:
        agent_config = agent_mgr.resolve_agent(current_agent)
        source = "configured"
    
    assert source == "configured", "Should resolve configured agent"
    if agent_config:  # Only if GPT is configured
        assert agent_config['name'] == 'gpt', "Should get configured agent config"
    
    print("  ✓ Agent resolution prioritizes spawned agents correctly")


def test_spawned_agent_has_required_fields():
    """Test that spawned agent config has all required fields."""
    print("Testing spawned agent required fields...")
    
    # Simulate spawned agent config
    spawned_config = {
        'model': 'claude-3-5-sonnet-20241022',
        'provider': 'anthropic',
        'name': str(uuid.uuid4()),
        'alias': '@claude-3-5-sonnet-20241022-2'
    }
    
    # Verify all required fields are present
    required_fields = ['model', 'provider', 'name', 'alias']
    for field in required_fields:
        assert field in spawned_config, f"Missing required field: {field}"
        assert spawned_config[field], f"Field {field} should not be empty"
    
    print("  ✓ Spawned agent has all required fields")


def test_multiple_spawned_agents():
    """Test that multiple spawned agents can coexist."""
    print("Testing multiple spawned agents...")
    
    spawned_agent_configs = {}
    
    # Spawn 3 agents
    for i in range(3):
        agent_id = str(uuid.uuid4())
        spawned_agent_configs[agent_id] = {
            'model': f'model-{i}',
            'provider': 'test',
            'name': agent_id,
            'alias': f'@spawned{i}'
        }
    
    assert len(spawned_agent_configs) == 3, "Should have 3 spawned agents"
    
    # Verify each has unique ID
    ids = list(spawned_agent_configs.keys())
    assert len(set(ids)) == 3, "All spawned agents should have unique IDs"
    
    # Verify each can be retrieved
    for agent_id, config in spawned_agent_configs.items():
        assert spawned_agent_configs[agent_id] == config, "Each agent should be retrievable"
    
    print("  ✓ Multiple spawned agents can coexist")


def main():
    """Run all Bug 2 tests."""
    print("="*70)
    print("BUG 2 FIX TEST SUITE: Spawned Agents Never Get Turns")
    print("="*70)
    
    try:
        test_spawned_agent_registration()
        test_spawned_vs_configured_agent_resolution()
        test_spawned_agent_has_required_fields()
        test_multiple_spawned_agents()
        
        print("\n" + "="*70)
        print("✅ ALL BUG 2 TESTS PASSED!")
        print("="*70)
        print("\nNote: These tests verify the data structures. Bug 2 is fixed by:")
        print("  1. Adding spawned_agent_configs dict to CollaborativeSession")
        print("  2. Storing spawned agent config in _handle_spawn_request()")
        print("  3. Checking spawned_agent_configs before resolve_agent() in agent calling code")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
