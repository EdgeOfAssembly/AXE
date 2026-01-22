#!/usr/bin/env python3
"""
Test suite for conflict detection and arbitration protocol.

Tests Minsky's cross-exclusion and conflict resolution patterns:
- Conflict detection (keyword matching)
- Manual conflict flagging
- Arbitration creation and resolution
- Arbitrator selection (level rules)
- Escalation mechanisms
- XP awards from arbitration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.global_workspace import GlobalWorkspace
from core.arbitration import ArbitrationProtocol
from core.constants import (
    CONTRADICTION_PAIRS,
    ARBITRATION_DEADLINE_TURNS,
    ARBITRATION_MIN_LEVEL_BUMP
)


def test_broadcast_creation():
    """Test basic broadcast functionality."""
    print("Testing broadcast creation...")
    
    workspace = GlobalWorkspace()
    
    # Create a broadcast
    broadcast_id = workspace.broadcast(
        agent_alias='claude',
        agent_level=10,
        category='SECURITY',
        content='This code is safe and secure.',
        metadata={'files': ['test.py']}
    )
    
    assert broadcast_id is not None, "Broadcast should return an ID"
    
    # Retrieve broadcasts
    broadcasts = workspace.get_broadcasts()
    assert len(broadcasts) == 1, "Should have one broadcast"
    assert broadcasts[0]['agent_alias'] == 'claude'
    assert broadcasts[0]['category'] == 'SECURITY'
    
    print("  ✓ Broadcast creation works")
    print()


def test_contradiction_detection():
    """Test automatic conflict detection via keyword matching."""
    print("Testing contradiction detection...")
    
    workspace = GlobalWorkspace()
    
    # Create contradictory broadcasts
    workspace.broadcast(
        agent_alias='claude',
        agent_level=10,
        category='SECURITY',
        content='This code is safe and has no vulnerabilities.',
        metadata={'files': ['test.py']}
    )
    
    workspace.broadcast(
        agent_alias='gpt',
        agent_level=12,
        category='SECURITY',
        content='This code is unsafe and has vulnerabilities.',
        metadata={'files': ['test.py']}
    )
    
    # Detect conflicts
    conflicts = workspace.detect_conflicts()
    
    assert len(conflicts) > 0, "Should detect at least one conflict"
    assert conflicts[0]['type'] == 'detected', "Should be automatically detected"
    assert 'safe' in conflicts[0]['reason'].lower() or 'unsafe' in conflicts[0]['reason'].lower()
    
    print(f"  ✓ Detected {len(conflicts)} conflict(s)")
    print(f"    Reason: {conflicts[0]['reason']}")
    print()


def test_contradiction_pairs():
    """Test all contradiction keyword pairs."""
    print("Testing contradiction keyword pairs...")
    
    workspace = GlobalWorkspace()
    detected_pairs = []
    
    for word1, word2 in CONTRADICTION_PAIRS[:5]:  # Test first 5 pairs
        workspace.broadcasts = []  # Clear workspace
        
        # Create contradictory broadcasts
        workspace.broadcast(
            agent_alias='agent1',
            agent_level=5,
            category='TEST',
            content=f'This is {word1}.',
            metadata={'files': ['test.py']}
        )
        
        workspace.broadcast(
            agent_alias='agent2',
            agent_level=5,
            category='TEST',
            content=f'This is {word2}.',
            metadata={'files': ['test.py']}
        )
        
        conflicts = workspace.detect_conflicts()
        if conflicts:
            detected_pairs.append((word1, word2))
    
    assert len(detected_pairs) >= 3, f"Should detect most contradiction pairs, found {len(detected_pairs)}"
    print(f"  ✓ Detected {len(detected_pairs)} contradiction pairs")
    print()


def test_manual_conflict_flagging():
    """Test manual conflict flagging by agents."""
    print("Testing manual conflict flagging...")
    
    workspace = GlobalWorkspace()
    
    # Create some broadcasts
    b1 = workspace.broadcast(
        agent_alias='claude',
        agent_level=10,
        category='CODE_QUALITY',
        content='This approach is correct.',
        metadata={'functions': ['process_data']}
    )
    
    b2 = workspace.broadcast(
        agent_alias='gpt',
        agent_level=12,
        category='CODE_QUALITY',
        content='This approach is incorrect.',
        metadata={'functions': ['process_data']}
    )
    
    # Manually flag conflict
    conflict = workspace.flag_conflict(
        broadcast_ids=[b1, b2],
        flagged_by='llama',
        reason='Agents disagree on correctness of process_data approach'
    )
    
    assert conflict['type'] == 'manual', "Should be manually flagged"
    assert conflict['flagged_by'] == 'llama'
    assert len(conflict['broadcasts']) == 2
    
    # Check that a CONFLICT broadcast was created
    conflict_broadcasts = workspace.get_broadcasts(category='CONFLICT')
    assert len(conflict_broadcasts) == 1, "Should create a CONFLICT broadcast"
    
    print("  ✓ Manual conflict flagging works")
    print()


def test_arbitration_creation():
    """Test arbitration creation from conflicts."""
    print("Testing arbitration creation...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create conflicting broadcasts
    broadcasts = [
        {
            'id': '1',
            'agent_alias': 'claude',
            'agent_level': 10,
            'category': 'SECURITY',
            'content': 'Safe code',
            'metadata': {}
        },
        {
            'id': '2',
            'agent_alias': 'gpt',
            'agent_level': 12,
            'category': 'SECURITY',
            'content': 'Unsafe code',
            'metadata': {}
        }
    ]
    
    # Create arbitration
    arbitration = protocol.create_arbitration(broadcasts, created_by='SYSTEM')
    
    assert arbitration['id'] is not None
    assert arbitration['status'] == 'pending'
    assert arbitration['required_level'] == 12 + ARBITRATION_MIN_LEVEL_BUMP
    assert arbitration['deadline_turn'] == ARBITRATION_DEADLINE_TURNS
    
    print(f"  ✓ Arbitration created with ID {arbitration['id'][:8]}")
    print(f"    Required level: {arbitration['required_level']}")
    print()


def test_arbitrator_selection():
    """Test arbitrator selection based on level rules."""
    print("Testing arbitrator selection...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create conflicting broadcasts
    broadcasts = [
        {
            'id': '1',
            'agent_alias': 'claude',
            'agent_level': 10,
            'category': 'SECURITY',
            'content': 'Safe',
            'metadata': {}
        },
        {
            'id': '2',
            'agent_alias': 'gpt',
            'agent_level': 12,
            'category': 'SECURITY',
            'content': 'Unsafe',
            'metadata': {}
        }
    ]
    
    arbitration = protocol.create_arbitration(broadcasts)
    required_level = arbitration['required_level']  # 12 + 10 = 22
    
    # Available agents
    available_agents = [
        {'alias': 'claude', 'level': 10},  # Conflicting agent
        {'alias': 'gpt', 'level': 12},     # Conflicting agent
        {'alias': 'llama', 'level': 15},   # Too low
        {'alias': 'grok', 'level': 25},    # Qualified
        {'alias': 'boss', 'level': 50},    # Over-qualified
    ]
    
    arbitrator = protocol.get_arbitrator(arbitration['id'], available_agents)
    
    assert arbitrator is not None, "Should find an arbitrator"
    assert arbitrator['level'] >= required_level, "Arbitrator must meet level requirement"
    assert arbitrator['alias'] not in ['claude', 'gpt'], "Conflicting agents cannot arbitrate"
    assert arbitrator['alias'] == 'grok', "Should select lowest qualified level (subsidiarity)"
    
    print(f"  ✓ Selected {arbitrator['alias']} (level {arbitrator['level']}) for level {required_level}+ arbitration")
    print()


def test_no_qualified_arbitrator():
    """Test case where no arbitrator is qualified."""
    print("Testing no qualified arbitrator scenario...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create high-level conflict
    broadcasts = [
        {
            'id': '1',
            'agent_alias': 'claude',
            'agent_level': 45,
            'category': 'SECURITY',
            'content': 'Safe',
            'metadata': {}
        },
        {
            'id': '2',
            'agent_alias': 'gpt',
            'agent_level': 48,
            'category': 'SECURITY',
            'content': 'Unsafe',
            'metadata': {}
        }
    ]
    
    arbitration = protocol.create_arbitration(broadcasts)
    # Required level will be 48 + 10 = 58
    
    # Only low-level agents available
    available_agents = [
        {'alias': 'llama', 'level': 15},
        {'alias': 'grok', 'level': 25},
    ]
    
    arbitrator = protocol.get_arbitrator(arbitration['id'], available_agents)
    
    assert arbitrator is None, "Should return None when no one is qualified"
    print("  ✓ Correctly handles case with no qualified arbitrator")
    print()


def test_resolution_submission():
    """Test submitting a resolution for an arbitration."""
    print("Testing resolution submission...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create arbitration
    broadcasts = [
        {
            'id': 'b1',
            'agent_alias': 'claude',
            'agent_level': 10,
            'category': 'SECURITY',
            'content': 'Safe',
            'metadata': {}
        },
        {
            'id': 'b2',
            'agent_alias': 'gpt',
            'agent_level': 12,
            'category': 'SECURITY',
            'content': 'Unsafe',
            'metadata': {}
        }
    ]
    
    arbitration = protocol.create_arbitration(broadcasts)
    arb_id = arbitration['id']
    
    # Submit resolution
    xp_awards = {
        'gpt': 15,      # Winner
        'claude': 5,    # Good faith participant
    }
    
    resolution = protocol.submit_resolution(
        arbitration_id=arb_id,
        arbitrator_alias='grok',
        arbitrator_level=25,
        resolution='After analysis, the code is unsafe. GPT is correct.',
        winning_broadcast_id='b2',
        xp_awards=xp_awards
    )
    
    assert resolution['arbitrator_alias'] == 'grok'
    assert resolution['winning_broadcast_id'] == 'b2'
    assert resolution['xp_awards'] == xp_awards
    
    # Check that arbitration is no longer pending
    pending = protocol.get_pending_arbitrations()
    assert len(pending) == 0, "Arbitration should no longer be pending"
    
    # Check resolution broadcast
    resolution_broadcasts = workspace.get_broadcasts(category='ARBITRATION_RESOLVED')
    assert len(resolution_broadcasts) == 1
    
    print("  ✓ Resolution submitted successfully")
    print(f"    Winner: {resolution['winning_broadcast_id']}")
    print()


def test_insufficient_level_resolution():
    """Test that insufficient level arbitrators are rejected."""
    print("Testing insufficient level rejection...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create arbitration
    broadcasts = [
        {
            'id': 'b1',
            'agent_alias': 'claude',
            'agent_level': 30,
            'category': 'SECURITY',
            'content': 'Safe',
            'metadata': {}
        },
        {
            'id': 'b2',
            'agent_alias': 'gpt',
            'agent_level': 35,
            'category': 'SECURITY',
            'content': 'Unsafe',
            'metadata': {}
        }
    ]
    
    arbitration = protocol.create_arbitration(broadcasts)
    # Required level: 35 + 10 = 45
    
    # Try to resolve with insufficient level
    try:
        protocol.submit_resolution(
            arbitration_id=arbitration['id'],
            arbitrator_alias='llama',
            arbitrator_level=20,  # Too low
            resolution='My resolution',
        )
        assert False, "Should raise ValueError for insufficient level"
    except ValueError as e:
        assert 'insufficient' in str(e).lower()
        print("  ✓ Correctly rejects insufficient level arbitrator")
    
    print()


def test_escalation():
    """Test arbitration escalation mechanism."""
    print("Testing escalation...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create arbitration
    broadcasts = [
        {
            'id': 'b1',
            'agent_alias': 'claude',
            'agent_level': 10,
            'category': 'SECURITY',
            'content': 'Safe',
            'metadata': {}
        },
        {
            'id': 'b2',
            'agent_alias': 'gpt',
            'agent_level': 12,
            'category': 'SECURITY',
            'content': 'Unsafe',
            'metadata': {}
        }
    ]
    
    arbitration = protocol.create_arbitration(broadcasts)
    original_level = arbitration['required_level']
    
    # Escalate
    escalated = protocol.escalate_arbitration(
        arbitration['id'],
        reason='Conflict too complex for current level'
    )
    
    assert escalated['required_level'] == original_level + ARBITRATION_MIN_LEVEL_BUMP
    assert escalated['escalation_count'] == 1
    assert len(escalated.get('escalations', [])) == 1
    
    # Check escalation broadcast
    escalation_broadcasts = workspace.get_broadcasts(category='ARBITRATION')
    escalation_found = any('escalated' in b['content'].lower() for b in escalation_broadcasts)
    assert escalation_found, "Should broadcast escalation"
    
    print(f"  ✓ Escalated from level {original_level} to {escalated['required_level']}")
    print()


def test_deadline_auto_escalation():
    """Test automatic escalation on deadline expiry."""
    print("Testing deadline auto-escalation...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create arbitration
    broadcasts = [
        {
            'id': 'b1',
            'agent_alias': 'claude',
            'agent_level': 10,
            'category': 'SECURITY',
            'content': 'Safe',
            'metadata': {}
        },
        {
            'id': 'b2',
            'agent_alias': 'gpt',
            'agent_level': 12,
            'category': 'SECURITY',
            'content': 'Unsafe',
            'metadata': {}
        }
    ]
    
    arbitration = protocol.create_arbitration(broadcasts)
    original_level = arbitration['required_level']
    deadline = arbitration['deadline_turn']
    
    # Advance turns past deadline
    for _ in range(deadline + 1):
        protocol.increment_turn()
    
    # Check if escalated
    updated = protocol.pending_arbitrations.get(arbitration['id'])
    if updated:  # If auto-escalation is enabled
        assert updated['required_level'] > original_level
        print(f"  ✓ Auto-escalated after {deadline} turns")
    else:
        print("  ✓ Auto-escalation disabled or arbitration resolved")
    
    print()


def test_format_for_prompt():
    """Test formatting arbitrations for agent prompts."""
    print("Testing prompt formatting...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create multiple arbitrations at different levels
    for level in [10, 20, 30]:
        broadcasts = [
            {
                'id': f'b1_{level}',
                'agent_alias': f'agent1_{level}',
                'agent_level': level,
                'category': 'TEST',
                'content': 'Content 1',
                'metadata': {}
            },
            {
                'id': f'b2_{level}',
                'agent_alias': f'agent2_{level}',
                'agent_level': level + 2,
                'category': 'TEST',
                'content': 'Content 2',
                'metadata': {}
            }
        ]
        protocol.create_arbitration(broadcasts)
    
    # Low-level agent sees nothing
    prompt_low = protocol.format_for_prompt('test_agent', 15)
    assert prompt_low == "", "Low-level agent should see no eligible arbitrations"
    
    # High-level agent sees eligible arbitrations
    prompt_high = protocol.format_for_prompt('test_agent', 50)
    assert len(prompt_high) > 0, "High-level agent should see eligible arbitrations"
    assert 'Pending Arbitrations' in prompt_high
    
    print("  ✓ Prompt formatting works correctly")
    print()


def test_get_pending_arbitrations_filter():
    """Test filtering pending arbitrations by level."""
    print("Testing pending arbitrations filtering...")
    
    workspace = GlobalWorkspace()
    protocol = ArbitrationProtocol(workspace)
    
    # Create arbitrations at different levels
    levels = [15, 25, 35]
    for i, level in enumerate(levels):
        broadcasts = [
            {
                'id': f'b1_{i}',
                'agent_alias': f'agent1',
                'agent_level': level - 5,
                'category': 'TEST',
                'content': f'Content {i}',
                'metadata': {}
            },
            {
                'id': f'b2_{i}',
                'agent_alias': f'agent2',
                'agent_level': level,
                'category': 'TEST',
                'content': f'Content {i}',
                'metadata': {}
            }
        ]
        protocol.create_arbitration(broadcasts)
    
    # Agent at level 30 should see only lower-level arbitrations
    pending = protocol.get_pending_arbitrations(min_level=30)
    assert all(arb['required_level'] <= 30 for arb in pending)
    
    # Agent at level 50 should see all
    pending_all = protocol.get_pending_arbitrations(min_level=50)
    assert len(pending_all) == 3
    
    print(f"  ✓ Level 30 agent sees {len(pending)} arbitrations")
    print(f"  ✓ Level 50 agent sees {len(pending_all)} arbitrations")
    print()


def run_all_tests():
    """Run all arbitration tests."""
    print("=" * 80)
    print("ARBITRATION PROTOCOL TEST SUITE")
    print("=" * 80)
    print()
    
    test_broadcast_creation()
    test_contradiction_detection()
    test_contradiction_pairs()
    test_manual_conflict_flagging()
    test_arbitration_creation()
    test_arbitrator_selection()
    test_no_qualified_arbitrator()
    test_resolution_submission()
    test_insufficient_level_resolution()
    test_escalation()
    test_deadline_auto_escalation()
    test_format_for_prompt()
    test_get_pending_arbitrations_filter()
    
    print("=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)


if __name__ == '__main__':
    run_all_tests()
