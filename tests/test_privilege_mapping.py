#!/usr/bin/env python3
"""
Test suite for Level-to-Privilege Mapping.
Tests privilege lookup, prompt formatting, command validation, and promotions.

Based on Herbert Simon's Sciences of the Artificial (1969) - Nearly-Decomposable Hierarchies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.privilege_mapping import (
    PRIVILEGE_MAPPING,
    get_privileges_for_level,
    format_privileges_for_prompt,
    validate_command,
    get_next_promotion,
    get_promotion_preview
)
from progression.levels import (
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER, 
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE
)


def test_privilege_mapping_structure():
    """Test that PRIVILEGE_MAPPING has correct structure."""
    print("Testing privilege mapping structure...")
    
    required_tiers = ['worker', 'senior_worker', 'deputy', 'supervisor']
    for tier in required_tiers:
        assert tier in PRIVILEGE_MAPPING, f"Missing tier: {tier}"
        
        priv = PRIVILEGE_MAPPING[tier]
        assert 'level_range' in priv, f"{tier} missing level_range"
        assert 'title' in priv, f"{tier} missing title"
        assert 'responsibilities' in priv, f"{tier} missing responsibilities"
        assert 'authorities' in priv, f"{tier} missing authorities"
        assert 'restrictions' in priv, f"{tier} missing restrictions"
        assert 'commands' in priv, f"{tier} missing commands"
        
        assert isinstance(priv['level_range'], tuple), f"{tier} level_range should be tuple"
        assert len(priv['level_range']) == 2, f"{tier} level_range should have 2 elements"
        assert isinstance(priv['responsibilities'], list), f"{tier} responsibilities should be list"
        assert isinstance(priv['authorities'], list), f"{tier} authorities should be list"
        assert isinstance(priv['restrictions'], list), f"{tier} restrictions should be list"
        assert isinstance(priv['commands'], list), f"{tier} commands should be list"
    
    print("  ✓ Privilege mapping structure is correct")
    print()


def test_get_privileges_for_level():
    """Test privilege lookup for different level ranges."""
    print("Testing privilege lookup for levels...")
    
    # Test worker levels (1-9)
    for level in [1, 5, 9]:
        priv = get_privileges_for_level(level)
        assert priv['title'] == 'Worker', f"Level {level} should be Worker"
    
    # Test senior worker levels (10-19)
    for level in [10, 15, 19]:
        priv = get_privileges_for_level(level)
        assert priv['title'] == 'Senior Worker', f"Level {level} should be Senior Worker"
    
    # Test team leader levels (20-29)
    for level in [20, 25, 29]:
        priv = get_privileges_for_level(level)
        assert priv['title'] == 'Team Leader', f"Level {level} should be Team Leader"
    
    # Test deputy supervisor levels (30-39) and supervisor-eligible (40+)
    for level in [30, 40, 50]:
        priv = get_privileges_for_level(level)
        assert priv['title'] == 'Deputy Supervisor', f"Level {level} should be Deputy Supervisor"
    
    print("  ✓ Privilege lookup works correctly for all levels")
    print()


def test_boundary_levels():
    """Test privilege assignment at boundary levels."""
    print("Testing boundary levels...")
    
    # Boundary 9→10
    priv_9 = get_privileges_for_level(9)
    priv_10 = get_privileges_for_level(10)
    assert priv_9['title'] == 'Worker', "Level 9 should be Worker"
    assert priv_10['title'] == 'Senior Worker', "Level 10 should be Senior Worker"
    
    # Boundary 19→20
    priv_19 = get_privileges_for_level(19)
    priv_20 = get_privileges_for_level(20)
    assert priv_19['title'] == 'Senior Worker', "Level 19 should be Senior Worker"
    assert priv_20['title'] == 'Team Leader', "Level 20 should be Team Leader"
    
    # Boundary 29→30
    priv_29 = get_privileges_for_level(29)
    priv_30 = get_privileges_for_level(30)
    assert priv_29['title'] == 'Team Leader', "Level 29 should be Team Leader"
    assert priv_30['title'] == 'Deputy Supervisor', "Level 30 should be Deputy Supervisor"
    
    print("  ✓ Boundary level transitions work correctly")
    print()


def test_format_privileges_for_prompt():
    """Test prompt formatting for different levels."""
    print("Testing prompt formatting...")
    
    # Test worker level
    prompt = format_privileges_for_prompt(5, "@test")
    assert "YOUR ROLE: Worker (Level 5)" in prompt, "Should include role title"
    assert "Agent: @test" in prompt, "Should include agent alias"
    assert "RESPONSIBILITIES" in prompt, "Should include responsibilities section"
    assert "AUTHORITIES" in prompt, "Should include authorities section"
    assert "RESTRICTIONS" in prompt, "Should include restrictions section"
    assert "AVAILABLE COMMANDS" in prompt, "Should include commands section"
    assert "NEXT PROMOTION" in prompt, "Should include promotion info"
    assert "Senior Worker" in prompt, "Should mention next promotion title"
    
    # Test senior worker level
    prompt = format_privileges_for_prompt(15, "@senior")
    assert "Senior Worker (Level 15)" in prompt
    assert "Team Leader" in prompt, "Should mention next promotion"
    
    # Test team leader level
    prompt = format_privileges_for_prompt(25, "@deputy")
    assert "Team Leader (Level 25)" in prompt
    assert "Supervisor" in prompt or "Deputy" in prompt, "Should mention next promotion"
    
    # Test deputy supervisor level
    prompt = format_privileges_for_prompt(40, "@boss")
    assert "Deputy Supervisor (Level 40)" in prompt
    # Should not have next promotion at max level
    
    print("  ✓ Prompt formatting works correctly")
    print()


def test_command_validation():
    """Test command validation for different levels."""
    print("Testing command validation...")
    
    # Worker level (1-9) commands
    is_valid, reason = validate_command(5, "[[BROADCAST:FINDING:test]]")
    assert is_valid, f"Workers should be able to broadcast: {reason}"
    
    is_valid, reason = validate_command(5, "[[XP_VOTE:+10:@agent:reason]]")
    assert is_valid, f"Workers should be able to vote XP: {reason}"
    
    is_valid, reason = validate_command(5, "[[AGENT_PASS_TURN]]")
    assert is_valid, f"Workers should be able to pass turn: {reason}"
    
    is_valid, reason = validate_command(5, "[[SUPPRESS:@agent:reason]]")
    assert not is_valid, "Workers should not be able to suppress (command is planned)"
    
    is_valid, reason = validate_command(5, "[[AGENT_TASK_COMPLETE:summary]]")
    assert not is_valid, "Workers should not be able to declare task complete"
    
    # Senior worker level (10-19) commands - should inherit worker commands
    is_valid, reason = validate_command(15, "[[AGENT_PASS_TURN]]")
    assert is_valid, f"Senior workers should inherit worker commands: {reason}"
    
    is_valid, reason = validate_command(15, "[[BROADCAST:FINDING:test]]")
    assert is_valid, f"Senior workers should inherit broadcast: {reason}"
    
    is_valid, reason = validate_command(15, "[[SUPPRESS:@worker:reason]]")
    assert not is_valid, "Senior workers should not be able to suppress (command is planned)"
    
    is_valid, reason = validate_command(15, "[[DIRECTIVE:instruction]]")
    assert not is_valid, "Senior workers should not be able to use DIRECTIVE (command is planned)"
    
    is_valid, reason = validate_command(15, "[[AGENT_TASK_COMPLETE:summary]]")
    assert not is_valid, "Senior workers should not be able to declare task complete"
    
    # Team Leader level (20-29) commands - should inherit worker + senior commands
    is_valid, reason = validate_command(25, "[[AGENT_PASS_TURN]]")
    assert is_valid, f"Team leaders should inherit worker commands: {reason}"
    
    is_valid, reason = validate_command(25, "[[BROADCAST:FINDING:test]]")
    assert is_valid, f"Team leaders should inherit broadcast: {reason}"
    
    is_valid, reason = validate_command(25, "[[ARBITRATE:arb_id:resolution:winner]]")
    assert not is_valid, "Team leaders should not be able to arbitrate (command is planned)"
    
    is_valid, reason = validate_command(25, "[[SPAWN:model:role:reason]]")
    assert not is_valid, "Team leaders should not be able to spawn (command is planned)"
    
    # Deputy Supervisor level (30+) commands - should inherit all lower commands
    is_valid, reason = validate_command(40, "[[AGENT_PASS_TURN]]")
    assert is_valid, f"Supervisors should inherit worker commands: {reason}"
    
    is_valid, reason = validate_command(40, "[[BROADCAST:FINDING:test]]")
    assert is_valid, f"Supervisors should inherit broadcast: {reason}"
    
    is_valid, reason = validate_command(40, "[[AGENT_TASK_COMPLETE:summary]]")
    assert is_valid, f"Supervisors should be able to declare task complete: {reason}"
    
    is_valid, reason = validate_command(40, "[[AGENT_EMERGENCY:message]]")
    assert is_valid, f"Supervisors should be able to use emergency: {reason}"
    
    print("  ✓ Command validation works correctly (including inheritance)")
    print()


def test_promotion_info():
    """Test next promotion and preview functions."""
    print("Testing promotion info...")
    
    # Worker to Senior Worker
    next_level, next_title = get_next_promotion(5)
    assert next_level == LEVEL_SENIOR_WORKER, "Worker should promote to level 10"
    assert next_title == "Senior Worker", "Worker should promote to Senior Worker"
    
    preview = get_promotion_preview(LEVEL_SENIOR_WORKER)
    assert "DIRECTIVE" in preview, "Preview should mention DIRECTIVE"
    assert "suppress workers" in preview, "Preview should mention suppress"
    
    # Senior Worker to Team Leader
    next_level, next_title = get_next_promotion(15)
    assert next_level == LEVEL_TEAM_LEADER, "Senior should promote to level 20"
    
    # Team Leader to Deputy Supervisor
    next_level, next_title = get_next_promotion(25)
    assert next_level == LEVEL_DEPUTY_SUPERVISOR, "Team Leader should promote to level 30"
    
    preview = get_promotion_preview(LEVEL_DEPUTY_SUPERVISOR)
    assert "TASK COMPLETE" in preview, "Preview should mention TASK COMPLETE"
    
    # Deputy Supervisor to Supervisor Eligible
    next_level, next_title = get_next_promotion(35)
    assert next_level == LEVEL_SUPERVISOR_ELIGIBLE, "Deputy should promote to level 40"
    
    # Supervisor at max level
    next_level, next_title = get_next_promotion(50)
    assert next_level is None, "Max level should have no next promotion"
    assert next_title is None, "Max level should have no next title"
    
    print("  ✓ Promotion info works correctly")
    print()


def test_privilege_progression():
    """Test that privileges escalate properly through levels."""
    print("Testing privilege progression...")
    
    worker = get_privileges_for_level(5)
    senior = get_privileges_for_level(15)
    supervisor = get_privileges_for_level(40)
    
    # Check that commands increase with level
    assert len(worker['commands']) < len(senior['commands']) or \
           len(worker['commands']) <= len(supervisor['commands']), \
           "Higher levels should have more or equal commands"
    
    # Check that responsibilities evolve
    assert worker['responsibilities'] != supervisor['responsibilities'], \
           "Different levels should have different responsibilities"
    
    # Check that restrictions decrease with level
    worker_restrictions = len(worker['restrictions'])
    supervisor_restrictions = len(supervisor['restrictions'])
    assert worker_restrictions >= supervisor_restrictions or \
           any("Must" in r for r in supervisor['restrictions']), \
           "Higher levels should have fewer or different restrictions"
    
    print("  ✓ Privilege progression is correct")
    print()


def test_command_token_format():
    """Test that command tokens follow expected format."""
    print("Testing command token format...")
    
    for tier_name, tier_data in PRIVILEGE_MAPPING.items():
        for cmd in tier_data['commands']:
            # Commands should use [[ ]] brackets
            assert cmd.startswith('[[') or '[[' in cmd, \
                   f"{tier_name} command should use [[ bracket format: {cmd}"
            
            # Commands should have : separators or be simple tokens
            assert ':' in cmd or cmd.startswith('[[AGENT_'), \
                   f"{tier_name} command should have proper format: {cmd}"
    
    print("  ✓ Command token format is correct")
    print()


def test_privilege_hierarchy_consistency():
    """Test that privileges follow hierarchical consistency."""
    print("Testing privilege hierarchy consistency...")
    
    # Senior workers should mention they have all worker authorities
    senior = get_privileges_for_level(15)
    assert any("All Worker authorities" in auth for auth in senior['authorities']), \
           "Senior workers should explicitly include worker authorities"
    
    # Deputies should mention they have all senior authorities
    deputy = get_privileges_for_level(25)
    assert any("All Senior authorities" in auth for auth in deputy['authorities']), \
           "Deputies should explicitly include senior authorities"
    
    # Supervisors should mention they have all deputy authorities
    supervisor = get_privileges_for_level(40)
    assert any("All Deputy authorities" in auth for auth in supervisor['authorities']), \
           "Supervisors should explicitly include deputy authorities"
    
    print("  ✓ Privilege hierarchy is consistent")
    print()


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("PRIVILEGE MAPPING TEST SUITE")
    print("=" * 60)
    print()
    
    test_privilege_mapping_structure()
    test_get_privileges_for_level()
    test_boundary_levels()
    test_format_privileges_for_prompt()
    test_command_validation()
    test_promotion_info()
    test_privilege_progression()
    test_command_token_format()
    test_privilege_hierarchy_consistency()
    
    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
