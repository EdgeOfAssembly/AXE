#!/usr/bin/env python3
"""
Test script for axe.py improvements (rules, aliases, XP, SQLite, resources).
Phases 1-10: Full feature test coverage.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.agent_db import AgentDatabase
from progression.xp_system import calculate_xp_for_level
from progression.levels import (
    get_title_for_level,
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER,
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE
)
from safety.rules import SESSION_RULES
from managers.sleep_manager import SleepManager
from managers.break_system import BreakSystem
from managers.emergency_mailbox import EmergencyMailbox
from managers.dynamic_spawner import DynamicSpawner
from core.constants import (
    MAX_WORK_HOURS,
    MIN_SLEEP_MINUTES,
    ERROR_THRESHOLD_PERCENT,
    MAX_BREAK_MINUTES,
    MAX_BREAKS_PER_HOUR,
    MIN_ACTIVE_AGENTS,
    MAX_TOTAL_AGENTS,
)
from core.config import Config


def test_xp_calculation():
    """Test XP calculation for different levels."""
    print("Testing XP calculation...")
    
    # Test linear progression (levels 1-10)
    assert calculate_xp_for_level(1) == 0, "Level 1 should require 0 XP"
    assert calculate_xp_for_level(2) == 100, "Level 2 should require 100 XP"
    assert calculate_xp_for_level(10) == 900, "Level 10 should require 900 XP"
    
    # Test non-linear progression
    xp_level_20 = calculate_xp_for_level(20)
    xp_level_30 = calculate_xp_for_level(30)
    xp_level_40 = calculate_xp_for_level(40)
    
    print(f"  Level 10: {calculate_xp_for_level(10)} XP")
    print(f"  Level 20: {xp_level_20} XP")
    print(f"  Level 30: {xp_level_30} XP")
    print(f"  Level 40: {xp_level_40} XP")
    
    # Verify progression is increasing
    assert xp_level_20 > calculate_xp_for_level(10), "Level 20 should require more XP than level 10"
    assert xp_level_30 > xp_level_20, "Level 30 should require more XP than level 20"
    assert xp_level_40 > xp_level_30, "Level 40 should require more XP than level 30"
    
    print("✓ XP calculation tests passed!")


def test_titles():
    """Test title assignment for different levels."""
    print("\nTesting title system...")
    
    assert get_title_for_level(1) == "Worker"
    assert get_title_for_level(5) == "Worker"
    assert get_title_for_level(10) == "Senior Worker"
    assert get_title_for_level(15) == "Senior Worker"
    assert get_title_for_level(20) == "Team Leader"
    assert get_title_for_level(25) == "Team Leader"
    assert get_title_for_level(30) == "Deputy Supervisor"
    assert get_title_for_level(35) == "Deputy Supervisor"
    assert get_title_for_level(40) == "Supervisor-Eligible"
    
    print(f"  Level 1: {get_title_for_level(1)}")
    print(f"  Level 10: {get_title_for_level(10)}")
    print(f"  Level 20: {get_title_for_level(20)}")
    print(f"  Level 30: {get_title_for_level(30)}")
    print(f"  Level 40: {get_title_for_level(40)}")
    
    print("✓ Title system tests passed!")


def test_database():
    """Test SQLite database functionality."""
    print("\nTesting database operations...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        
        # Test agent creation
        agent_id = "test-agent-1"
        db.save_agent_state(
            agent_id=agent_id,
            alias="@llama1",
            model_name="meta-llama/Llama-3.1-70B-Instruct",
            memory_dict={"context": "test"},
            diffs=["diff1", "diff2"],
            error_count=0,
            xp=0,
            level=1
        )
        
        # Test loading agent
        state = db.load_agent_state(agent_id)
        assert state is not None, "Agent should exist in database"
        assert state['alias'] == "@llama1"
        assert state['level'] == 1
        assert state['xp'] == 0
        print(f"  Created and loaded agent: {state['alias']}")
        
        # Test XP award and level-up
        result = db.award_xp(agent_id, 500, "Test task")
        assert result['xp'] == 500
        assert result['leveled_up'] is True
        assert result['new_level'] > 1
        print(f"  Awarded 500 XP: Level {result['old_level']} → {result['new_level']}")
        
        # Test multiple level-ups
        result = db.award_xp(agent_id, 10000, "Big task")
        print(f"  Awarded 10000 XP: Level {result['old_level']} → {result['new_level']}")
        print(f"  New title: {result.get('new_title', 'N/A')}")
        
        # Test alias numbering
        next_num = db.get_next_agent_number("llama")
        assert next_num == 2, "Next llama number should be 2"
        print(f"  Next agent number for 'llama': {next_num}")
        
        # Test alias collision detection
        assert db.alias_exists("@llama1") is True
        assert db.alias_exists("@llama999") is False
        
        # Test supervisor log
        db.log_supervisor_event(
            supervisor_id="boss-1",
            event_type="spawn_agent",
            details={"agent": "llama1", "reason": "high load"}
        )
        print("  Logged supervisor event")
        
        print("✓ Database tests passed!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        # Also remove WAL files if they exist
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


def test_session_rules():
    """Test that session rules are defined and formatted correctly."""
    print("\nTesting session rules...")
    
    assert SESSION_RULES is not None, "SESSION_RULES should be defined"
    assert len(SESSION_RULES) > 100, "SESSION_RULES should have content"
    assert "MISSION FIRST" in SESSION_RULES
    assert "RESPECT & WELL-BEING" in SESSION_RULES
    assert "CHAIN OF COMMAND" in SESSION_RULES
    assert "PERFORMANCE & REWARDS" in SESSION_RULES
    
    print("  Rules contain all 4 core principles")
    print(f"  Total length: {len(SESSION_RULES)} characters")
    print("✓ Session rules tests passed!")


# ========== Phase 6 Tests: Mandatory Sleep System ==========

def test_sleep_system():
    """Test the mandatory sleep system (Phase 6)."""
    print("\nTesting mandatory sleep system (Phase 6)...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        sleep_mgr = SleepManager(db)
        
        # Create test agent
        agent_id = "test-sleep-agent"
        db.save_agent_state(
            agent_id=agent_id,
            alias="@llama1",
            model_name="test-model",
            memory_dict={},
            diffs=[],
            error_count=0,
            xp=0,
            level=1
        )
        
        # Test work tracking
        db.start_work_tracking(agent_id)
        work_duration = db.get_work_duration_minutes(agent_id)
        assert work_duration >= 0, "Work duration should be >= 0"
        print(f"  Work tracking started, duration: {work_duration} minutes")
        
        # Test sleep check (should not need sleep immediately)
        needs_sleep, msg = db.check_mandatory_sleep(agent_id)
        assert needs_sleep is False, "Agent should not need sleep immediately"
        print(f"  Immediate sleep check: {needs_sleep}, {msg}")
        
        # Test putting agent to sleep
        sleep_result = db.put_agent_to_sleep(agent_id, "test_sleep", 15)
        assert sleep_result['alias'] == "@llama1"
        assert sleep_result['sleep_duration_minutes'] == 15
        print(f"  Agent put to sleep: {sleep_result['alias']} for {sleep_result['sleep_duration_minutes']} min")
        
        # Test sleeping agents list
        sleeping = db.get_sleeping_agents()
        assert len(sleeping) == 1
        assert sleeping[0]['alias'] == "@llama1"
        print(f"  Sleeping agents count: {len(sleeping)}")
        
        # Test waking agent
        wake_result = db.wake_agent(agent_id)
        assert wake_result['status'] == 'active'
        print(f"  Agent woken: {wake_result['alias']}")
        
        # Test active agents list
        active = db.get_active_agents()
        assert len(active) == 1
        print(f"  Active agents count: {len(active)}")
        
        # Test sleep manager status
        status = sleep_mgr.get_status_summary()
        assert 'active_count' in status
        assert 'sleeping_count' in status
        print(f"  Sleep manager status: Active={status['active_count']}, Sleeping={status['sleeping_count']}")
        
        print("✓ Mandatory sleep system tests passed!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


# ========== Phase 7 Tests: Degradation Monitoring ==========

def test_degradation_monitoring():
    """Test the degradation monitoring system (Phase 7)."""
    print("\nTesting degradation monitoring (Phase 7)...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        
        # Create test agent
        agent_id = "test-degrade-agent"
        db.save_agent_state(
            agent_id=agent_id,
            alias="@test1",
            model_name="test-model",
            memory_dict={},
            diffs=[],
            error_count=0,
            xp=0,
            level=1
        )
        
        # Test recording diffs with no errors
        db.record_diff(agent_id, "diff content 1", error_count=0)
        db.record_diff(agent_id, "diff content 2", error_count=0)
        db.record_diff(agent_id, "diff content 3", error_count=0)
        
        error_rate = db.get_error_rate(agent_id)
        assert error_rate == 0.0, f"Error rate should be 0, got {error_rate}"
        print(f"  Error rate with no errors: {error_rate}%")
        
        # Test recording diffs with errors
        for i in range(10):
            db.record_diff(agent_id, f"diff with errors {i}", error_count=5)
        
        error_rate = db.get_error_rate(agent_id)
        assert error_rate > 0, "Error rate should be > 0 after adding errors"
        print(f"  Error rate after errors: {error_rate:.1f}%")
        
        # Test degradation check
        degraded, msg = db.check_degradation(agent_id)
        print(f"  Degradation check: {degraded}, {msg}")
        
        print("✓ Degradation monitoring tests passed!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


# ========== Phase 8 Tests: Emergency Mailbox ==========

def test_emergency_mailbox():
    """Test the emergency mailbox system (Phase 8)."""
    print("\nTesting emergency mailbox (Phase 8)...")
    
    # Create temporary mailbox directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        mailbox = EmergencyMailbox(tmp_dir)
        
        # Test sending a report
        success, result = mailbox.send_report(
            agent_alias="@llama1",
            report_type="test_report",
            subject="Test Emergency",
            details="This is a test emergency message for Phase 8 testing."
        )
        
        assert success is True, "Report should be sent successfully"
        assert result.endswith('.gpg'), "Report filename should end with .gpg"
        print(f"  Report sent: {result}")
        
        # Test listing reports
        reports = mailbox.list_reports()
        assert len(reports) == 1, "Should have 1 report"
        assert reports[0]['filename'] == result
        print(f"  Reports in mailbox: {len(reports)}")
        
        # Send another report
        success2, result2 = mailbox.send_report(
            agent_alias="@grok1",
            report_type="supervisor_issue",
            subject="Supervisor Behavior",
            details="Testing supervisor abuse reporting pathway."
        )
        
        assert success2 is True
        reports = mailbox.list_reports()
        assert len(reports) == 2
        print(f"  Total reports after second send: {len(reports)}")
        
        # Test report details
        for report in reports:
            assert 'filename' in report
            assert 'size' in report
            assert 'created' in report
            assert report['size'] > 0
        
        print("✓ Emergency mailbox tests passed!")


# ========== Phase 9 Tests: Break System ==========

def test_break_system():
    """Test the break system (Phase 9)."""
    print("\nTesting break system (Phase 9)...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        break_sys = BreakSystem(db)
        
        # Create multiple test agents (need 3+ to allow breaks since max 40% can be on break)
        for i in range(5):
            db.save_agent_state(
                agent_id=f"test-agent-{i}",
                alias=f"@llama{i}",
                model_name="test-model",
                memory_dict={},
                diffs=[],
                error_count=0,
                xp=0,
                level=1
            )
        
        agent_id = "test-agent-0"
        
        # Test break request
        request = break_sys.request_break(
            agent_id=agent_id,
            alias="@llama0",
            break_type="coffee",
            justification="Need to recharge after intensive task"
        )
        
        assert request['status'] == 'pending'
        assert request['break_type'] == 'coffee'
        print(f"  Break requested: {request['id'][:8]}...")
        
        # Test pending requests
        pending = break_sys.get_pending_requests()
        assert len(pending) == 1
        print(f"  Pending requests: {len(pending)}")
        
        # Test break approval (with 5 agents, 1 on break = 20% which is < 40%)
        result = break_sys.approve_break(request['id'], duration_minutes=10)
        assert result['approved'] is True, f"Break should be approved but got: {result}"
        assert result['duration_minutes'] <= MAX_BREAK_MINUTES
        print(f"  Break approved: {result['duration_minutes']} minutes")
        
        # Test break status
        status = break_sys.get_status()
        assert status['agents_on_break'] == 1
        print(f"  Agents on break: {status['agents_on_break']}")
        
        # Test can_take_break limits
        # Record multiple breaks to test the limit
        db.record_break(agent_id, "coffee", 10)
        db.record_break(agent_id, "coffee", 10)
        
        breaks_count = db.get_breaks_in_last_hour(agent_id)
        print(f"  Breaks in last hour: {breaks_count}")
        
        print("✓ Break system tests passed!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


# ========== Phase 10 Tests: Dynamic Spawning ==========

def test_dynamic_spawning():
    """Test the dynamic spawning system (Phase 10)."""
    print("\nTesting dynamic spawning (Phase 10)...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        config = Config()
        spawner = DynamicSpawner(db, config)
        
        # Test can_spawn (should be allowed initially)
        can, msg = spawner.can_spawn()
        assert can is True, f"Should be able to spawn initially: {msg}"
        print(f"  Initial spawn check: {can}, {msg}")
        
        # Test spawning an agent
        result = spawner.spawn_agent(
            model_name="meta-llama/Llama-3.1-70B-Instruct",
            provider="huggingface",
            supervisor_id="supervisor-1",
            reason="Testing spawn functionality"
        )
        
        assert result['spawned'] is True
        assert result['alias'].startswith('@')
        print(f"  Agent spawned: {result['alias']}")
        
        # Test spawn cooldown
        can, msg = spawner.can_spawn()
        assert can is False, "Should be in cooldown"
        assert "cooldown" in msg.lower()
        print(f"  Spawn cooldown check: {can}, {msg}")
        
        # Test spawn history
        history = spawner.get_spawn_history()
        assert len(history) == 1
        assert history[0]['alias'] == result['alias']
        print(f"  Spawn history entries: {len(history)}")
        
        # Test auto-spawn decision
        should_spawn, reason = spawner.should_auto_spawn(task_complexity=0.8)
        print(f"  Auto-spawn decision (complexity 0.8): {should_spawn}, {reason}")
        
        print("✓ Dynamic spawning tests passed!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


def main():
    """Run all tests."""
    print("=" * 70)
    print("AXE.PY IMPROVEMENTS TEST SUITE (Phases 1-10)")
    print("=" * 70)
    
    try:
        # Original Phase 1-5 tests
        test_xp_calculation()
        test_titles()
        test_database()
        test_session_rules()
        
        # New Phase 6-10 tests
        test_sleep_system()
        test_degradation_monitoring()
        test_emergency_mailbox()
        test_break_system()
        test_dynamic_spawning()
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✓ (Phases 1-10)")
        print("=" * 70)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
