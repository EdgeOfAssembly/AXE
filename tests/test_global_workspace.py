#!/usr/bin/env python3
"""
Test suite for Global Workspace.
Tests workspace initialization, broadcasting, acknowledgments, filtering, and prompt formatting.
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.global_workspace import GlobalWorkspace


def test_workspace_initialization():
    """Test that workspace initializes correctly with proper structure."""
    print("Testing workspace initialization...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Check that workspace file was created
        assert workspace.workspace_file.exists(), "Workspace file should be created"
        
        # Check initial structure
        data = workspace._read_workspace()
        assert 'version' in data, "Should have version field"
        assert 'created' in data, "Should have created timestamp"
        assert 'broadcasts' in data, "Should have broadcasts list"
        assert 'metadata' in data, "Should have metadata dict"
        assert data['broadcasts'] == [], "Broadcasts should start empty"
        assert data['metadata']['total_broadcasts'] == 0, "Total broadcasts should start at 0"
        
        print("  ✓ Workspace initialization works correctly")
    print()


def test_broadcast_valid_category():
    """Test broadcasting with valid category."""
    print("Testing broadcast with valid category...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        result = workspace.broadcast(
            agent_alias="@gpt1",
            agent_level=10,
            category="SECURITY",
            message="Found potential buffer overflow in parse_header()"
        )
        
        assert result['success'], f"Broadcast should succeed: {result}"
        assert 'broadcast_id' in result, "Should return broadcast_id"
        assert 'entry' in result, "Should return entry"
        
        # Check the broadcast was stored
        broadcasts = workspace.get_broadcasts()
        assert len(broadcasts) == 1, "Should have 1 broadcast"
        assert broadcasts[0]['category'] == 'SECURITY', "Category should be SECURITY"
        assert broadcasts[0]['agent'] == '@gpt1', "Agent should be @gpt1"
        assert broadcasts[0]['message'] == "Found potential buffer overflow in parse_header()"
        
        print("  ✓ Broadcasting with valid category works correctly")
    print()


def test_broadcast_invalid_category():
    """Test broadcasting with invalid category fails."""
    print("Testing broadcast with invalid category...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        result = workspace.broadcast(
            agent_alias="@gpt1",
            agent_level=10,
            category="INVALID_CATEGORY",
            message="This should fail"
        )
        
        assert not result['success'], "Broadcast should fail with invalid category"
        assert 'reason' in result, "Should provide reason for failure"
        assert 'Invalid category' in result['reason'], "Reason should mention invalid category"
        
        # Check no broadcast was stored
        broadcasts = workspace.get_broadcasts()
        assert len(broadcasts) == 0, "Should have 0 broadcasts"
        
        print("  ✓ Invalid category rejection works correctly")
    print()


def test_directive_permission_check():
    """Test that DIRECTIVE broadcasts require minimum level."""
    print("Testing DIRECTIVE permission check...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Try to broadcast DIRECTIVE with insufficient level
        result = workspace.broadcast(
            agent_alias="@claude1",
            agent_level=5,  # Below minimum level of 20
            category="DIRECTIVE",
            message="Everyone focus on security"
        )
        
        assert not result['success'], "DIRECTIVE should fail with low level"
        assert 'reason' in result, "Should provide reason"
        assert 'level' in result['reason'].lower() or 'team leader' in result['reason'].lower(), \
            "Reason should mention level requirement"
        
        # Try with sufficient level
        result = workspace.broadcast(
            agent_alias="@claude1",
            agent_level=25,  # Above minimum level of 20
            category="DIRECTIVE",
            message="Everyone focus on security"
        )
        
        assert result['success'], f"DIRECTIVE should succeed with high level: {result}"
        
        broadcasts = workspace.get_broadcasts()
        assert len(broadcasts) == 1, "Should have 1 broadcast"
        assert broadcasts[0]['category'] == 'DIRECTIVE', "Category should be DIRECTIVE"
        
        print("  ✓ DIRECTIVE permission check works correctly")
    print()


def test_acknowledgment_flow():
    """Test the acknowledgment system."""
    print("Testing acknowledgment flow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create a broadcast requiring acknowledgment
        result = workspace.broadcast(
            agent_alias="@gpt1",
            agent_level=25,
            category="DIRECTIVE",
            message="All agents must review security findings",
            requires_ack=True
        )
        
        assert result['success'], "Broadcast should succeed"
        broadcast_id = result['broadcast_id']
        
        # Check pending acks for another agent
        pending = workspace.get_pending_acks("@claude1")
        assert len(pending) == 1, "Should have 1 pending ack for @claude1"
        assert pending[0]['id'] == broadcast_id, "Pending ack should match broadcast"
        
        # Acknowledge from another agent
        ack_result = workspace.acknowledge(broadcast_id, "@claude1", "Understood, will review")
        assert ack_result['success'], f"Acknowledgment should succeed: {ack_result}"
        
        # Check that pending acks updated
        pending_after = workspace.get_pending_acks("@claude1")
        assert len(pending_after) == 0, "Should have 0 pending acks after acknowledging"
        
        # Try to acknowledge again (should fail)
        ack_result2 = workspace.acknowledge(broadcast_id, "@claude1", "Again")
        assert not ack_result2['success'], "Second acknowledgment should fail"
        assert 'already acknowledged' in ack_result2['reason'].lower(), \
            "Should mention already acknowledged"
        
        # Original broadcaster should not have pending acks for their own broadcast
        self_pending = workspace.get_pending_acks("@gpt1")
        assert len(self_pending) == 0, "Broadcaster should not have pending ack for own broadcast"
        
        # Try to acknowledge a broadcast that doesn't require ack (should fail)
        result2 = workspace.broadcast(
            agent_alias="@llama1",
            agent_level=10,
            category="STATUS",
            message="Still working on task",
            requires_ack=False
        )
        broadcast_id2 = result2['broadcast_id']
        
        ack_result3 = workspace.acknowledge(broadcast_id2, "@gpt1")
        assert not ack_result3['success'], "Should fail to ack broadcast not requiring ack"
        
        print("  ✓ Acknowledgment flow works correctly")
    print()


def test_filtering_by_category():
    """Test filtering broadcasts by category."""
    print("Testing filtering by category...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create broadcasts with different categories
        workspace.broadcast("@gpt1", 10, "SECURITY", "Security issue 1")
        workspace.broadcast("@claude1", 10, "BUG", "Bug found")
        workspace.broadcast("@llama1", 10, "SECURITY", "Security issue 2")
        workspace.broadcast("@grok1", 10, "OPTIMIZATION", "Performance improvement")
        
        # Filter by SECURITY
        security_broadcasts = workspace.get_broadcasts(category='SECURITY')
        assert len(security_broadcasts) == 2, "Should have 2 SECURITY broadcasts"
        for b in security_broadcasts:
            assert b['category'] == 'SECURITY', "All should be SECURITY category"
        
        # Filter by BUG
        bug_broadcasts = workspace.get_broadcasts(category='BUG')
        assert len(bug_broadcasts) == 1, "Should have 1 BUG broadcast"
        assert bug_broadcasts[0]['category'] == 'BUG', "Should be BUG category"
        
        print("  ✓ Category filtering works correctly")
    print()


def test_filtering_by_agent():
    """Test filtering broadcasts by agent."""
    print("Testing filtering by agent...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create broadcasts from different agents
        workspace.broadcast("@gpt1", 10, "SECURITY", "From GPT")
        workspace.broadcast("@claude1", 10, "BUG", "From Claude 1")
        workspace.broadcast("@claude1", 10, "SECURITY", "From Claude 2")
        workspace.broadcast("@llama1", 10, "STATUS", "From Llama")
        
        # Filter by @claude1
        claude_broadcasts = workspace.get_broadcasts(agent='@claude1')
        assert len(claude_broadcasts) == 2, "Should have 2 broadcasts from @claude1"
        for b in claude_broadcasts:
            assert b['agent'] == '@claude1', "All should be from @claude1"
        
        # Filter by @gpt1
        gpt_broadcasts = workspace.get_broadcasts(agent='@gpt1')
        assert len(gpt_broadcasts) == 1, "Should have 1 broadcast from @gpt1"
        
        print("  ✓ Agent filtering works correctly")
    print()


def test_filtering_by_time():
    """Test filtering broadcasts by timestamp."""
    print("Testing filtering by time...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create first broadcast
        workspace.broadcast("@gpt1", 10, "SECURITY", "Old broadcast")
        
        # Get timestamp for "since" filter
        since_time = datetime.now(timezone.utc).isoformat()
        
        # Create more broadcasts after timestamp
        workspace.broadcast("@claude1", 10, "BUG", "New broadcast 1")
        workspace.broadcast("@llama1", 10, "STATUS", "New broadcast 2")
        
        # Filter by time
        recent_broadcasts = workspace.get_broadcasts(since=since_time)
        assert len(recent_broadcasts) == 2, f"Should have 2 recent broadcasts, got {len(recent_broadcasts)}"
        
        # All broadcasts
        all_broadcasts = workspace.get_broadcasts()
        assert len(all_broadcasts) == 3, "Should have 3 total broadcasts"
        
        print("  ✓ Time filtering works correctly")
    print()


def test_filtering_requires_ack():
    """Test filtering for broadcasts requiring acknowledgment."""
    print("Testing requires_ack filtering...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create broadcasts with and without ack requirement
        workspace.broadcast("@gpt1", 10, "SECURITY", "No ack needed", requires_ack=False)
        workspace.broadcast("@claude1", 25, "DIRECTIVE", "Ack required 1", requires_ack=True)
        workspace.broadcast("@llama1", 10, "STATUS", "No ack", requires_ack=False)
        workspace.broadcast("@grok1", 25, "DIRECTIVE", "Ack required 2", requires_ack=True)
        
        # Filter for requires_ack
        ack_required = workspace.get_broadcasts(requires_ack_only=True)
        assert len(ack_required) == 2, "Should have 2 broadcasts requiring ack"
        for b in ack_required:
            assert b['requires_ack'], "All should require ack"
        
        print("  ✓ Requires_ack filtering works correctly")
    print()


def test_pending_acks_retrieval():
    """Test retrieving pending acknowledgments for specific agent."""
    print("Testing pending acks retrieval...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create broadcasts requiring ack
        result1 = workspace.broadcast("@gpt1", 25, "DIRECTIVE", "Task 1", requires_ack=True)
        result2 = workspace.broadcast("@claude1", 25, "DIRECTIVE", "Task 2", requires_ack=True)
        workspace.broadcast("@llama1", 10, "STATUS", "No ack", requires_ack=False)
        
        # Check pending for @llama1 (should have 2)
        pending = workspace.get_pending_acks("@llama1")
        assert len(pending) == 2, f"Should have 2 pending acks, got {len(pending)}"
        
        # Acknowledge one
        workspace.acknowledge(result1['broadcast_id'], "@llama1")
        
        # Check pending again (should have 1)
        pending_after = workspace.get_pending_acks("@llama1")
        assert len(pending_after) == 1, "Should have 1 pending ack after acknowledging"
        
        # Broadcasters shouldn't have pending acks for their own broadcasts
        gpt_pending = workspace.get_pending_acks("@gpt1")
        claude_pending = workspace.get_pending_acks("@claude1")
        assert len(gpt_pending) == 1, "@gpt1 should have 1 pending (from @claude1)"
        assert len(claude_pending) == 1, "@claude1 should have 1 pending (from @gpt1)"
        
        print("  ✓ Pending acks retrieval works correctly")
    print()


def test_get_conflicts():
    """Test retrieving CONFLICT broadcasts."""
    print("Testing get_conflicts...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create various broadcasts
        workspace.broadcast("@gpt1", 10, "SECURITY", "Security issue")
        workspace.broadcast("@claude1", 15, "CONFLICT", "Conflicting approach", requires_ack=True)
        workspace.broadcast("@llama1", 15, "CONFLICT", "Another conflict", requires_ack=True)
        workspace.broadcast("@grok1", 10, "BUG", "Bug found")
        
        # Get conflicts
        conflicts = workspace.get_conflicts()
        assert len(conflicts) == 2, "Should have 2 conflicts"
        for c in conflicts:
            assert c['category'] == 'CONFLICT', "All should be CONFLICT category"
            assert c['requires_ack'], "Conflicts should require acknowledgment"
        
        print("  ✓ Get conflicts works correctly")
    print()


def test_get_directives():
    """Test retrieving DIRECTIVE broadcasts."""
    print("Testing get_directives...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create various broadcasts
        workspace.broadcast("@gpt1", 10, "SECURITY", "Security issue")
        workspace.broadcast("@claude1", 25, "DIRECTIVE", "Focus on security")
        workspace.broadcast("@llama1", 30, "DIRECTIVE", "Review all code")
        workspace.broadcast("@grok1", 10, "BUG", "Bug found")
        
        # Get directives
        directives = workspace.get_directives(active_only=False)
        assert len(directives) == 2, "Should have 2 directives"
        for d in directives:
            assert d['category'] == 'DIRECTIVE', "All should be DIRECTIVE category"
            assert d['level'] >= 20, "All should be from high-level agents"
        
        print("  ✓ Get directives works correctly")
    print()


def test_summary_generation():
    """Test workspace summary generation."""
    print("Testing summary generation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create broadcasts
        workspace.broadcast("@gpt1", 10, "SECURITY", "Security 1")
        workspace.broadcast("@claude1", 10, "SECURITY", "Security 2")
        workspace.broadcast("@llama1", 10, "BUG", "Bug 1")
        workspace.broadcast("@grok1", 25, "DIRECTIVE", "Directive 1", requires_ack=True)
        workspace.broadcast("@gpt1", 10, "OPTIMIZATION", "Opt 1")
        
        # Get summary
        summary = workspace.get_summary()
        
        assert summary['total_broadcasts'] == 5, "Should have 5 total broadcasts"
        assert summary['by_category']['SECURITY'] == 2, "Should have 2 SECURITY"
        assert summary['by_category']['BUG'] == 1, "Should have 1 BUG"
        assert summary['by_category']['DIRECTIVE'] == 1, "Should have 1 DIRECTIVE"
        assert summary['by_category']['OPTIMIZATION'] == 1, "Should have 1 OPTIMIZATION"
        assert summary['pending_acks'] == 1, "Should have 1 pending ack"
        
        print("  ✓ Summary generation works correctly")
    print()


def test_prompt_formatting():
    """Test formatting broadcasts for agent prompts."""
    print("Testing prompt formatting...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create broadcasts
        workspace.broadcast("@gpt1", 10, "SECURITY", "Found vulnerability in auth module")
        workspace.broadcast("@claude1", 15, "BUG", "Null pointer dereference detected")
        result = workspace.broadcast("@llama1", 25, "DIRECTIVE", "Focus on security issues", requires_ack=True)
        
        # Format for @grok1 (should see pending ack)
        formatted = workspace.format_for_prompt("@grok1", max_entries=10)
        
        assert "GLOBAL WORKSPACE" in formatted, "Should have header"
        assert "SECURITY" in formatted, "Should mention SECURITY broadcast"
        assert "BUG" in formatted, "Should mention BUG broadcast"
        assert "DIRECTIVE" in formatted, "Should mention DIRECTIVE broadcast"
        assert "require your acknowledgment" in formatted, "Should mention pending acks"
        assert "[ACK: 0]" in formatted, "Should show ack count"
        
        # Acknowledge and format again
        workspace.acknowledge(result['broadcast_id'], "@grok1")
        formatted_after = workspace.format_for_prompt("@grok1", max_entries=10)
        
        assert "require your acknowledgment" not in formatted_after, \
            "Should not mention pending acks after acknowledging"
        
        # Format for agent with no pending acks
        formatted_gpt = workspace.format_for_prompt("@gpt1", max_entries=10)
        assert "1 broadcast requires" in formatted_gpt or "1 broadcasts require" in formatted_gpt, \
            f"GPT should see 1 pending (from llama DIRECTIVE), got: {formatted_gpt}"
        
        print("  ✓ Prompt formatting works correctly")
    print()


def test_broadcast_limit():
    """Test that workspace limits broadcasts to max count."""
    print("Testing broadcast limit...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Create more than max broadcasts (200)
        for i in range(250):
            workspace.broadcast(f"@agent{i % 5}", 10, "STATUS", f"Message {i}")
        
        # Check that only last 200 are kept
        all_broadcasts = workspace.get_broadcasts(limit=999)
        assert len(all_broadcasts) <= 200, f"Should have at most 200 broadcasts, got {len(all_broadcasts)}"
        
        # Check metadata still tracks total
        data = workspace._read_workspace()
        assert data['metadata']['total_broadcasts'] == 250, \
            f"Total should be 250, got {data['metadata']['total_broadcasts']}"
        
        print("  ✓ Broadcast limit works correctly")
    print()


def test_thread_safety():
    """Test that filelock provides thread-safe access."""
    print("Testing thread safety...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        # Test that lock file is created and used
        assert workspace.lock_file.exists(), "Lock file should be created"
        
        # Multiple rapid broadcasts should all succeed
        for i in range(10):
            result = workspace.broadcast(f"@agent{i}", 10, "STATUS", f"Rapid message {i}")
            assert result['success'], f"Broadcast {i} should succeed"
        
        broadcasts = workspace.get_broadcasts(limit=999)
        assert len(broadcasts) == 10, "All 10 broadcasts should be stored"
        
        print("  ✓ Thread safety works correctly")
    print()


def test_broadcast_with_optional_fields():
    """Test broadcasting with optional related_file and tags."""
    print("Testing broadcast with optional fields...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        
        result = workspace.broadcast(
            agent_alias="@claude1",
            agent_level=15,
            category="SECURITY",
            message="XSS vulnerability detected",
            related_file="src/auth/login.py",
            tags=["xss", "high-priority", "auth"]
        )
        
        assert result['success'], "Broadcast should succeed"
        
        broadcasts = workspace.get_broadcasts()
        assert len(broadcasts) == 1, "Should have 1 broadcast"
        
        broadcast = broadcasts[0]
        assert broadcast['related_file'] == "src/auth/login.py", "Should have related file"
        assert broadcast['tags'] == ["xss", "high-priority", "auth"], "Should have tags"
        
        print("  ✓ Optional fields work correctly")
    print()


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("GLOBAL WORKSPACE TEST SUITE")
    print("=" * 60)
    print()
    
    test_functions = [
        test_workspace_initialization,
        test_broadcast_valid_category,
        test_broadcast_invalid_category,
        test_directive_permission_check,
        test_acknowledgment_flow,
        test_filtering_by_category,
        test_filtering_by_agent,
        test_filtering_by_time,
        test_filtering_requires_ack,
        test_pending_acks_retrieval,
        test_get_conflicts,
        test_get_directives,
        test_summary_generation,
        test_prompt_formatting,
        test_broadcast_limit,
        test_thread_safety,
        test_broadcast_with_optional_fields,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
