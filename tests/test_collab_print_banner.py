#!/usr/bin/env python3
"""
Test suite for CollaborativeSession.print_banner() method.

Verifies that the print_banner method correctly displays agent information
without errors, particularly checking that context_tokens is properly retrieved.
"""
import os
import sys
import tempfile
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from axe import CollaborativeSession, Config, AgentManager, SharedWorkspace
from database.agent_db import AgentDatabase


def create_test_session(tmpdir, agent_names=None, with_agent_states=False):
    """Create a minimal test session for testing print_banner."""
    if agent_names is None:
        agent_names = ['grok', 'grok_code']
    
    config = Config()
    db_path = os.path.join(tmpdir, 'test.db')
    
    # Create a minimal session object with required attributes
    session = object.__new__(CollaborativeSession)
    session.config = config
    session.agent_mgr = AgentManager(config)
    session.workspace = SharedWorkspace(tmpdir)
    session.db = AgentDatabase(db_path)
    session.agents = agent_names
    session.agent_ids = {name: f'{name}-id' for name in agent_names}
    session.agent_aliases = {name: f'@{name}' for name in agent_names}
    session.spawned_agents = {}
    session.time_limit = 240
    
    # Optionally initialize agent states in database
    if with_agent_states:
        for agent_name in agent_names:
            agent_id = session.agent_ids[agent_name]
            # Save a minimal agent state
            session.db.save_agent_state(
                agent_id=agent_id,
                alias=f'@{agent_name}',
                model_name=agent_name,
                memory_dict={},
                diffs=[],
                error_count=0,
                xp=1000,
                level=5
            )
    
    return session


def test_print_banner_no_ctx_window_error():
    """Test that print_banner does not raise NameError for ctx_window."""
    print("Testing print_banner does not have ctx_window NameError...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir)
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # This should not raise a NameError
            session.print_banner()
            output = sys.stdout.getvalue()
            
            # Verify that output was produced
            assert len(output) > 0, "No output produced"
            assert "COLLABORATIVE SESSION MODE" in output, "Banner header missing"
            assert "PARTICIPATING AGENTS" in output, "Agents section missing"
            
            print("  ✓ print_banner executes without ctx_window error", file=old_stdout)
            
        except NameError as e:
            if 'ctx_window' in str(e):
                sys.stdout = old_stdout
                print(f"  ✗ FAILED: ctx_window NameError still present: {e}")
                raise
            else:
                sys.stdout = old_stdout
                raise
        finally:
            sys.stdout = old_stdout


def test_print_banner_displays_context_tokens():
    """Test that print_banner correctly displays context tokens."""
    print("Testing print_banner displays context tokens...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir, ['claude', 'gpt'], with_agent_states=True)
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            session.print_banner()
            output = sys.stdout.getvalue()
            
            # Check that context information is displayed
            # The exact format is "Context: N tokens"
            assert "Context:" in output, "Context label missing from output"
            assert "tokens" in output, "tokens word missing from output"
            
            # Verify agents are listed
            assert "@claude" in output or "claude" in output, "claude agent missing"
            assert "@gpt" in output or "gpt" in output, "gpt agent missing"
            
            print("  ✓ print_banner displays context tokens correctly", file=old_stdout)
            
        finally:
            sys.stdout = old_stdout


def test_print_banner_handles_missing_context_tokens():
    """Test that print_banner gracefully handles agents without context_tokens."""
    print("Testing print_banner handles missing context tokens...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create session with agents that don't have saved state (new agents)
        session = create_test_session(tmpdir, ['test_agent'], with_agent_states=False)
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Should not crash even if agent config is missing or incomplete
            session.print_banner()
            output = sys.stdout.getvalue()
            
            # Verify basic output structure is present
            assert "PARTICIPATING AGENTS" in output, "Agents section missing"
            
            # For new agents (without state), should show [New Agent]
            assert "[New Agent]" in output, "New Agent indicator missing"
            
            print("  ✓ print_banner handles missing context tokens gracefully", file=old_stdout)
            
        finally:
            sys.stdout = old_stdout


def test_print_banner_with_multiple_agents():
    """Test that print_banner works with multiple agents."""
    print("Testing print_banner with multiple agents...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session = create_test_session(tmpdir, ['grok', 'grok_code', 'claude', 'gpt'])
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            session.print_banner()
            output = sys.stdout.getvalue()
            
            # Verify all agents are listed
            for agent in ['grok', 'grok_code', 'claude', 'gpt']:
                assert f"@{agent}" in output or agent in output, f"Agent {agent} missing from banner"
            
            # Verify workspace and time limit are shown
            assert "Workspace:" in output, "Workspace info missing"
            assert "Time limit:" in output, "Time limit info missing"
            
            print("  ✓ print_banner works with multiple agents", file=old_stdout)
            
        finally:
            sys.stdout = old_stdout


if __name__ == '__main__':
    print("=" * 70)
    print("COLLABORATIVE SESSION PRINT_BANNER TEST SUITE")
    print("=" * 70)
    
    test_print_banner_no_ctx_window_error()
    test_print_banner_displays_context_tokens()
    test_print_banner_handles_missing_context_tokens()
    test_print_banner_with_multiple_agents()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
