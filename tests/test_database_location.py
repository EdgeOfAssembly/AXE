#!/usr/bin/env python3
"""
Test script for database location fix.
Validates that the database is always created in the AXE installation directory,
not the workspace directory.
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.agent_db import AgentDatabase, get_database_path


def test_get_database_path():
    """Test that get_database_path returns the correct path."""
    print("Testing get_database_path()...")
    
    db_path = get_database_path()
    print(f"  Database path: {db_path}")
    
    # Verify it's an absolute path
    assert os.path.isabs(db_path), "Database path should be absolute"
    print("  ✓ Path is absolute")
    
    # Verify it ends with axe_agents.db
    assert db_path.endswith("axe_agents.db"), "Path should end with axe_agents.db"
    print("  ✓ Path ends with axe_agents.db")
    
    # Verify it's in the AXE installation directory
    # The database module is in database/, so AXE root is one level up
    database_module_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "agent_db.py")))
    axe_dir = os.path.dirname(database_module_dir)
    expected_path = os.path.join(axe_dir, "axe_agents.db")
    assert db_path == expected_path, f"Expected {expected_path}, got {db_path}"
    print(f"  ✓ Path is in AXE installation directory: {axe_dir}")
    
    print("✅ get_database_path() test PASSED\n")


def test_database_location_with_different_workspace():
    """Test that database is in AXE dir even when working in different directory."""
    print("Testing database location with different workspace...")
    
    # The database module is in database/, so AXE root is one level up
    database_module_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "agent_db.py")))
    axe_dir = os.path.dirname(database_module_dir)
    expected_db_path = os.path.join(axe_dir, "axe_agents.db")
    
    # Create temporary workspace directory
    with tempfile.TemporaryDirectory() as temp_workspace:
        print(f"  Workspace: {temp_workspace}")
        
        # Change to temp workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)
            print(f"  Changed to workspace: {os.getcwd()}")
            
            # Create database instance
            db = AgentDatabase()
            
            # Verify database path is NOT in the workspace
            assert db.db_path == expected_db_path, \
                f"Expected {expected_db_path}, got {db.db_path}"
            print(f"  ✓ Database path: {db.db_path}")
            
            assert not db.db_path.startswith(temp_workspace), \
                "Database should not be in workspace directory"
            print("  ✓ Database is NOT in workspace directory")
            
            assert db.db_path.startswith(axe_dir), \
                "Database should be in AXE installation directory"
            print("  ✓ Database IS in AXE installation directory")
            
        finally:
            os.chdir(original_cwd)
    
    print("✅ Database location test PASSED\n")


def test_database_tables_autocreate():
    """Test that tables are automatically created."""
    print("Testing database table auto-creation...")
    
    # Create database in temp location for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, "test_axe_agents.db")
        print(f"  Test database: {test_db_path}")
        
        # Ensure database doesn't exist
        assert not os.path.exists(test_db_path), "Test DB should not exist yet"
        print("  ✓ Test database doesn't exist yet")
        
        # Create database
        db = AgentDatabase(db_path=test_db_path)
        
        # Verify database file was created
        assert os.path.exists(test_db_path), "Database file should exist"
        print("  ✓ Database file created")
        
        # Verify tables exist
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
        
        print(f"  Tables found: {tables}")
        
        assert 'agent_state' in tables, "agent_state table should exist"
        print("  ✓ agent_state table exists")
        
        assert 'supervisor_log' in tables, "supervisor_log table should exist"
        print("  ✓ supervisor_log table exists")
        
        assert 'alias_mappings' in tables, "alias_mappings table should exist"
        print("  ✓ alias_mappings table exists")
    
    print("✅ Table auto-creation test PASSED\n")


def test_database_persistence_across_workspaces():
    """Test that agent data persists when switching workspaces."""
    print("Testing database persistence across workspaces...")
    
    # Create database in temp location for testing
    with tempfile.TemporaryDirectory() as temp_db_dir:
        test_db_path = os.path.join(temp_db_dir, "test_axe_agents.db")
        
        # Create workspace 1
        with tempfile.TemporaryDirectory() as workspace1:
            print(f"  Workspace 1: {workspace1}")
            original_cwd = os.getcwd()
            try:
                os.chdir(workspace1)
                
                # Create database and save agent state
                db1 = AgentDatabase(db_path=test_db_path)
                agent_id = "test_agent_123"
                db1.save_agent_state(
                    agent_id=agent_id,
                    alias="@test1",
                    model_name="test_model",
                    memory_dict={"key": "value"},
                    diffs=["diff1"],
                    error_count=0,
                    xp=100,
                    level=2
                )
                print("  ✓ Saved agent state in workspace 1")
                
            finally:
                os.chdir(original_cwd)
        
        # Create workspace 2 and verify data persists
        with tempfile.TemporaryDirectory() as workspace2:
            print(f"  Workspace 2: {workspace2}")
            try:
                os.chdir(workspace2)
                
                # Load database from same location
                db2 = AgentDatabase(db_path=test_db_path)
                state = db2.load_agent_state(agent_id)
                
                assert state is not None, "Agent state should exist"
                print("  ✓ Loaded agent state in workspace 2")
                
                assert state['alias'] == '@test1', "Agent alias should match"
                assert state['xp'] == 100, "Agent XP should match"
                assert state['level'] == 2, "Agent level should match"
                print("  ✓ Agent data persisted correctly")
                
            finally:
                os.chdir(original_cwd)
    
    print("✅ Persistence across workspaces test PASSED\n")


def test_empty_database_file():
    """Test that tables are created even if an empty database file exists."""
    print("Testing with empty database file...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, "empty_axe_agents.db")
        
        # Create an empty file
        Path(test_db_path).touch()
        print(f"  Created empty file: {test_db_path}")
        
        # Initialize database
        db = AgentDatabase(db_path=test_db_path)
        
        # Verify tables were created
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
        
        assert 'agent_state' in tables, "agent_state table should exist"
        assert 'supervisor_log' in tables, "supervisor_log table should exist"
        assert 'alias_mappings' in tables, "alias_mappings table should exist"
        print("  ✓ Tables created in empty database file")
    
    print("✅ Empty database file test PASSED\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("DATABASE LOCATION FIX TESTS")
    print("=" * 60)
    print()
    
    try:
        test_get_database_path()
        test_database_location_with_different_workspace()
        test_database_tables_autocreate()
        test_database_persistence_across_workspaces()
        test_empty_database_file()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"TEST FAILED ❌: {e}")
        print("=" * 60)
        return 1
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR ❌: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
