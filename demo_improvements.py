#!/usr/bin/env python3
"""
Demonstration of axe.py improvements without requiring API keys.

This script simulates a collaborative session to showcase:
- Session rules display
- Agent aliasing (@boss, @worker1, etc.)
- XP and level progression
- SQLite persistence
- Resource monitoring

Run with: python3 demo_improvements.py
"""
import os
import sys
import tempfile
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import (
    AgentDatabase,
    SESSION_RULES,
    calculate_xp_for_level,
    get_title_for_level,
    colorize,
    Colors,
    collect_resources,
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER,
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE
)

c = colorize


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(c(f" {title} ", Colors.CYAN + Colors.BOLD))
    print("=" * 80 + "\n")


def demo_session_rules():
    """Demonstrate the session rules display."""
    print_section("DEMO 1: Session Rules Display")
    print(c(SESSION_RULES, Colors.CYAN))


def demo_xp_progression():
    """Demonstrate XP and level progression."""
    print_section("DEMO 2: XP & Level Progression System")
    
    levels_to_show = [1, 5, 10, 15, 20, 25, 30, 35, 40]
    
    print(c("Level Progression Table:", Colors.BOLD))
    print(c("-" * 80, Colors.DIM))
    print(f"{'Level':<8} {'Total XP':<12} {'XP to Next':<12} {'Title':<25}")
    print(c("-" * 80, Colors.DIM))
    
    for level in levels_to_show:
        xp_total = calculate_xp_for_level(level)
        xp_next = calculate_xp_for_level(level + 1) - xp_total if level < 40 else 0
        title = get_title_for_level(level)
        
        color = Colors.GREEN if level in [10, 20, 30, 40] else Colors.DIM
        print(c(f"{level:<8} {xp_total:<12} {xp_next:<12} {title:<25}", color))
    
    print(c("-" * 80, Colors.DIM))


def demo_aliasing():
    """Demonstrate agent aliasing system."""
    print_section("DEMO 3: Agent Aliasing System")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        
        # Simulate creating multiple agents
        agents = [
            ("supervisor-001", "@boss", "claude-3-5-sonnet", 40, "Supervisor"),
            ("llama-001", "@llama1", "meta-llama/Llama-3.1-70B", 1, "Worker"),
            ("llama-002", "@llama2", "meta-llama/Llama-3.1-70B", 1, "Worker"),
            ("grok-001", "@grok1", "grok-beta", 1, "Worker"),
            ("copilot-001", "@copilot1", "openai/gpt-4o", 1, "Worker"),
        ]
        
        print(c("╔══════════════════════════════════════════════════════════════════════════════╗", Colors.GREEN))
        print(c("║                           PARTICIPATING AGENTS                               ║", Colors.GREEN))
        print(c("╚══════════════════════════════════════════════════════════════════════════════╝", Colors.GREEN))
        print()
        
        for agent_id, alias, model, level, role in agents:
            db.save_agent_state(
                agent_id=agent_id,
                alias=alias,
                model_name=model,
                memory_dict={},
                diffs=[],
                error_count=0,
                xp=calculate_xp_for_level(level),
                level=level
            )
            
            title = get_title_for_level(level)
            xp = calculate_xp_for_level(level)
            role_indicator = " [SUPERVISOR]" if alias == "@boss" else ""
            
            print(c(f"  {alias:20} Level {level:2} ({xp:6} XP)  {title}{role_indicator}", Colors.GREEN))
        
        print()
        
        # Demonstrate conversation with aliases
        print(c("Sample Conversation:", Colors.BOLD))
        print(c("-" * 80, Colors.DIM))
        print(c("@boss", Colors.CYAN) + ": @llama1, please review the authentication module")
        print(c("@llama1", Colors.CYAN) + ": @boss, I found 3 security issues. @copilot1 can you verify?")
        print(c("@copilot1", Colors.CYAN) + ": @llama1, confirmed. I'll create a PR with fixes")
        print(c("@grok1", Colors.CYAN) + ": @boss, I can add test coverage for those fixes")
        print(c("@boss", Colors.CYAN) + ": Great teamwork! @grok1, proceed with the tests")
        print(c("-" * 80, Colors.DIM))
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


def demo_level_ups():
    """Demonstrate level-up mechanics."""
    print_section("DEMO 4: Level-Up Mechanics")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        
        # Create an agent
        agent_id = "demo-agent"
        db.save_agent_state(
            agent_id=agent_id,
            alias="@llama1",
            model_name="meta-llama/Llama-3.1-70B",
            memory_dict={},
            diffs=[],
            error_count=0,
            xp=0,
            level=1
        )
        
        print(c("Starting agent: @llama1 at Level 1 with 0 XP", Colors.BOLD))
        print()
        
        # Simulate XP awards
        scenarios = [
            (50, "Turn contribution"),
            (50, "Turn contribution"),
            (50, "Turn contribution"),
            (200, "Task completion bonus"),
            (500, "Exceptional code review"),
            (1000, "Major bug fix"),
            (5000, "Critical security patch"),
        ]
        
        for xp_award, reason in scenarios:
            result = db.award_xp(agent_id, xp_award, reason)
            
            if result['leveled_up']:
                print(c(f"🎉 @llama1 LEVELED UP! Level {result['old_level']} → {result['new_level']}", 
                       Colors.GREEN + Colors.BOLD))
                print(c(f"   New Title: {result['new_title']}", Colors.GREEN))
                print(c(f"   Total XP: {result['xp']}", Colors.DIM))
                print(c(f"   Reason: {reason} (+{xp_award} XP)", Colors.DIM))
            else:
                print(f"   +{xp_award} XP for {reason} (Total: {result['xp']} XP, Level {result['new_level']})")
            
            print()
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


def demo_persistence():
    """Demonstrate SQLite persistence."""
    print_section("DEMO 5: SQLite Persistence")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        print(colorize(f"Database created at: {db_path}", Colors.DIM))
        print()
        
        # Initialize database
        db = AgentDatabase(db_path)
        
        # Create multiple agents
        print(colorize("Creating agents...", Colors.BOLD))
        for i in range(1, 4):
            agent_id = f"agent-{i}"
            alias = f"@llama{i}"
            xp = i * 1000  # Different XP for each
            level = 1
            
            # Calculate actual level based on XP
            while level < 40:
                if xp >= calculate_xp_for_level(level + 1):
                    level += 1
                else:
                    break
            
            db.save_agent_state(
                agent_id=agent_id,
                alias=alias,
                model_name="meta-llama/Llama-3.1-70B",
                memory_dict={"context": f"Agent {i} memory"},
                diffs=[f"diff-{i}-1", f"diff-{i}-2"],
                error_count=0,
                xp=xp,
                level=level
            )
            print(f"  Created {alias} at Level {level} with {xp} XP")
        
        print()
        
        # Load agents back
        print(colorize("Loading agents from database...", Colors.BOLD))
        for i in range(1, 4):
            agent_id = f"agent-{i}"
            state = db.load_agent_state(agent_id)
            
            if state:
                print(f"  Loaded {state['alias']}: Level {state['level']}, {state['xp']} XP, {len(state['diffs'])} diffs")
        
        print()
        print(colorize("✓ All agent states persisted and recovered successfully!", Colors.GREEN))
        
        # Show database file info
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM agent_state")
            agent_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM supervisor_log")
            log_count = cursor.fetchone()[0]
        
        print()
        print(colorize("Database Statistics:", Colors.BOLD))
        print(f"  Agents stored: {agent_count}")
        print(f"  Supervisor log entries: {log_count}")
        print(f"  WAL mode: Enabled (better concurrency)")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)


def demo_resources():
    """Demonstrate resource monitoring."""
    print_section("DEMO 6: Resource Monitoring")
    
    print(c("Collecting system resources...", Colors.BOLD))
    print()
    
    resources = collect_resources()
    
    # Display resource snapshot
    print(c("=" * 80, Colors.DIM))
    print(resources)
    print(c("=" * 80, Colors.DIM))
    print()
    
    print(c("In a real session:", Colors.BOLD))
    print("  • This data is written to /tmp/axe_resources.txt every 60 seconds")
    print("  • Supervisor can read it to make spawn/sleep decisions")
    print("  • Helps prevent system overload")


def demo_sleep_system():
    """Demonstrate the mandatory sleep system (Phase 6)."""
    print_section("DEMO 7: Mandatory Sleep System (Phase 6)")
    
    # Import additional classes
    from axe import SleepManager, MAX_WORK_HOURS, MIN_SLEEP_MINUTES
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        sleep_mgr = SleepManager(db)
        
        # Create test agent
        agent_id = "demo-sleep-agent"
        db.save_agent_state(
            agent_id=agent_id,
            alias="@llama1",
            model_name="meta-llama/Llama-3.1-70B",
            memory_dict={},
            diffs=[],
            error_count=0,
            xp=500,
            level=5
        )
        
        print(c("Sleep System Configuration:", Colors.BOLD))
        print(f"  • Maximum work hours: {MAX_WORK_HOURS} hours")
        print(f"  • Minimum sleep duration: {MIN_SLEEP_MINUTES} minutes")
        print()
        
        # Start work tracking
        db.start_work_tracking(agent_id)
        print(c("Work tracking started for @llama1", Colors.GREEN))
        
        # Check if needs sleep
        needs_sleep, msg = db.check_mandatory_sleep(agent_id)
        print(f"  Current work duration: {db.get_work_duration_minutes(agent_id)} minutes")
        print(f"  Needs sleep: {needs_sleep}")
        print()
        
        # Demonstrate putting agent to sleep
        print(c("Putting agent to sleep...", Colors.YELLOW))
        result = db.put_agent_to_sleep(agent_id, "demo_test", 15)
        print(f"  {result['alias']} is now sleeping")
        print(f"  Reason: {result['reason']}")
        print(f"  Duration: {result['sleep_duration_minutes']} minutes")
        print()
        
        # Get status
        status = sleep_mgr.get_status_summary()
        print(c("Sleep Manager Status:", Colors.BOLD))
        print(f"  Active agents: {status['active_count']}")
        print(f"  Sleeping agents: {status['sleeping_count']}")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            if os.path.exists(db_path + ext):
                os.unlink(db_path + ext)


def demo_emergency_mailbox():
    """Demonstrate the emergency mailbox system (Phase 8)."""
    print_section("DEMO 8: Emergency Mailbox (Phase 8)")
    
    from axe import EmergencyMailbox
    
    # Create temporary mailbox
    with tempfile.TemporaryDirectory() as tmp_dir:
        mailbox = EmergencyMailbox(tmp_dir)
        
        print(c("Emergency Mailbox Configuration:", Colors.BOLD))
        print(f"  • Location: {tmp_dir}")
        print(f"  • Access: Workers write-only, supervisor denied")
        print()
        
        # Send encrypted report
        print(c("Sending encrypted emergency report from @llama1...", Colors.YELLOW))
        success, filename = mailbox.send_report(
            agent_alias="@llama1",
            report_type="supervisor_issue",
            subject="Testing Emergency Channel",
            details="This is a demonstration of the emergency mailbox system. "
                   "Workers can send encrypted reports that only humans can read."
        )
        
        if success:
            print(c(f"  ✓ Report saved: {filename}", Colors.GREEN))
        
        # List reports
        reports = mailbox.list_reports()
        print()
        print(c("Mailbox Contents:", Colors.BOLD))
        for report in reports:
            print(f"  📧 {report['filename']}")
            print(f"     Size: {report['size']} bytes")
            print(f"     Created: {report['created']}")
        
        print()
        print(c("Security Features:", Colors.DIM))
        print("  • Messages are encrypted (base64 + key derivation)")
        print("  • In production, use GPG for full encryption")
        print("  • Supervisor cannot access this directory")


def demo_break_system():
    """Demonstrate the break system (Phase 9)."""
    print_section("DEMO 9: Break System (Phase 9)")
    
    from axe import BreakSystem, MAX_BREAK_MINUTES, MAX_BREAKS_PER_HOUR
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        break_sys = BreakSystem(db)
        
        # Create multiple agents
        for i in range(5):
            db.save_agent_state(
                agent_id=f"demo-agent-{i}",
                alias=f"@worker{i}",
                model_name="test-model",
                memory_dict={},
                diffs=[],
                error_count=0,
                xp=100 * i,
                level=1 + i
            )
        
        print(c("Break System Configuration:", Colors.BOLD))
        print(f"  • Max break duration: {MAX_BREAK_MINUTES} minutes")
        print(f"  • Max breaks per hour: {MAX_BREAKS_PER_HOUR}")
        print(f"  • Max workforce on break: 40%")
        print()
        
        # Submit break request
        print(c("@worker1 requesting coffee break...", Colors.CYAN))
        request = break_sys.request_break(
            agent_id="demo-agent-1",
            alias="@worker1",
            break_type="coffee",
            justification="Need to recharge after intensive code review"
        )
        print(f"  Request ID: {request['id'][:8]}...")
        print(f"  Status: {request['status']}")
        print()
        
        # Approve break
        print(c("@boss approving break request...", Colors.GREEN))
        result = break_sys.approve_break(request['id'], duration_minutes=10)
        if result['approved']:
            print(f"  ✓ Break approved for {result['duration_minutes']} minutes")
            print(f"  Ends at: {result['ends_at']}")
        else:
            print(f"  ✗ Break denied: {result['reason']}")
        
        print()
        print(c("Break System Status:", Colors.BOLD))
        status = break_sys.get_status()
        print(f"  Agents on break: {status['agents_on_break']}")
        print(f"  Pending requests: {status['pending_requests']}")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            if os.path.exists(db_path + ext):
                os.unlink(db_path + ext)


def demo_dynamic_spawning():
    """Demonstrate dynamic spawning (Phase 10)."""
    print_section("DEMO 10: Dynamic Spawning (Phase 10)")
    
    from axe import DynamicSpawner, Config, MIN_ACTIVE_AGENTS, MAX_TOTAL_AGENTS
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = AgentDatabase(db_path)
        config = Config()
        spawner = DynamicSpawner(db, config)
        
        print(c("Dynamic Spawning Configuration:", Colors.BOLD))
        print(f"  • Minimum active agents: {MIN_ACTIVE_AGENTS}")
        print(f"  • Maximum total agents: {MAX_TOTAL_AGENTS}")
        print(f"  • Spawn cooldown: 60 seconds")
        print()
        
        # Check if can spawn
        can_spawn, reason = spawner.can_spawn()
        print(c("Checking spawn availability:", Colors.CYAN))
        print(f"  Can spawn: {can_spawn}")
        print(f"  Reason: {reason}")
        print()
        
        # Spawn a new agent
        print(c("Spawning new Llama agent...", Colors.GREEN))
        result = spawner.spawn_agent(
            model_name="meta-llama/Llama-3.1-70B-Instruct",
            provider="huggingface",
            supervisor_id="supervisor-1",
            reason="Demo spawn for testing"
        )
        
        if result['spawned']:
            print(f"  ✓ Agent spawned: {result['alias']}")
            print(f"  Model: {result['model_name']}")
            print(f"  Provider: {result['provider']}")
        else:
            print(f"  ✗ Spawn failed: {result['reason']}")
        
        print()
        print(c("Spawn History:", Colors.BOLD))
        history = spawner.get_spawn_history()
        for spawn in history:
            print(f"  • {spawn['alias']} - {spawn['spawned_at'][:19]}")
        
        # Check auto-spawn
        print()
        print(c("Auto-spawn Decision:", Colors.CYAN))
        should_spawn, auto_reason = spawner.should_auto_spawn(task_complexity=0.8)
        print(f"  Should auto-spawn: {should_spawn}")
        print(f"  Reason: {auto_reason}")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        for ext in ['-wal', '-shm']:
            if os.path.exists(db_path + ext):
                os.unlink(db_path + ext)


def main():
    """Run all demonstrations."""
    print(c("""
   ___   _  __ ____     
  / _ | | |/_// __/    
 / __ |_>  < / _/      
/_/ |_/_/|_|/___/       
    """, Colors.CYAN))
    print(c("AXE MULTIAGENT IMPROVEMENTS DEMONSTRATION", Colors.BOLD + Colors.YELLOW))
    print(c("Showcasing ALL Phases 1-10: Complete Implementation", Colors.DIM))
    
    try:
        # Original Phase 1-5 demos
        demo_session_rules()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_xp_progression()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_aliasing()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_level_ups()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_persistence()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_resources()
        input(c("\nPress Enter to continue to Phase 6-10 demos...", Colors.YELLOW))
        
        # New Phase 6-10 demos
        demo_sleep_system()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_emergency_mailbox()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_break_system()
        input(c("\nPress Enter to continue to next demo...", Colors.YELLOW))
        
        demo_dynamic_spawning()
        
        print_section("DEMONSTRATION COMPLETE - ALL PHASES 1-10")
        print(c("All features working correctly!", Colors.GREEN + Colors.BOLD))
        print()
        print(c("Summary of Implemented Features:", Colors.BOLD))
        print("  ✅ Phase 1: Session Rules")
        print("  ✅ Phase 2: Agent Aliasing")
        print("  ✅ Phase 3: XP & Levels")
        print("  ✅ Phase 4: SQLite Persistence")
        print("  ✅ Phase 5: Resource Monitoring")
        print("  ✅ Phase 6: Mandatory Sleep System")
        print("  ✅ Phase 7: Degradation Monitoring")
        print("  ✅ Phase 8: Emergency Mailbox")
        print("  ✅ Phase 9: Break System")
        print("  ✅ Phase 10: Dynamic Spawning")
        print()
        print(c("To test with live models:", Colors.BOLD))
        print("  python3 axe.py --collab llama,copilot --workspace ./playground --time 30 --task \"Your task\"")
        print()
        print(c("For more information:", Colors.BOLD))
        print("  • Read IMPROVEMENTS_README.md for full documentation")
        print("  • Run test_axe_improvements.py for automated tests")
        print("  • Check improvements.txt for design discussions")
        
    except KeyboardInterrupt:
        print(c("\n\nDemonstration interrupted by user.", Colors.YELLOW))
    except Exception as e:
        print(c(f"\n\nError during demonstration: {e}", Colors.RED))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
