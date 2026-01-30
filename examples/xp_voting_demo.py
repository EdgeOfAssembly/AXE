#!/usr/bin/env python3
"""
Example usage of the Peer XP Voting System.
Demonstrates:
- Creating a workspace
- Casting votes
- Applying votes to database
- Viewing vote history
- Level-up from votes
"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.global_workspace import GlobalWorkspace
from database.agent_db import AgentDatabase
def main():
    print("=" * 70)
    print("PEER XP VOTING SYSTEM - USAGE EXAMPLE")
    print("Minsky's Society of Mind - Emergent Reputation")
    print("=" * 70)
    print()
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_file = os.path.join(tmpdir, 'workspace.json')
        db_path = os.path.join(tmpdir, 'agents.db')
        # Initialize workspace and database
        print("1. Initializing workspace and database...")
        ws = GlobalWorkspace(workspace_file)
        db = AgentDatabase(db_path)
        print("   ✓ Workspace and database ready")
        print()
        # Create some test agents
        print("2. Creating test agents...")
        db.save_agent_state('agent_claude', 'claude', 'claude-3-5-sonnet',
                           {}, [], 0, 150, 8)
        db.save_agent_state('agent_llama', 'llama', 'llama-3.1-70b',
                           {}, [], 0, 300, 12)
        db.save_agent_state('agent_grok', 'grok', 'grok-beta',
                           {}, [], 0, 95, 5)
        print("   ✓ Created @claude (L8, 150 XP)")
        print("   ✓ Created @llama (L12, 300 XP)")
        print("   ✓ Created @grok (L5, 95 XP)")
        print()
        # Scenario 1: Positive vote
        print("3. Scenario 1: @llama endorses @claude's security analysis")
        result = ws.vote_xp('@llama', 12, '@claude', 15,
                           'Excellent buffer overflow detection in auth module')
        if result['success']:
            print(f"   ✓ Vote cast: {result['xp_delta']:+d} XP")
            print(f"   ✓ Votes remaining: {result['votes_remaining']}")
            print(f"   ✓ Reason: Excellent buffer overflow detection in auth module")
        print()
        # Scenario 2: Another positive vote
        print("4. Scenario 2: @claude endorses @grok's optimization")
        result = ws.vote_xp('@claude', 8, '@grok', 10,
                           'Clever assembly optimization saved 50 bytes')
        if result['success']:
            print(f"   ✓ Vote cast: {result['xp_delta']:+d} XP")
            print(f"   ✓ Votes remaining: {result['votes_remaining']}")
        print()
        # Scenario 3: Negative vote (rare)
        print("5. Scenario 3: @llama penalizes @grok for poor suggestion")
        result = ws.vote_xp('@llama', 12, '@grok', -5,
                           'Suggested strcpy without bounds checking')
        if result['success']:
            print(f"   ✓ Vote cast: {result['xp_delta']:+d} XP")
            print(f"   ✓ Votes remaining: {result['votes_remaining']}")
        print()
        # Scenario 4: Try to vote for self (should fail)
        print("6. Scenario 4: @claude attempts to vote for self (should fail)")
        result = ws.vote_xp('@claude', 8, '@claude', 10, 'I am great!')
        if not result['success']:
            print(f"   ✓ Vote blocked: {result['error']}")
        print()
        # Scenario 5: Try to exceed vote limit
        print("7. Scenario 5: @llama tries to exceed level-based limit")
        result = ws.vote_xp('@llama', 12, '@claude', 20,
                           'Amazing work')
        if not result['success']:
            print(f"   ✓ Vote blocked: {result['error']}")
            print(f"   ✓ Level 12 (Team Leader) max: 15 XP")
        print()
        # View vote history
        print("8. Viewing vote history...")
        all_votes = ws.get_vote_history()
        print(f"   Total votes cast: {len(all_votes)}")
        for vote in all_votes:
            print(f"   • {vote['voter']} → {vote['target']}: {vote['xp_delta']:+d} XP")
            print(f"     Reason: {vote['reason']}")
        print()
        # View vote summary
        print("9. Vote summary (net XP per agent)...")
        summary = ws.get_vote_summary()
        for agent, net_xp in sorted(summary.items(), key=lambda x: x[1], reverse=True):
            print(f"   {agent}: {net_xp:+d} XP from votes")
        print()
        # Apply votes to database
        print("10. Applying pending votes to database...")
        pending = ws.get_pending_votes()
        print(f"    Pending votes: {len(pending)}")
        results = db.apply_xp_votes(pending)
        for result in results:
            if result['success']:
                print(f"    ✓ {result['target']}: {result['old_level']} XP → {result['xp']} XP")
                if result['leveled_up']:
                    print(f"      🎉 LEVEL UP! {result['old_level']} → {result['new_level']} ({result['new_title']})")
        # Mark votes as applied
        for vote in pending:
            ws.mark_vote_applied(vote['id'])
        print()
        # Final agent states
        print("11. Final agent states...")
        for alias in ['claude', 'llama', 'grok']:
            agent = db.get_agent_by_alias(alias)
            if agent:
                print(f"    @{alias}: L{agent['level']} - {agent['xp']} XP")
        print()
        # Session limits demo
        print("12. Session limits demo (max 3 votes per agent)...")
        ws.reset_vote_limits()  # Start fresh
        # Cast 3 votes
        for i in range(3):
            result = ws.vote_xp('@claude', 8, f'@target{i}', 5, f'Vote {i+1}')
            if result['success']:
                print(f"    Vote {i+1}/3: Success (remaining: {result['votes_remaining']})")
        # Try 4th vote
        result = ws.vote_xp('@claude', 8, '@target_extra', 5, 'Vote 4')
        if not result['success']:
            print(f"    Vote 4/3: Blocked - {result['error']}")
        print()
        # Broadcast example
        print("13. Broadcast system example...")
        ws.broadcast('XP_VOTE', '@llama',
                    'Cast endorsement vote for @claude',
                    {'vote_id': 'vote_123', 'amount': 15})
        broadcasts = ws.get_broadcasts(category='XP_VOTE')
        print(f"    XP_VOTE broadcasts: {len(broadcasts)}")
        if broadcasts:
            bc = broadcasts[0]
            print(f"    Latest: {bc['sender']}: {bc['message']}")
        print()
        print("=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print()
        print("Key Takeaways:")
        print("  • Votes are limited by voter level (Worker → Supervisor)")
        print("  • Cannot vote for yourself")
        print("  • Max 3 votes per agent per session")
        print("  • Votes can trigger level-ups")
        print("  • Negative votes are limited (use sparingly)")
        print("  • All votes are tracked in persistent workspace")
        print()
        print("Theory: Minsky's Society of Mind (1986)")
        print("  Emergent reputation through peer interaction")
        print()
if __name__ == '__main__':
    main()