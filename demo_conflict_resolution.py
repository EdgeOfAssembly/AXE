#!/usr/bin/env python3
"""
Demo script showing conflict detection and arbitration protocol in action.
This demonstrates Minsky's Society of Mind concepts for handling agent disagreements.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.global_workspace import GlobalWorkspace
from core.arbitration import ArbitrationProtocol
from database.agent_db import AgentDatabase
import tempfile
def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)
def print_section(text):
    """Print a formatted section header."""
    print(f"\n--- {text} ---")
def demo_conflict_resolution():
    """Demonstrate the full conflict resolution workflow."""
    print_header("AXE CONFLICT RESOLUTION PROTOCOL DEMO")
    print("\nImplementing Marvin Minsky's Society of Mind concepts")
    print("Reference: Minsky, M. (1986). The Society of Mind. Chapters 17-19")
    # Set up system with temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'demo.db')
        db = AgentDatabase(db_path)
        workspace = GlobalWorkspace(db)
        protocol = ArbitrationProtocol(workspace, None, db)
        print_section("SCENARIO: Security Analysis Disagreement")
        print("Two agents analyze the same function and reach different conclusions...")
        # Simulate agent broadcasts
        print("\n🤖 Agent Claude (Level 10) broadcasts:")
        b1_id = workspace.broadcast(
            agent_alias='claude',
            agent_level=10,
            category='SECURITY',
            content='Function sanitize_user_input() is safe. All inputs are properly escaped.',
            metadata={'files': ['auth.py'], 'functions': ['sanitize_user_input']}
        )
        print(f"   Category: SECURITY")
        print(f"   Content: 'Function sanitize_user_input() is safe. All inputs are properly escaped.'")
        print(f"   Broadcast ID: {b1_id[:8]}...")
        print("\n🤖 Agent GPT (Level 12) broadcasts:")
        b2_id = workspace.broadcast(
            agent_alias='gpt',
            agent_level=12,
            category='SECURITY',
            content='Function sanitize_user_input() is unsafe. SQL injection vulnerability detected.',
            metadata={'files': ['auth.py'], 'functions': ['sanitize_user_input']}
        )
        print(f"   Category: SECURITY")
        print(f"   Content: 'Function sanitize_user_input() is unsafe. SQL injection vulnerability detected.'")
        print(f"   Broadcast ID: {b2_id[:8]}...")
        # Detect conflicts
        print_section("AUTOMATIC CONFLICT DETECTION")
        conflicts = workspace.detect_conflicts()
        if conflicts:
            conflict = conflicts[0]
            print(f"✅ Conflict detected!")
            print(f"   Type: {conflict['type']}")
            print(f"   Reason: {conflict['reason']}")
            print(f"   Agents: claude vs gpt")
            print(f"   Topic: sanitize_user_input() function")
        # Create arbitration
        print_section("ARBITRATION CREATION")
        broadcasts_for_arb = [
            {
                'id': b1_id,
                'agent_alias': 'claude',
                'agent_level': 10,
                'category': 'SECURITY',
                'content': 'Function is safe',
                'metadata': {}
            },
            {
                'id': b2_id,
                'agent_alias': 'gpt',
                'agent_level': 12,
                'category': 'SECURITY',
                'content': 'Function is unsafe',
                'metadata': {}
            }
        ]
        arbitration = protocol.create_arbitration(broadcasts_for_arb, created_by='SYSTEM')
        print(f"📋 Arbitration created:")
        print(f"   ID: {arbitration['id'][:8]}...")
        print(f"   Required Level: {arbitration['required_level']} (max agent level 12 + 10)")
        print(f"   Deadline: Turn {arbitration['deadline_turn']}")
        print(f"   Status: {arbitration['status']}")
        # Find arbitrator
        print_section("ARBITRATOR SELECTION")
        available_agents = [
            {'alias': 'claude', 'level': 10},
            {'alias': 'gpt', 'level': 12},
            {'alias': 'llama', 'level': 15},
            {'alias': 'grok', 'level': 25},
            {'alias': 'boss', 'level': 50},
        ]
        print("Available agents:")
        for agent in available_agents:
            qualified = "✓" if agent['level'] >= arbitration['required_level'] else "✗"
            conflicting = "⚠" if agent['alias'] in ['claude', 'gpt'] else " "
            print(f"   {qualified} {conflicting} {agent['alias']:10s} (Level {agent['level']:2d})")
        arbitrator = protocol.get_arbitrator(arbitration['id'], available_agents)
        print(f"\n🎯 Selected arbitrator: {arbitrator['alias']} (Level {arbitrator['level']})")
        print(f"   Reason: Lowest qualifying level (subsidiarity principle)")
        # Submit resolution
        print_section("ARBITRATION RESOLUTION")
        xp_awards = {
            'gpt': 15,      # Winner
            'claude': 5,    # Good faith participant
            'grok': 20      # Arbitrator
        }
        resolution = protocol.submit_resolution(
            arbitration_id=arbitration['id'],
            arbitrator_alias='grok',
            arbitrator_level=25,
            resolution='After code analysis, SQL injection vulnerability confirmed. GPT is correct.',
            winning_broadcast_id=b2_id,
            xp_awards=xp_awards
        )
        print("🏆 Arbitration resolved by Grok:")
        print(f"   Resolution: {resolution['resolution']}")
        print(f"   Winner: gpt (broadcast {resolution['winning_broadcast_id'][:8]}...)")
        print(f"\n💰 XP Awards:")
        for agent, xp in xp_awards.items():
            print(f"   {agent:10s}: +{xp:2d} XP")
        # Show workspace broadcasts
        print_section("FINAL WORKSPACE STATE")
        all_broadcasts = workspace.get_broadcasts()
        print(f"\nTotal broadcasts: {len(all_broadcasts)}")
        print("\nRecent broadcasts:")
        for b in all_broadcasts[-3:]:
            print(f"   [{b['category']:20s}] {b['agent_alias']:10s}: {b['content'][:60]}...")
        pending = protocol.get_pending_arbitrations()
        print(f"\nPending arbitrations: {len(pending)}")
        resolved = protocol.resolved_arbitrations
        print(f"Resolved arbitrations: {len(resolved)}")
        print_header("DEMO COMPLETE")
        print("\nKey Concepts Demonstrated:")
        print("  ✓ Global Workspace - Broadcast-based communication")
        print("  ✓ Conflict Detection - Automatic keyword matching")
        print("  ✓ Hierarchical Arbitration - Level-based authority")
        print("  ✓ Subsidiarity Principle - Lowest qualifying arbitrator")
        print("  ✓ XP Progression - Rewards for conflict resolution")
        print("\nFor more examples, see: docs/conflict_resolution_examples.md")
        print()
if __name__ == '__main__':
    demo_conflict_resolution()