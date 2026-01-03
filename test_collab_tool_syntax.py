#!/usr/bin/env python3
"""
Test suite for collaborative mode tool syntax instructions.

Verifies that agents in collaborative mode receive proper instructions
for using WRITE, READ, and EXEC blocks.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import CollaborativeSession, Config, AgentManager, SharedWorkspace
from database.agent_db import AgentDatabase


def create_test_session(tmpdir):
    """Create a minimal test session without full initialization."""
    config = Config()
    db_path = os.path.join(tmpdir, 'test.db')
    
    # Create a minimal session object with required attributes
    session = object.__new__(CollaborativeSession)
    session.config = config
    session.agent_mgr = AgentManager(config)
    session.workspace = SharedWorkspace(tmpdir)
    session.db = AgentDatabase(db_path)
    session.agents = ['gpt', 'claude']
    session.agent_ids = {'gpt': 'gpt-id', 'claude': 'claude-id'}
    session.agent_aliases = {'gpt': '@gpt', 'claude': '@claude'}
    session.spawned_agents = {}
    
    return session


def test_collab_prompt_includes_tool_syntax():
    """Test that collaborative mode system prompt includes tool syntax instructions."""
    print("Testing collaborative mode tool syntax instructions...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir)
        
        # Get the system prompt for an agent
        prompt = session._get_system_prompt_for_collab('gpt')
        
        # Verify tool syntax instructions are present
        assert 'WRITE' in prompt, "WRITE block syntax not in prompt"
        assert 'READ' in prompt, "READ block syntax not in prompt"
        assert 'EXEC' in prompt, "EXEC block syntax not in prompt"
        
        # Verify critical warnings are present
        assert 'FILE AND COMMAND OPERATIONS' in prompt, "Tool operations section missing"
        assert 'CRITICAL' in prompt, "Critical warning not in prompt"
        
        # Verify examples are present
        assert '```WRITE' in prompt, "WRITE block example not in prompt"
        assert '```READ' in prompt, "READ block example not in prompt"
        assert '```EXEC' in prompt, "EXEC block example not in prompt"
        
        # Verify warning about describing vs executing
        assert 'NOTHING HAPPENS' in prompt or 'does NOTHING' in prompt, "Warning about non-execution missing"
        
        print("  ✓ Collaborative system prompt includes tool syntax")


def test_collab_prompt_has_clear_examples():
    """Test that the prompt includes clear examples of correct usage."""
    print("Testing collaborative mode prompt examples...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir)
        
        prompt = session._get_system_prompt_for_collab('gpt')
        
        # Check for distinction between wrong and right approaches
        assert '❌' in prompt or 'WRONG' in prompt, "Wrong example marker not found"
        assert '✅' in prompt or 'RIGHT' in prompt, "Right example marker not found"
        
        # Check that the examples show the actual syntax
        assert 'filename.txt' in prompt or 'hello.py' in prompt, "Example filename not found"
        
        print("  ✓ Collaborative prompt includes clear examples")


def test_collab_prompt_preserves_existing_features():
    """Test that the updated prompt still includes all existing features."""
    print("Testing that existing collaborative features are preserved...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir)
        
        prompt = session._get_system_prompt_for_collab('gpt')
        
        # Verify existing features are still present
        assert 'COLLABORATION RULES' in prompt, "Collaboration rules section missing"
        assert 'SPECIAL COMMANDS' in prompt, "Special commands section missing"
        assert 'WORKSPACE INFO' in prompt, "Workspace info section missing"
        assert '[[AGENT_PASS_TURN]]' in prompt, "Pass turn token missing"
        assert '[[AGENT_TASK_COMPLETE:' in prompt, "Task complete token missing"
        
        print("  ✓ Existing collaborative features preserved")


def test_multiple_agents_get_tool_instructions():
    """Test that all agents in a session get the tool syntax instructions."""
    print("Testing that all agents receive tool instructions...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir)
        session.agents = ['gpt', 'claude', 'grok']
        session.agent_ids = {'gpt': 'gpt-id', 'claude': 'claude-id', 'grok': 'grok-id'}
        session.agent_aliases = {'gpt': '@gpt', 'claude': '@claude', 'grok': '@grok'}
        
        for agent_name in ['gpt', 'claude', 'grok']:
            prompt = session._get_system_prompt_for_collab(agent_name)
            
            assert 'WRITE' in prompt, f"Agent {agent_name} missing WRITE syntax"
            assert 'READ' in prompt, f"Agent {agent_name} missing READ syntax"
            assert 'EXEC' in prompt, f"Agent {agent_name} missing EXEC syntax"
            assert 'FILE AND COMMAND OPERATIONS' in prompt, f"Agent {agent_name} missing tool operations section"
        
        print("  ✓ All agents receive tool syntax instructions")


if __name__ == '__main__':
    print("=" * 70)
    print("COLLABORATIVE MODE TOOL SYNTAX TEST SUITE")
    print("=" * 70)
    
    test_collab_prompt_includes_tool_syntax()
    test_collab_prompt_has_clear_examples()
    test_collab_prompt_preserves_existing_features()
    test_multiple_agents_get_tool_instructions()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
