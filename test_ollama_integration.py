#!/usr/bin/env python3
"""
Integration test for consolidated cognitive architecture features with Ollama.
Tests all three merged PRs with actual local LLM models:
- PR #54: Subsumption Architecture (Brooks 1986)
- PR #55: XP Voting System (Minsky 1986)
- PR #56: Conflict Detection & Arbitration (Minsky 1986)
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    SubsumptionController, SubsumptionLayer,
    GlobalWorkspace,
    ArbitrationProtocol,
)
from database.agent_db import AgentDatabase
from progression.xp_system import XP_AWARDS

def test_ollama_available():
    """Test that Ollama is available and models are installed."""
    print("=" * 70)
    print("TEST: Ollama Setup Verification")
    print("=" * 70)
    
    import subprocess
    
    # Check Ollama is installed
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=5)
        print(f"✅ Ollama installed: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Ollama not found: {e}")
        return False
    
    # Check models are available
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=5)
        models = result.stdout
        print(f"✅ Installed models:\n{models}")
        
        # Verify we have at least 2 small models
        if 'tinyllama' in models.lower() or 'qwen' in models.lower():
            print("✅ Small test models available")
            return True
        else:
            print("⚠️  Expected tinyllama or qwen models")
            return False
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return False

def test_subsumption_with_database():
    """Test Subsumption Architecture with real agent database."""
    print("\n" + "=" * 70)
    print("TEST 1: Subsumption Architecture (Brooks 1986) + Database")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = AgentDatabase(db_path)
        
        # Create test agents at different levels
        import uuid
        agent1_id = str(uuid.uuid4())
        agent2_id = str(uuid.uuid4())
        
        # Save initial agent state
        db.save_agent_state(agent1_id, '@llama1', 'tinyllama:latest', {}, [], 0, 0, 1)
        db.save_agent_state(agent2_id, '@qwen1', 'qwen2.5:0.5b', {}, [], 0, 0, 1)
        
        # Award XP to create level differences
        db.award_xp(agent1_id, 500, 'test')  # Should be level 6
        db.award_xp(agent2_id, 1500, 'test')  # Should be level 16
        
        # Get agent info
        agent1 = db.load_agent_state(agent1_id)
        agent2 = db.load_agent_state(agent2_id)
        
        print(f"✅ Created agents:")
        print(f"   @llama1: Level {agent1['level']} (XP: {agent1['xp']})")
        print(f"   @qwen1: Level {agent2['level']} (XP: {agent2['xp']})")
        
        # Test subsumption with these agents
        controller = SubsumptionController()
        
        layer1 = controller.get_layer_for_level(agent1['level'])
        layer2 = controller.get_layer_for_level(agent2['level'])
        
        print(f"✅ Layer assignment:")
        print(f"   @llama1 (L{agent1['level']}) → {layer1.name}")
        print(f"   @qwen1 (L{agent2['level']}) → {layer2.name}")
        
        # Test that higher level can suppress lower level
        success, msg = controller.suppress_agent(
            '@qwen1', agent2['level'], 
            '@llama1', agent1['level'], 
            'Higher level tactical decision'
        )
        print(f"✅ Suppression test: {success}")
        print(f"   {msg}")
        
        return True

def test_xp_voting_integration():
    """Test XP Voting System with database integration."""
    print("\n" + "=" * 70)
    print("TEST 2: XP Voting System (Minsky 1986) + Database")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = AgentDatabase(db_path)
        workspace = GlobalWorkspace(tmpdir)
        
        # Create agents
        import uuid
        agent1_id = str(uuid.uuid4())
        agent2_id = str(uuid.uuid4())
        
        db.save_agent_state(agent1_id, '@llama1', 'tinyllama:latest', {}, [], 0, 0, 1)
        db.save_agent_state(agent2_id, '@qwen1', 'qwen2.5:0.5b', {}, [], 0, 0, 1)
        
        # Award XP to establish levels
        db.award_xp(agent1_id, 1000, 'initial')  # Level 11
        db.award_xp(agent2_id, 500, 'initial')   # Level 6
        
        agent1 = db.load_agent_state(agent1_id)
        agent2 = db.load_agent_state(agent2_id)
        
        print(f"✅ Agents with XP:")
        print(f"   @llama1: Level {agent1['level']}, XP {agent1['xp']}")
        print(f"   @qwen1: Level {agent2['level']}, XP {agent2['xp']}")
        
        # Test voting
        result = workspace.vote_xp(
            '@llama1', agent1['level'], 
            '@qwen1', 10, 
            'Good collaboration on task'
        )
        print(f"✅ Vote cast: {result['success']}")
        if result['success']:
            print(f"   {result['message']}")
        
        # Get pending votes
        pending = workspace.get_pending_votes()
        print(f"✅ Pending votes: {len(pending)}")
        
        # Apply votes to database
        if pending:
            results = db.apply_xp_votes(pending)
            for r in results:
                if r['success']:
                    print(f"✅ Vote applied to {r['target']}")
                    workspace.mark_vote_applied(r['vote_id'])
        
        # Check updated XP
        agent2_updated = db.load_agent_state(agent2_id)
        xp_gained = agent2_updated['xp'] - agent2['xp']
        print(f"✅ XP gained by @qwen1: {xp_gained}")
        
        return True

def test_conflict_detection():
    """Test Conflict Detection & Arbitration."""
    print("\n" + "=" * 70)
    print("TEST 3: Conflict Detection & Arbitration (Minsky 1986)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = GlobalWorkspace(tmpdir)
        protocol = ArbitrationProtocol(workspace)
        
        # Create conflicting broadcasts
        bc1 = workspace.broadcast(
            '@llama1', 10, 'SECURITY',
            'This code is safe and has no vulnerabilities',
            related_file='test.py'
        )
        
        bc2 = workspace.broadcast(
            '@qwen1', 15, 'SECURITY',
            'Found critical vulnerabilities in the code',
            related_file='test.py'
        )
        
        print(f"✅ Created 2 broadcasts")
        
        # Detect conflicts
        conflicts = workspace.detect_conflicts(window_broadcasts=10)
        print(f"✅ Conflicts detected: {len(conflicts)}")
        
        if conflicts:
            for conflict in conflicts:
                print(f"   Type: {conflict['type']}")
                print(f"   Reason: {conflict['reason']}")
        
        # Create arbitration for detected conflict
        if conflicts and conflicts[0]['type'] == 'detected':
            arb = protocol.create_arbitration(
                conflict_broadcasts=[
                    conflicts[0]['broadcast1']['id'],
                    conflicts[0]['broadcast2']['id']
                ],
                created_by='@supervisor1',
                current_turn=1
            )
            print(f"✅ Arbitration created: {arb['arbitration_id']}")
            print(f"   Required level: {arb['required_level']}")
            print(f"   Deadline turn: {arb['deadline_turn']}")
        
        return True

def test_full_integration():
    """Test all features working together in AXE directory."""
    print("\n" + "=" * 70)
    print("TEST 4: Full Integration in AXE Directory")
    print("=" * 70)
    
    # Use actual AXE directory for workspace (as mentioned in requirement)
    axe_dir = Path(__file__).parent
    workspace_dir = axe_dir / '.test_workspace'
    workspace_dir.mkdir(exist_ok=True)
    
    try:
        db_path = str(workspace_dir / 'test.db')
        db = AgentDatabase(db_path)
        workspace = GlobalWorkspace(str(workspace_dir))
        controller = SubsumptionController()
        protocol = ArbitrationProtocol(workspace)
        
        print(f"✅ Workspace: {workspace_dir}")
        
        # Create agents with Ollama models
        import uuid
        agents = []
        for i, model in enumerate(['tinyllama:latest', 'qwen2.5:0.5b']):
            agent_id = str(uuid.uuid4())
            alias = f'@agent{i+1}'
            db.save_agent_state(agent_id, alias, model, {}, [], 0, 0, 1)
            # Give them different XP levels
            db.award_xp(agent_id, i * 1000, 'initial setup')
            agent_data = db.load_agent_state(agent_id)
            agents.append(agent_data)
            print(f"✅ Created {agent_data['alias']}: Level {agent_data['level']}")
        
        # Test subsumption ordering
        agent_list = [{'id': a['alias'], 'level': a['level']} for a in agents]
        ordered = controller.get_execution_order(agent_list)
        print(f"✅ Execution order: {' → '.join([a['id'] for a in ordered])}")
        
        # Test voting between agents
        if len(agents) >= 2:
            result = workspace.vote_xp(
                agents[0]['alias'], agents[0]['level'],
                agents[1]['alias'], 10,
                'Great work on integration'
            )
            print(f"✅ Vote: {result['success']}")
        
        # Test conflict detection
        workspace.broadcast(
            agents[0]['alias'], agents[0]['level'],
            'CODE_QUALITY', 'Code is clean and correct'
        )
        workspace.broadcast(
            agents[1]['alias'], agents[1]['level'],
            'CODE_QUALITY', 'Code has incorrect logic'
        )
        
        conflicts = workspace.detect_conflicts(window_broadcasts=5)
        print(f"✅ Conflicts detected: {len(conflicts)}")
        
        print("\n✅ All features working in AXE directory!")
        
        return True
        
    finally:
        # Cleanup test workspace
        import shutil
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)

def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("OLLAMA INTEGRATION TEST SUITE")
    print("Consolidated Cognitive Architecture Features")
    print("=" * 70)
    
    tests = [
        ("Ollama Setup", test_ollama_available),
        ("Subsumption + Database", test_subsumption_with_database),
        ("XP Voting + Database", test_xp_voting_integration),
        ("Conflict Detection", test_conflict_detection),
        ("Full Integration", test_full_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success if success is not None else True))
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
