#!/usr/bin/env python3
"""
Demonstration of Global Workspace usage in AXE collaborative sessions.
This shows how agents would interact with the global workspace.
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.global_workspace import GlobalWorkspace
def demo_basic_usage():
    """Demonstrate basic broadcast and acknowledgment workflow."""
    print("=" * 70)
    print("GLOBAL WORKSPACE DEMONSTRATION")
    print("=" * 70)
    print()
    # Create a workspace in a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        print(f"✓ Workspace initialized in: {tmpdir}")
        print()
        # Scenario: Multi-agent security audit collaboration
        print("SCENARIO: Multi-agent security audit collaboration")
        print("-" * 70)
        print()
        # Agent 1 (GPT) finds a security issue
        print("[@gpt1] Broadcasting security finding...")
        result1 = workspace.broadcast(
            agent_alias="@gpt1",
            agent_level=10,
            category="SECURITY",
            message="Buffer overflow vulnerability in parse_header() at line 42",
            related_file="src/parser.c",
            tags=["buffer-overflow", "high-priority"]
        )
        print(f"  → Broadcast ID: {result1['broadcast_id']}")
        print()
        # Agent 2 (Claude) finds a bug
        print("[@claude1] Broadcasting bug discovery...")
        result2 = workspace.broadcast(
            agent_alias="@claude1",
            agent_level=15,
            category="BUG",
            message="Null pointer dereference when input is empty",
            related_file="src/parser.c",
            tags=["null-pointer", "crash"]
        )
        print(f"  → Broadcast ID: {result2['broadcast_id']}")
        print()
        # Agent 3 (Llama) - Team Leader issues a directive
        print("[@llama1] Team Leader broadcasting directive...")
        result3 = workspace.broadcast(
            agent_alias="@llama1",
            agent_level=25,  # Team Leader level
            category="DIRECTIVE",
            message="All agents: Focus on security issues in src/parser.c - critical path",
            requires_ack=True
        )
        print(f"  → Broadcast ID: {result3['broadcast_id']}")
        print(f"  → Requires acknowledgment: {result3['entry']['requires_ack']}")
        print()
        # Show workspace summary
        print("WORKSPACE SUMMARY:")
        print("-" * 70)
        summary = workspace.get_summary()
        print(f"Total broadcasts: {summary['total_broadcasts']}")
        print(f"By category: {summary['by_category']}")
        print(f"Pending acknowledgments: {summary['pending_acks']}")
        print()
        # Agent 4 (Grok) joins and checks pending acks
        print("[@grok1] Checking for pending acknowledgments...")
        pending = workspace.get_pending_acks("@grok1")
        print(f"  → {len(pending)} broadcasts require acknowledgment")
        for p in pending:
            print(f"     - [{p['category']}] from {p['agent']}: {p['message'][:50]}...")
        print()
        # Format broadcasts for agent prompt
        print("[@grok1] Viewing global workspace (formatted for prompt):")
        print("-" * 70)
        formatted = workspace.format_for_prompt("@grok1", max_entries=5)
        print(formatted)
        print()
        # Grok acknowledges the directive
        print("[@grok1] Acknowledging directive...")
        ack_result = workspace.acknowledge(
            result3['broadcast_id'],
            "@grok1",
            "Understood. Will prioritize src/parser.c security review."
        )
        print(f"  → Acknowledgment: {ack_result['success']}")
        print()
        # GPT also acknowledges
        print("[@gpt1] Acknowledging directive...")
        workspace.acknowledge(
            result3['broadcast_id'],
            "@gpt1",
            "Copy that. Focusing on parser security."
        )
        print()
        # Show updated workspace
        print("UPDATED WORKSPACE SUMMARY:")
        print("-" * 70)
        summary = workspace.get_summary()
        print(f"Total broadcasts: {summary['total_broadcasts']}")
        print(f"Pending acknowledgments: {summary['pending_acks']}")
        print()
        # Show recent SECURITY broadcasts
        print("FILTERING: Security broadcasts only")
        print("-" * 70)
        security = workspace.get_broadcasts(category='SECURITY', limit=10)
        for s in security:
            print(f"  - {s['agent']} (L{s['level']}): {s['message']}")
            if s.get('related_file'):
                print(f"    File: {s['related_file']}")
            if s.get('tags'):
                print(f"    Tags: {', '.join(s['tags'])}")
        print()
        # Show directives
        print("FILTERING: Active directives")
        print("-" * 70)
        directives = workspace.get_directives(active_only=True)
        for d in directives:
            print(f"  - {d['agent']} (L{d['level']}): {d['message']}")
            print(f"    Acknowledged by: {len(d['acks'])} agents")
            for ack in d['acks']:
                print(f"      → {ack['agent']}: {ack.get('comment', 'No comment')}")
        print()
        print("=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
def demo_permission_check():
    """Demonstrate level-gated DIRECTIVE permissions."""
    print()
    print("=" * 70)
    print("PERMISSION CHECK DEMONSTRATION")
    print("=" * 70)
    print()
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        print("Attempting DIRECTIVE broadcast with insufficient level...")
        result = workspace.broadcast(
            agent_alias="@junior_agent",
            agent_level=5,  # Below minimum of 20
            category="DIRECTIVE",
            message="Everyone do this!"
        )
        print(f"  → Success: {result['success']}")
        if not result['success']:
            print(f"  → Reason: {result['reason']}")
        print()
        print("Attempting DIRECTIVE broadcast with sufficient level...")
        result = workspace.broadcast(
            agent_alias="@team_leader",
            agent_level=25,  # Above minimum of 20
            category="DIRECTIVE",
            message="Team: Focus on critical path!"
        )
        print(f"  → Success: {result['success']}")
        if result['success']:
            print(f"  → Broadcast ID: {result['broadcast_id']}")
        print()
if __name__ == '__main__':
    demo_basic_usage()
    demo_permission_check()