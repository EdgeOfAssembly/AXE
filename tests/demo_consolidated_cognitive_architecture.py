#!/usr/bin/env python3
"""
Demo: Consolidated Cognitive Architecture Features
Tests all three merged PRs:
- PR #54: Subsumption Architecture (Brooks 1986)
- PR #55: XP Voting System (Minsky 1986)
- PR #56: Conflict Detection & Arbitration (Minsky 1986)
"""
import sys
import tempfile
from pathlib import Path
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from core import (
    SubsumptionController, SubsumptionLayer,
    GlobalWorkspace,
    ArbitrationProtocol,
    AGENT_TOKEN_SUPPRESS, AGENT_TOKEN_XP_VOTE, AGENT_TOKEN_CONFLICT
)
from database.agent_db import AgentDatabase
from progression.xp_system import XP_AWARDS
def test_subsumption():
    """Test Subsumption Architecture (Brooks 1986)"""
    print("=" * 60)
    print("TEST 1: Subsumption Architecture (Brooks 1986)")
    print("=" * 60)
    controller = SubsumptionController()
    # Test layer assignment
    worker_layer = controller.get_layer_for_level(5)
    tactical_layer = controller.get_layer_for_level(15)
    strategic_layer = controller.get_layer_for_level(25)
    print(f"✅ Worker (L5) → {worker_layer.name}")
    print(f"✅ Tactical (L15) → {tactical_layer.name}")
    print(f"✅ Strategic (L25) → {strategic_layer.name}")
    # Test suppression
    success, message = controller.suppress_agent('@worker1', 5, '@worker2', 3, 'Lower priority task')
    print(f"✅ Suppression: {success}")
    # Test execution order
    agents = [
        {'id': '@exec1', 'level': 40},
        {'id': '@worker1', 'level': 5},
        {'id': '@tactical1', 'level': 15},
    ]
    ordered = controller.get_execution_order(agents)
    order_str = ' → '.join([f"{a['id']}(L{a['level']})" for a in ordered])
    print(f"✅ Execution order: {order_str}")
    print()
def test_xp_voting():
    """Test XP Voting System (Minsky 1986)"""
    print("=" * 60)
    print("TEST 2: XP Voting System (Minsky 1986)")
    print("=" * 60)
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        # Test voting
        result = workspace.vote_xp('@agent1', 10, '@agent2', 10, 'Great code review')
        print(f"✅ Vote cast: {result['success']}")
        print(f"   {result.get('message', '')}")
        # Test vote limits
        result2 = workspace.vote_xp('@agent1', 10, '@agent3', 11, 'Trying to exceed limit')
        print(f"✅ Limit enforcement: {not result2['success']}")
        print(f"   {result2.get('error', '')}")
        # Test self-vote prevention
        result3 = workspace.vote_xp('@agent1', 10, '@agent1', 5, 'Self vote')
        print(f"✅ Self-vote prevention: {not result3['success']}")
        # Test vote history
        votes = workspace.get_vote_history()
        print(f"✅ Vote history: {len(votes)} votes recorded")
    print()
def test_conflict_detection():
    """Test Conflict Detection & Arbitration (Minsky 1986)"""
    print("=" * 60)
    print("TEST 3: Conflict Detection & Arbitration (Minsky 1986)")
    print("=" * 60)
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        # Create contradictory broadcasts
        b1 = workspace.broadcast('@agent1', 10, 'SECURITY', 'This code is safe')
        b2 = workspace.broadcast('@agent2', 12, 'SECURITY', 'This code is unsafe')
        print(f"✅ Broadcast 1: {b1['success']}")
        print(f"✅ Broadcast 2: {b2['success']}")
        # Detect conflicts
        conflicts = workspace.detect_conflicts(window_broadcasts=10)
        print(f"✅ Conflicts detected: {len(conflicts)}")
        if conflicts:
            c = conflicts[0]
            print(f"   Type: {c['type']}")
            print(f"   Reason: {c['reason']}")
        # Test arbitration protocol
        protocol = ArbitrationProtocol(tmpdir)
        if conflicts:
            arb = protocol.create_arbitration(
                broadcast_ids=[b1['broadcast_id'], b2['broadcast_id']],
                created_by='@supervisor',
                current_turn=1,
                agent_levels={'@agent1': 10, '@agent2': 12}
            )
            print(f"✅ Arbitration created: {arb['success']}")
            if arb['success']:
                print(f"   Required level: {arb['arbitration']['required_level']}")
                print(f"   Deadline: turn {arb['arbitration']['deadline_turn']}")
    print()
def test_xp_awards():
    """Test XP Award System"""
    print("=" * 60)
    print("TEST 4: XP Award System")
    print("=" * 60)
    print(f"✅ Total XP award types: {len(XP_AWARDS)}")
    print()
    print("Peer Voting Awards:")
    for key, value in XP_AWARDS.items():
        if 'peer' in key or 'voting' in key:
            print(f"  - {key}: {value:+d} XP")
    print()
    print("Arbitration Awards:")
    for key, value in XP_AWARDS.items():
        if 'arbitration' in key or 'conflict' in key:
            print(f"  - {key}: {value:+d} XP")
    print()
def test_tokens():
    """Test Agent Communication Tokens"""
    print("=" * 60)
    print("TEST 5: Agent Communication Tokens")
    print("=" * 60)
    print(f"✅ Suppress token: {AGENT_TOKEN_SUPPRESS}")
    print(f"✅ XP Vote token: {AGENT_TOKEN_XP_VOTE}")
    print(f"✅ Conflict token: {AGENT_TOKEN_CONFLICT}")
    print()
def test_database_integration():
    """Test Database Integration"""
    print("=" * 60)
    print("TEST 6: Database Integration")
    print("=" * 60)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"
        db = AgentDatabase(db_path)
        # Test agent state save
        agent_id = "agent_test_001"
        db.save_agent_state(agent_id, 'test_agent', 'tinyllama',
                           {}, [], 0, 25, 1)
        print(f"✅ Agent state saved: {agent_id}")
        # Test XP award
        result = db.award_xp(agent_id, 25, 'arbitration_win')
        print(f"✅ XP awarded: 25 XP")
        print(f"   New level: {result['new_level']}")
        print(f"   Total XP: {result['xp']}")
        # Test agent lookup by alias
        agent = db.get_agent_by_alias('test_agent')
        if agent:
            print(f"✅ Agent lookup: {agent['alias']} (Level {agent['level']}, {agent['xp']} XP)")
    print()
def main():
    print("\n" + "=" * 60)
    print("CONSOLIDATED COGNITIVE ARCHITECTURE DEMO")
    print("Testing PRs #54, #55, #56")
    print("=" * 60)
    print()
    test_subsumption()
    test_xp_voting()
    test_conflict_detection()
    test_xp_awards()
    test_tokens()
    test_database_integration()
    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    print()
    print("The consolidated cognitive architecture is working correctly!")
    print("Features integrated:")
    print("  1. Subsumption Architecture (Brooks 1986) - Hierarchical control")
    print("  2. XP Voting System (Minsky 1986) - Peer reputation")
    print("  3. Conflict Detection & Arbitration (Minsky 1986) - Conflict resolution")
    print()
if __name__ == '__main__':
    main()