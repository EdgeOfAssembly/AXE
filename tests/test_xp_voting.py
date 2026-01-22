#!/usr/bin/env python3
"""
Test suite for XP Voting System (Minsky's Society of Mind).

Tests peer voting mechanics:
- Vote limits by level
- Self-vote prevention
- Session vote limits
- Positive/negative vote bounds
- Vote application to database
- Level-up from peer votes
- Vote history retrieval
"""

import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.global_workspace import GlobalWorkspace, VOTE_LIMITS, MAX_VOTES_PER_SESSION
from database.agent_db import AgentDatabase
from progression.xp_system import XP_AWARDS


def test_vote_limits_by_level():
    """Test that vote limits are enforced based on voter level."""
    print("Testing vote limits by level...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        # Test Worker (Level 5) - max +10, -5
        result = ws.vote_xp('@worker', 5, '@target', 10, 'Good work')
        assert result['success'], "Worker should be able to vote +10"
        print("  ✓ Worker L5 can vote +10")
        
        result = ws.vote_xp('@worker', 5, '@target', 11, 'Great work')
        assert not result['success'], "Worker should not exceed +10 limit"
        assert 'exceeds positive limit' in result['error']
        print("  ✓ Worker L5 cannot vote +11 (limit enforced)")
        
        result = ws.vote_xp('@worker', 5, '@target', -5, 'Poor work')
        assert result['success'], "Worker should be able to vote -5"
        print("  ✓ Worker L5 can vote -5")
        
        result = ws.vote_xp('@worker', 5, '@target', -6, 'Bad work')
        assert not result['success'], "Worker should not exceed -5 limit"
        assert 'exceeds negative limit' in result['error']
        print("  ✓ Worker L5 cannot vote -6 (limit enforced)")
        
        # Test Team Leader (Level 15) - max +15, -5
        ws.reset_vote_limits()  # Reset for new voter
        result = ws.vote_xp('@leader', 15, '@target', 15, 'Excellent')
        assert result['success'], "Team Leader should be able to vote +15"
        print("  ✓ Team Leader L15 can vote +15")
        
        result = ws.vote_xp('@leader', 15, '@target', 16, 'Outstanding')
        assert not result['success'], "Team Leader should not exceed +15 limit"
        print("  ✓ Team Leader L15 cannot vote +16 (limit enforced)")
        
        # Test Deputy (Level 25) - max +20, -10
        ws.reset_vote_limits()
        result = ws.vote_xp('@deputy', 25, '@target', 20, 'Superior')
        assert result['success'], "Deputy should be able to vote +20"
        print("  ✓ Deputy L25 can vote +20")
        
        result = ws.vote_xp('@deputy', 25, '@target', -10, 'Serious issue')
        assert result['success'], "Deputy should be able to vote -10"
        print("  ✓ Deputy L25 can vote -10")
        
        # Test Supervisor (Level 35) - max +25, -15
        ws.reset_vote_limits()
        result = ws.vote_xp('@supervisor', 35, '@target', 25, 'Exceptional')
        assert result['success'], "Supervisor should be able to vote +25"
        print("  ✓ Supervisor L35 can vote +25")
        
        result = ws.vote_xp('@supervisor', 35, '@target', -15, 'Major problem')
        assert result['success'], "Supervisor should be able to vote -15"
        print("  ✓ Supervisor L35 can vote -15")
    
    print()


def test_self_vote_prevention():
    """Test that agents cannot vote for themselves."""
    print("Testing self-vote prevention...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        # Try to vote for self
        result = ws.vote_xp('@agent1', 10, '@agent1', 10, 'I am great')
        assert not result['success'], "Should not be able to vote for yourself"
        assert 'Cannot vote for yourself' in result['error']
        print("  ✓ Self-vote prevented")
        
        # Also test without @ prefix
        result = ws.vote_xp('agent2', 10, 'agent2', 10, 'I am great')
        assert not result['success'], "Should not be able to vote for yourself (no @ prefix)"
        print("  ✓ Self-vote prevented (no @ prefix)")
    
    print()


def test_session_vote_limits():
    """Test that agents can only cast limited votes per session."""
    print("Testing session vote limits...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        # Cast maximum votes
        for i in range(MAX_VOTES_PER_SESSION):
            result = ws.vote_xp('@voter', 10, f'@target{i}', 5, f'Reason {i}')
            assert result['success'], f"Vote {i+1} should succeed"
            assert result['votes_remaining'] == MAX_VOTES_PER_SESSION - (i + 1)
            print(f"  ✓ Vote {i+1}/{MAX_VOTES_PER_SESSION} cast successfully")
        
        # Try one more - should fail
        result = ws.vote_xp('@voter', 10, '@target_extra', 5, 'Extra vote')
        assert not result['success'], "Should not exceed vote limit"
        assert 'Vote limit reached' in result['error']
        print(f"  ✓ Vote limit ({MAX_VOTES_PER_SESSION}) enforced")
        
        # Reset and verify can vote again
        ws.reset_vote_limits()
        result = ws.vote_xp('@voter', 10, '@target_new', 5, 'After reset')
        assert result['success'], "Should be able to vote after reset"
        print("  ✓ Vote limits reset successfully")
    
    print()


def test_vote_history():
    """Test vote history retrieval."""
    print("Testing vote history...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        # Cast various votes
        ws.vote_xp('@agent1', 10, '@agent2', 10, 'Good job')
        ws.vote_xp('@agent2', 15, '@agent3', 5, 'Nice work')
        ws.vote_xp('@agent3', 20, '@agent1', 15, 'Excellent')
        
        # Get all history
        all_votes = ws.get_vote_history()
        assert len(all_votes) == 3, f"Should have 3 votes, got {len(all_votes)}"
        print("  ✓ All vote history retrieved")
        
        # Get filtered by agent1 (as voter or target)
        agent1_votes = ws.get_vote_history('@agent1')
        assert len(agent1_votes) == 2, f"agent1 should have 2 related votes, got {len(agent1_votes)}"
        print("  ✓ Filtered vote history works")
        
        # Get vote summary
        summary = ws.get_vote_summary()
        assert summary['@agent2'] == 10, "agent2 should have +10 net XP"
        assert summary['@agent3'] == 5, "agent3 should have +5 net XP"
        assert summary['@agent1'] == 15, "agent1 should have +15 net XP"
        print("  ✓ Vote summary calculated correctly")
    
    print()


def test_vote_application_to_database():
    """Test applying votes to agent database."""
    print("Testing vote application to database...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test database
        db_path = os.path.join(tmpdir, 'test_agents.db')
        db = AgentDatabase(db_path)
        
        # Create test agents
        agent1_id = 'agent_1'
        agent2_id = 'agent_2'
        
        db.save_agent_state(agent1_id, 'claude', 'claude-3-5-sonnet',
                           {}, [], 0, 100, 5)
        db.save_agent_state(agent2_id, 'llama', 'llama-3.1-70b',
                           {}, [], 0, 200, 8)
        
        # Create workspace with votes
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        ws.vote_xp('@llama', 8, '@claude', 10, 'Excellent analysis')
        ws.vote_xp('@claude', 5, '@llama', 8, 'Good suggestions')
        
        # Get pending votes
        pending = ws.get_pending_votes()
        assert len(pending) == 2, f"Should have 2 pending votes, got {len(pending)}"
        print("  ✓ Pending votes tracked")
        
        # Apply votes
        results = db.apply_xp_votes(pending)
        assert len(results) == 2, f"Should have 2 results, got {len(results)}"
        
        # Check results
        for result in results:
            assert result['success'], f"Vote application should succeed: {result}"
        
        print("  ✓ Votes applied successfully")
        
        # Verify XP was updated
        agent1_info = db.get_agent_by_alias('claude')
        assert agent1_info is not None, "claude should exist"
        assert agent1_info['xp'] == 110, f"claude should have 110 XP, got {agent1_info['xp']}"
        print(f"  ✓ claude XP updated: 100 → {agent1_info['xp']}")
        
        agent2_info = db.get_agent_by_alias('llama')
        assert agent2_info is not None, "llama should exist"
        assert agent2_info['xp'] == 208, f"llama should have 208 XP, got {agent2_info['xp']}"
        print(f"  ✓ llama XP updated: 200 → {agent2_info['xp']}")
        
        # Mark votes as applied
        for vote in pending:
            ws.mark_vote_applied(vote['id'])
        
        # Verify no more pending
        pending_after = ws.get_pending_votes()
        assert len(pending_after) == 0, f"Should have 0 pending votes after marking, got {len(pending_after)}"
        print("  ✓ Votes marked as applied")
    
    print()


def test_level_up_from_votes():
    """Test that peer votes can trigger level-ups."""
    print("Testing level-up from peer votes...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_agents.db')
        db = AgentDatabase(db_path)
        
        # Create agent close to level-up (Level 2 needs 100 XP total)
        agent_id = 'agent_1'
        db.save_agent_state(agent_id, 'claude', 'claude-3-5-sonnet',
                           {}, [], 0, 95, 1)  # 95 XP, Level 1
        
        # Create workspace and vote
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        # Vote to push over the edge
        ws.vote_xp('@llama', 10, '@claude', 10, 'Pushed you to level 2!')
        
        # Apply votes
        pending = ws.get_pending_votes()
        results = db.apply_xp_votes(pending)
        
        # Check for level-up
        result = results[0]
        assert result['success'], "Vote application should succeed"
        assert result['leveled_up'], "Should trigger level-up"
        assert result['old_level'] == 1, "Old level should be 1"
        assert result['new_level'] == 2, "New level should be 2"
        assert result['xp'] == 105, f"XP should be 105, got {result['xp']}"
        
        print(f"  ✓ Level-up triggered: Level {result['old_level']} → {result['new_level']}")
        print(f"  ✓ XP: 95 → {result['xp']}")
        print(f"  ✓ New title: {result.get('new_title', 'N/A')}")
    
    print()


def test_negative_votes():
    """Test that negative votes (penalties) work correctly."""
    print("Testing negative votes...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_agents.db')
        db = AgentDatabase(db_path)
        
        # Create agent with some XP
        agent_id = 'agent_1'
        db.save_agent_state(agent_id, 'grok', 'grok-beta',
                           {}, [], 0, 100, 2)
        
        # Create workspace and vote negative
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        ws.vote_xp('@claude', 15, '@grok', -5, 'Poor suggestion')
        
        # Apply votes
        pending = ws.get_pending_votes()
        results = db.apply_xp_votes(pending)
        
        # Check result
        result = results[0]
        assert result['success'], "Negative vote should be applied"
        assert result['xp'] == 95, f"XP should be reduced to 95, got {result['xp']}"
        
        print(f"  ✓ Negative vote applied: 100 XP → {result['xp']}")
    
    print()


def test_xp_awards_exist():
    """Test that peer voting XP awards are defined."""
    print("Testing XP award definitions...")
    
    required_awards = [
        'peer_endorsement',
        'peer_strong_endorsement',
        'peer_penalty',
        'conflict_resolution',
        'arbitration_win'
    ]
    
    for award in required_awards:
        assert award in XP_AWARDS, f"{award} should be in XP_AWARDS"
        print(f"  ✓ {award}: {XP_AWARDS[award]} XP")
    
    # Check values
    assert XP_AWARDS['peer_endorsement'] == 10
    assert XP_AWARDS['peer_strong_endorsement'] == 20
    assert XP_AWARDS['peer_penalty'] == -5
    assert XP_AWARDS['conflict_resolution'] == 15
    assert XP_AWARDS['arbitration_win'] == 25
    
    print("  ✓ All peer voting XP awards defined correctly")
    print()


def test_workspace_persistence():
    """Test that workspace state persists to file."""
    print("Testing workspace persistence...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        
        # Create workspace and add votes
        ws1 = GlobalWorkspace(workspace_file)
        ws1.vote_xp('@agent1', 10, '@agent2', 10, 'Good work')
        ws1.vote_xp('@agent2', 15, '@agent3', 8, 'Nice')
        
        # Load in new instance
        ws2 = GlobalWorkspace(workspace_file)
        votes = ws2.get_vote_history()
        
        assert len(votes) == 2, f"Should load 2 votes, got {len(votes)}"
        print("  ✓ Votes persisted to file")
        
        # Check vote limits persisted
        assert '@agent1' in ws2.data['vote_limits']
        assert '@agent2' in ws2.data['vote_limits']
        print("  ✓ Vote limits persisted")
    
    print()


def test_broadcast_system():
    """Test the broadcast messaging system."""
    print("Testing broadcast system...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        ws = GlobalWorkspace(workspace_file)
        
        # Send broadcasts
        bc1 = ws.broadcast('XP_VOTE', '@agent1', 'I voted for @agent2')
        bc2 = ws.broadcast('STATUS', '@agent2', 'Analysis complete', {'status': 'done'})
        bc3 = ws.broadcast('XP_VOTE', '@agent3', 'Another vote')
        
        # Get all broadcasts
        all_bc = ws.get_broadcasts()
        assert len(all_bc) == 3, f"Should have 3 broadcasts, got {len(all_bc)}"
        print("  ✓ Broadcasts stored")
        
        # Get filtered by category
        xp_bc = ws.get_broadcasts(category='XP_VOTE')
        assert len(xp_bc) == 2, f"Should have 2 XP_VOTE broadcasts, got {len(xp_bc)}"
        print("  ✓ Broadcast filtering works")
        
        # Check ordering (most recent first)
        assert xp_bc[0]['sender'] == '@agent3', "Most recent should be first"
        print("  ✓ Broadcasts ordered correctly (newest first)")
    
    print()


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("XP VOTING SYSTEM TEST SUITE")
    print("Minsky's Society of Mind - Peer Reputation")
    print("=" * 60)
    print()
    
    tests = [
        test_xp_awards_exist,
        test_vote_limits_by_level,
        test_self_vote_prevention,
        test_session_vote_limits,
        test_vote_history,
        test_vote_application_to_database,
        test_level_up_from_votes,
        test_negative_votes,
        test_workspace_persistence,
        test_broadcast_system,
    ]
    
    failed = []
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ FAILED: {test.__name__}")
            print(f"  Error: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ ERROR: {test.__name__}")
            print(f"  Error: {e}")
            failed.append(test.__name__)
    
    print("=" * 60)
    if failed:
        print(f"FAILED: {len(failed)} test(s)")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print("SUCCESS: All tests passed!")
        return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
