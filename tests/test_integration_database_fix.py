#!/usr/bin/env python3
"""
Integration test for database location fix.
Simulates the exact scenario from the problem statement where AXE
crashes with "no such table: agent_state" error.
"""
import os
import sys
import tempfile
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.agent_db import AgentDatabase, get_database_path


def simulate_problem_scenario():
    """Simulate the exact problem described in the issue."""
    print("=" * 70)
    print("SIMULATING PROBLEM SCENARIO")
    print("=" * 70)
    print()
    
    axe_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"AXE installation directory: {axe_dir}")
    print()
    
    # Simulate running AXE with a workspace like /tmp/playground
    with tempfile.TemporaryDirectory(prefix="playground_") as workspace:
        print(f"Workspace directory: {workspace}")
        print()
        
        # Change to workspace (simulates user running 'axe.py' from workspace)
        original_cwd = os.getcwd()
        try:
            os.chdir(workspace)
            print(f"Changed working directory to: {os.getcwd()}")
            print()
            
            # Before the fix, this would create database in workspace
            # After the fix, it should create in AXE installation directory
            print("Creating AgentDatabase instance...")
            db = AgentDatabase()
            print(f"  Database path: {db.db_path}")
            print()
            
            # Check where the database file is located
            if db.db_path.startswith(workspace):
                print("❌ PROBLEM: Database is in workspace directory!")
                print(f"   This would cause 'no such table' errors when switching workspaces")
                return False
            elif db.db_path.startswith(axe_dir):
                print("✅ FIXED: Database is in AXE installation directory!")
                print(f"   Agent data will persist across different workspace sessions")
            else:
                print("⚠️  WARNING: Database is in unexpected location!")
                return False
            
            print()
            
            # Try to use the database to ensure tables exist
            print("Testing database operations...")
            try:
                # This would cause a "no such table: agent_state" error if tables don't exist
                agent_id = "test_agent_123"
                db.save_agent_state(
                    agent_id=agent_id,
                    alias="@test",
                    model_name="test_model",
                    memory_dict={},
                    diffs=[],
                    error_count=0,
                    xp=0,
                    level=1
                )
                print("  ✓ save_agent_state() succeeded")
                
                state = db.load_agent_state(agent_id)
                assert state is not None
                print("  ✓ load_agent_state() succeeded")
                
                print()
                print("✅ No 'no such table: agent_state' error!")
                
            except Exception as e:
                print(f"❌ Database operation failed: {e}")
                return False
            
            print()
            
            # Verify tables exist
            print("Verifying database tables...")
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]
            
            print(f"  Tables: {', '.join(tables)}")
            
            required_tables = ['agent_state', 'supervisor_log', 'alias_mappings']
            for table in required_tables:
                if table in tables:
                    print(f"  ✓ {table} exists")
                else:
                    print(f"  ❌ {table} missing!")
                    return False
            
            print()
            
        finally:
            os.chdir(original_cwd)
    
    # Test switching to a different workspace
    print("-" * 70)
    print("Testing workspace switch...")
    print("-" * 70)
    print()
    
    with tempfile.TemporaryDirectory(prefix="project2_") as workspace2:
        print(f"New workspace directory: {workspace2}")
        print()
        
        try:
            os.chdir(workspace2)
            print(f"Changed working directory to: {os.getcwd()}")
            print()
            
            print("Creating new AgentDatabase instance...")
            db2 = AgentDatabase()
            print(f"  Database path: {db2.db_path}")
            print()
            
            # Verify it's the same database
            if db2.db_path == db.db_path:
                print("✅ Same database is used across workspaces!")
                print()
            else:
                print("❌ Different database files!")
                print(f"   First: {db.db_path}")
                print(f"   Second: {db2.db_path}")
                return False
            
            # Verify data persists
            print("Testing data persistence...")
            state = db2.load_agent_state("test_agent_123")
            if state is not None:
                print("  ✓ Agent data persisted from previous workspace")
                print(f"    Alias: {state['alias']}")
                print()
            else:
                print("  ❌ Agent data not found!")
                return False
            
        finally:
            os.chdir(original_cwd)
    
    return True


def main():
    """Run integration test."""
    success = simulate_problem_scenario()
    
    print("=" * 70)
    if success:
        print("INTEGRATION TEST PASSED ✅")
        print()
        print("The fix ensures:")
        print("  1. Database is always in AXE installation directory")
        print("  2. Agent XP/levels persist across workspace sessions")
        print("  3. No 'no such table: agent_state' errors")
        print("  4. Tables are auto-created")
    else:
        print("INTEGRATION TEST FAILED ❌")
    print("=" * 70)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
