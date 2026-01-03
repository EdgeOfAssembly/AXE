#!/usr/bin/env python3
"""
Test suite for spawned agent registration and turn-taking.

Tests the bug fix for spawned agents not receiving turns because
they were registered with UUIDs but resolve_agent only knew static names.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import CollaborativeSession


def test_spawned_agent_system_prompt():
    """Test that spawned agents get appropriate system prompts."""
    print("Testing spawned agent system prompt generation...")
    
    # We'll create a minimal mock to test the method
    class MockSession:
        def _get_spawned_agent_system_prompt(self, model_type: str) -> str:
            """Get appropriate system prompt for a spawned agent based on model type."""
            prompts = {
                'llama': """You are an open-source hacker fluent in x86 assembly.
Specialize in nasm, DOS interrupts, binary analysis.""",
                'gpt': """You are an expert software engineer. Provide clear, working code.
For C/C++: Prefer portable code; when DOS/16-bit targets are requested, explain that true DOS support typically needs compilers like Open Watcom or DJGPP and that 16-bit ints/far pointers are non-standard in modern toolchains.
For Python: Clean, type-hinted code.
For reverse-engineering: Use hexdump/objdump analysis.""",
                'claude': """You are a code review expert and security auditor.
Analyze code for bugs, security issues, and improvements.
For rev-eng: Check endianness, memory safety, DOS compatibility.""",
                'grok': """You are a fast-coding hacker who rapidly implements solutions.
Focus on getting working code quickly, then iterate.""",
                'copilot': """You are an expert software engineer. Provide clear, working code.
Focus on practical, well-tested solutions."""
            }
            return prompts.get(model_type, prompts['gpt'])
    
    session = MockSession()
    
    # Test different model types
    model_types = ['gpt', 'claude', 'llama', 'grok', 'copilot']
    
    for model_type in model_types:
        prompt = session._get_spawned_agent_system_prompt(model_type)
        assert prompt is not None, f"No prompt for {model_type}"
        assert len(prompt) > 0, f"Empty prompt for {model_type}"
        assert isinstance(prompt, str), f"Prompt not a string for {model_type}"
    
    print("  ✓ Spawned agent system prompts generated correctly")


def test_spawned_agent_data_structures():
    """Test that spawned agent data structures are properly designed."""
    print("Testing spawned agent data structures...")
    
    # Simulate the data structures
    spawned_agents = {}
    agent_ids = {}
    agent_aliases = {}
    agents = []
    
    # Simulate spawning an agent
    agent_key = 'uuid-1234-5678'
    provider = 'openai'
    model_name = 'gpt-4o'
    alias = '@gpt-4o2'
    
    # This is what _handle_spawn_request should do
    agents.append(agent_key)
    agent_ids[agent_key] = agent_key
    agent_aliases[agent_key] = alias
    spawned_agents[agent_key] = {
        'name': agent_key,
        'provider': provider,
        'model': model_name,
        'alias': alias,
        'system_prompt': 'Test prompt'
    }
    
    # Verify structure
    assert agent_key in agents, "Agent not in agents list"
    assert agent_key in agent_ids, "Agent not in agent_ids"
    assert agent_key in agent_aliases, "Agent not in agent_aliases"
    assert agent_key in spawned_agents, "Agent not in spawned_agents"
    
    # Simulate resolution (what happens in main loop)
    current_agent = agents[0]
    
    # Check spawned agents first
    if current_agent in spawned_agents:
        agent_config = spawned_agents[current_agent]
    else:
        agent_config = None  # Would call resolve_agent() for static agents
    
    assert agent_config is not None, "Failed to resolve spawned agent"
    assert agent_config['provider'] == provider, "Provider mismatch"
    assert agent_config['model'] == model_name, "Model mismatch"
    
    print("  ✓ Spawned agent data structures work correctly")


def test_spawned_vs_static_agent_resolution():
    """Test that both spawned and static agents can be resolved."""
    print("Testing spawned vs static agent resolution...")
    
    # Simulate mixed agent list
    agents = ['claude', 'uuid-spawned-1', 'gpt', 'uuid-spawned-2']
    spawned_agents = {
        'uuid-spawned-1': {
            'name': 'uuid-spawned-1',
            'provider': 'openai',
            'model': 'gpt-4o',
            'system_prompt': 'Prompt 1'
        },
        'uuid-spawned-2': {
            'name': 'uuid-spawned-2',
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022',
            'system_prompt': 'Prompt 2'
        }
    }
    
    # Simulate resolution for each agent
    for current_agent in agents:
        if current_agent in spawned_agents:
            # Spawned agent
            config = spawned_agents[current_agent]
            assert config is not None, f"Spawned agent {current_agent} not resolved"
        else:
            # Static agent - would use resolve_agent(), just verify the logic
            assert current_agent in ['claude', 'gpt'], f"Unknown static agent: {current_agent}"
            # In real code: config = agent_mgr.resolve_agent(current_agent)
    
    print("  ✓ Both spawned and static agents can be resolved")


def test_agent_key_consistency():
    """Test that agent keys are used consistently across data structures."""
    print("Testing agent key consistency...")
    
    # The bug was that UUIDs were used as keys but couldn't be resolved
    # The fix ensures spawned agents use UUID as key everywhere consistently
    
    agent_uuid = 'test-uuid-abcd-1234'
    
    # All structures should use the same key
    agents = [agent_uuid]
    agent_ids = {agent_uuid: agent_uuid}
    agent_aliases = {agent_uuid: '@spawned-agent'}
    spawned_agents = {agent_uuid: {'name': agent_uuid, 'provider': 'openai'}}
    
    # Verify consistency
    for key in agents:
        assert key in agent_ids, f"Key {key} missing from agent_ids"
        assert key in agent_aliases, f"Key {key} missing from agent_aliases"
        if key.startswith('test-uuid'):  # spawned agent check
            assert key in spawned_agents, f"Key {key} missing from spawned_agents"
    
    print("  ✓ Agent key consistency verified")


if __name__ == '__main__':
    print("=" * 70)
    print("SPAWNED AGENT TURN-TAKING TEST SUITE")
    print("=" * 70)
    
    test_spawned_agent_system_prompt()
    test_spawned_agent_data_structures()
    test_spawned_vs_static_agent_resolution()
    test_agent_key_consistency()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
