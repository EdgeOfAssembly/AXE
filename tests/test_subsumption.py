#!/usr/bin/env python3
"""
Test suite for Subsumption Controller (Brooks 1986).

Tests layer assignment, suppression permissions, suppression lifecycle,
execution ordering, and prompt formatting.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.subsumption_layer import (
    SubsumptionController,
    SubsumptionLayer,
    LAYER_METADATA
)
from core.constants import (
    SUPPRESSION_DEFAULT_TURNS,
    SUPPRESSION_MAX_TURNS
)
from progression.levels import (
    LEVEL_SENIOR_WORKER,
    LEVEL_TEAM_LEADER,
    LEVEL_DEPUTY_SUPERVISOR,
    LEVEL_SUPERVISOR_ELIGIBLE
)


def test_layer_assignment():
    """Test that XP levels map correctly to subsumption layers."""
    print("=" * 70)
    print("TEST: Layer Assignment from XP Levels")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Test Worker layer (levels 1-9)
    assert controller.get_layer_for_level(1) == SubsumptionLayer.WORKER, "Level 1 should be WORKER"
    assert controller.get_layer_for_level(5) == SubsumptionLayer.WORKER, "Level 5 should be WORKER"
    assert controller.get_layer_for_level(9) == SubsumptionLayer.WORKER, "Level 9 should be WORKER"
    print(f"  ✓ Levels 1-9 correctly map to WORKER (Layer {SubsumptionLayer.WORKER.value})")
    
    # Test Tactical layer (levels 10-19)
    assert controller.get_layer_for_level(10) == SubsumptionLayer.TACTICAL, "Level 10 should be TACTICAL"
    assert controller.get_layer_for_level(15) == SubsumptionLayer.TACTICAL, "Level 15 should be TACTICAL"
    assert controller.get_layer_for_level(19) == SubsumptionLayer.TACTICAL, "Level 19 should be TACTICAL"
    print(f"  ✓ Levels 10-19 correctly map to TACTICAL (Layer {SubsumptionLayer.TACTICAL.value})")
    
    # Test Strategic layer (levels 20-39)
    assert controller.get_layer_for_level(20) == SubsumptionLayer.STRATEGIC, "Level 20 should be STRATEGIC"
    assert controller.get_layer_for_level(25) == SubsumptionLayer.STRATEGIC, "Level 25 should be STRATEGIC"
    assert controller.get_layer_for_level(30) == SubsumptionLayer.STRATEGIC, "Level 30 should be STRATEGIC"
    assert controller.get_layer_for_level(39) == SubsumptionLayer.STRATEGIC, "Level 39 should be STRATEGIC"
    print(f"  ✓ Levels 20-39 correctly map to STRATEGIC (Layer {SubsumptionLayer.STRATEGIC.value})")
    
    # Test Executive layer (levels 40+)
    assert controller.get_layer_for_level(40) == SubsumptionLayer.EXECUTIVE, "Level 40 should be EXECUTIVE"
    assert controller.get_layer_for_level(50) == SubsumptionLayer.EXECUTIVE, "Level 50 should be EXECUTIVE"
    assert controller.get_layer_for_level(100) == SubsumptionLayer.EXECUTIVE, "Level 100 should be EXECUTIVE"
    print(f"  ✓ Levels 40+ correctly map to EXECUTIVE (Layer {SubsumptionLayer.EXECUTIVE.value})")
    
    print("\n✅ Layer assignment test passed!")
    print()


def test_suppression_permission_checks():
    """Test that suppression permissions are enforced correctly."""
    print("=" * 70)
    print("TEST: Suppression Permission Checks")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Executive (L4) can suppress Strategic (L3)
    assert controller.can_suppress(40, 30), "Executive should suppress Strategic"
    assert controller.can_suppress(40, 20), "Executive should suppress Strategic"
    print("  ✓ Executive (L4) can suppress Strategic (L3)")
    
    # Executive (L4) can suppress Tactical (L2)
    assert controller.can_suppress(40, 15), "Executive should suppress Tactical"
    assert controller.can_suppress(40, 10), "Executive should suppress Tactical"
    print("  ✓ Executive (L4) can suppress Tactical (L2)")
    
    # Executive (L4) can suppress Worker (L1)
    assert controller.can_suppress(40, 5), "Executive should suppress Worker"
    assert controller.can_suppress(40, 1), "Executive should suppress Worker"
    print("  ✓ Executive (L4) can suppress Worker (L1)")
    
    # Strategic (L3) can suppress Tactical (L2)
    assert controller.can_suppress(30, 15), "Strategic should suppress Tactical"
    assert controller.can_suppress(25, 10), "Strategic should suppress Tactical"
    print("  ✓ Strategic (L3) can suppress Tactical (L2)")
    
    # Strategic (L3) can suppress Worker (L1)
    assert controller.can_suppress(30, 5), "Strategic should suppress Worker"
    assert controller.can_suppress(25, 1), "Strategic should suppress Worker"
    print("  ✓ Strategic (L3) can suppress Worker (L1)")
    
    # Tactical (L2) can suppress Worker (L1)
    assert controller.can_suppress(15, 5), "Tactical should suppress Worker"
    assert controller.can_suppress(10, 1), "Tactical should suppress Worker"
    print("  ✓ Tactical (L2) can suppress Worker (L1)")
    
    # Same layer cannot suppress each other
    assert not controller.can_suppress(40, 40), "Executive cannot suppress Executive"
    assert not controller.can_suppress(30, 25), "Strategic cannot suppress Strategic"
    assert not controller.can_suppress(15, 10), "Tactical cannot suppress Tactical"
    assert not controller.can_suppress(5, 1), "Worker cannot suppress Worker"
    print("  ✓ Same layer agents cannot suppress each other")
    
    # Lower layers cannot suppress higher
    assert not controller.can_suppress(1, 40), "Worker cannot suppress Executive"
    assert not controller.can_suppress(10, 30), "Tactical cannot suppress Strategic"
    assert not controller.can_suppress(25, 40), "Strategic cannot suppress Executive"
    print("  ✓ Lower layers cannot suppress higher layers")
    
    print("\n✅ Suppression permission checks passed!")
    print()


def test_suppression_lifecycle():
    """Test suppression creation, ticking, and expiration."""
    print("=" * 70)
    print("TEST: Suppression Lifecycle (Create → Tick → Expire)")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Create suppression
    success, message = controller.suppress_agent(
        suppressor_id="@senior",
        suppressor_level=15,
        target_id="@worker",
        target_level=5,
        reason="Task needs tactical oversight",
        turns=3
    )
    assert success, "Suppression should succeed"
    assert "@senior" in message, "Message should mention suppressor"
    assert "@worker" in message, "Message should mention target"
    print(f"  ✓ Suppression created: {message}")
    
    # Check suppression is active
    assert controller.is_suppressed("@worker"), "Worker should be suppressed"
    assert not controller.is_suppressed("@senior"), "Senior should not be suppressed"
    print("  ✓ Suppression is active")
    
    # Get suppression info
    supp_info = controller.get_suppression_info("@worker")
    assert supp_info is not None, "Suppression info should exist"
    assert supp_info.turns_remaining == 3, "Should have 3 turns remaining"
    assert supp_info.reason == "Task needs tactical oversight", "Reason should match"
    print(f"  ✓ Suppression info: {supp_info.turns_remaining} turns remaining")
    
    # Tick 1 - should still be active
    expired = controller.tick_suppressions()
    assert len(expired) == 0, "No suppressions should expire on first tick"
    assert controller.is_suppressed("@worker"), "Worker should still be suppressed"
    supp_info = controller.get_suppression_info("@worker")
    assert supp_info.turns_remaining == 2, "Should have 2 turns remaining after tick"
    print("  ✓ Tick 1: 2 turns remaining")
    
    # Tick 2 - should still be active
    expired = controller.tick_suppressions()
    assert len(expired) == 0, "No suppressions should expire on second tick"
    assert controller.is_suppressed("@worker"), "Worker should still be suppressed"
    supp_info = controller.get_suppression_info("@worker")
    assert supp_info.turns_remaining == 1, "Should have 1 turn remaining after tick"
    print("  ✓ Tick 2: 1 turn remaining")
    
    # Tick 3 - should expire
    expired = controller.tick_suppressions()
    assert len(expired) == 1, "One suppression should expire"
    assert "@worker" in expired, "Worker suppression should expire"
    assert not controller.is_suppressed("@worker"), "Worker should no longer be suppressed"
    assert controller.get_suppression_info("@worker") is None, "Suppression info should be gone"
    print("  ✓ Tick 3: Suppression expired")
    
    print("\n✅ Suppression lifecycle test passed!")
    print()


def test_manual_release():
    """Test manual release of suppressions with permission checks."""
    print("=" * 70)
    print("TEST: Manual Release with Permission Checks")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Create suppression: Strategic suppresses Worker
    controller.suppress_agent(
        suppressor_id="@strategic",
        suppressor_level=25,
        target_id="@worker",
        target_level=5,
        reason="Strategic planning in progress"
    )
    assert controller.is_suppressed("@worker"), "Worker should be suppressed"
    print("  ✓ Initial suppression created")
    
    # Test 1: Original suppressor can release
    success, message = controller.release_suppression(
        releaser_id="@strategic",
        releaser_level=25,
        target_id="@worker"
    )
    assert success, "Original suppressor should be able to release"
    assert not controller.is_suppressed("@worker"), "Worker should no longer be suppressed"
    print(f"  ✓ Original suppressor can release: {message}")
    
    # Create new suppression for next tests
    controller.suppress_agent(
        suppressor_id="@tactical",
        suppressor_level=15,
        target_id="@worker",
        target_level=5,
        reason="Tactical override"
    )
    assert controller.is_suppressed("@worker"), "Worker should be suppressed again"
    print("  ✓ New suppression created for testing")
    
    # Test 2: Higher layer can release
    success, message = controller.release_suppression(
        releaser_id="@executive",
        releaser_level=40,
        target_id="@worker"
    )
    assert success, "Executive (higher layer) should be able to release"
    assert not controller.is_suppressed("@worker"), "Worker should no longer be suppressed"
    print(f"  ✓ Higher layer can release: {message}")
    
    # Create another suppression
    controller.suppress_agent(
        suppressor_id="@strategic",
        suppressor_level=25,
        target_id="@worker",
        target_level=5,
        reason="Testing permission denial"
    )
    print("  ✓ New suppression for negative test")
    
    # Test 3: Lower/same layer cannot release (except original)
    success, message = controller.release_suppression(
        releaser_id="@tactical",
        releaser_level=15,
        target_id="@worker"
    )
    assert not success, "Lower layer should not be able to release"
    assert controller.is_suppressed("@worker"), "Worker should still be suppressed"
    assert "cannot release" in message.lower(), "Error message should explain permission denial"
    print(f"  ✓ Lower layer cannot release: {message}")
    
    # Test 4: Release non-existent suppression
    success, message = controller.release_suppression(
        releaser_id="@strategic",
        releaser_level=25,
        target_id="@nonexistent"
    )
    assert not success, "Should fail to release non-existent suppression"
    assert "not currently suppressed" in message.lower(), "Should indicate target not suppressed"
    print(f"  ✓ Release non-existent suppression fails gracefully: {message}")
    
    print("\n✅ Manual release test passed!")
    print()


def test_max_turns_enforcement():
    """Test that SUPPRESSION_MAX_TURNS is enforced."""
    print("=" * 70)
    print("TEST: Maximum Turns Enforcement")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Try to create suppression with excessive turns
    success, message = controller.suppress_agent(
        suppressor_id="@executive",
        suppressor_level=40,
        target_id="@worker",
        target_level=5,
        reason="Testing max turns",
        turns=999  # Way over the limit
    )
    assert success, "Suppression should succeed (but with clamped turns)"
    print(f"  ✓ Suppression created: {message}")
    
    # Check that turns were clamped to max
    supp_info = controller.get_suppression_info("@worker")
    assert supp_info is not None, "Suppression should exist"
    assert supp_info.turns_remaining == SUPPRESSION_MAX_TURNS, \
        f"Turns should be clamped to {SUPPRESSION_MAX_TURNS}"
    print(f"  ✓ Turns clamped to maximum: {SUPPRESSION_MAX_TURNS}")
    
    print("\n✅ Maximum turns enforcement test passed!")
    print()


def test_execution_order():
    """Test that agents are sorted by layer and suppressed agents are excluded."""
    print("=" * 70)
    print("TEST: Execution Order Sorting")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Create test agents at different levels
    agents = [
        {'id': '@worker1', 'alias': '@worker1', 'level': 5},
        {'id': '@worker2', 'alias': '@worker2', 'level': 8},
        {'id': '@tactical1', 'alias': '@tactical1', 'level': 12},
        {'id': '@tactical2', 'alias': '@tactical2', 'level': 18},
        {'id': '@strategic', 'alias': '@strategic', 'level': 25},
        {'id': '@executive', 'alias': '@executive', 'level': 42},
    ]
    
    # Get execution order without suppressions
    ordered = controller.get_execution_order(agents)
    assert len(ordered) == 6, "All agents should be included"
    
    # Check order: Executive → Strategic → Tactical (high to low) → Worker (high to low)
    assert ordered[0]['id'] == '@executive', "Executive should be first"
    assert ordered[1]['id'] == '@strategic', "Strategic should be second"
    assert ordered[2]['id'] == '@tactical2', "Higher tactical should be third"
    assert ordered[3]['id'] == '@tactical1', "Lower tactical should be fourth"
    assert ordered[4]['id'] == '@worker2', "Higher worker should be fifth"
    assert ordered[5]['id'] == '@worker1', "Lower worker should be sixth"
    print("  ✓ Agents sorted correctly: Executive > Strategic > Tactical > Worker")
    print(f"    Order: {' → '.join(a['id'] for a in ordered)}")
    
    # Suppress some agents
    controller.suppress_agent('@strategic', 25, '@tactical1', 12, "Testing exclusion")
    controller.suppress_agent('@executive', 42, '@worker2', 8, "Testing exclusion")
    
    # Get execution order with suppressions
    ordered = controller.get_execution_order(agents)
    assert len(ordered) == 4, "Only 4 agents should be active (2 suppressed)"
    
    # Check suppressed agents are excluded
    active_ids = [a['id'] for a in ordered]
    assert '@tactical1' not in active_ids, "Suppressed tactical1 should be excluded"
    assert '@worker2' not in active_ids, "Suppressed worker2 should be excluded"
    assert '@executive' in active_ids, "Executive should be active"
    assert '@strategic' in active_ids, "Strategic should be active"
    assert '@tactical2' in active_ids, "Tactical2 should be active"
    assert '@worker1' in active_ids, "Worker1 should be active"
    print("  ✓ Suppressed agents correctly excluded from execution order")
    print(f"    Active: {' → '.join(a['id'] for a in ordered)}")
    
    print("\n✅ Execution order test passed!")
    print()


def test_prompt_formatting():
    """Test prompt formatting for different layers."""
    print("=" * 70)
    print("TEST: Prompt Formatting")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Test Worker prompt
    prompt = controller.format_for_prompt('@worker', 5)
    assert "Worker (Layer 1)" in prompt, "Should identify layer"
    assert "Execute assigned tasks" in prompt, "Should list responsibilities"
    assert "CAN suppress" not in prompt or "Tactical" in prompt, "Worker can't suppress much"
    assert "CAN BE suppressed by" in prompt, "Should list higher layers"
    print("  ✓ Worker prompt formatted correctly")
    print(f"    Preview: {prompt[:100]}...")
    
    # Test Tactical prompt
    prompt = controller.format_for_prompt('@tactical', 15)
    assert "Tactical (Layer 2)" in prompt, "Should identify layer"
    assert "Coordinate multiple tasks" in prompt, "Should list responsibilities"
    assert "Worker" in prompt, "Can suppress Worker layer"
    print("  ✓ Tactical prompt formatted correctly")
    
    # Test Strategic prompt
    prompt = controller.format_for_prompt('@strategic', 25)
    assert "Strategic (Layer 3)" in prompt, "Should identify layer"
    assert "Plan long-term objectives" in prompt, "Should list responsibilities"
    assert "Worker" in prompt, "Can suppress Worker"
    assert "Tactical" in prompt, "Can suppress Tactical"
    print("  ✓ Strategic prompt formatted correctly")
    
    # Test Executive prompt
    prompt = controller.format_for_prompt('@executive', 42)
    assert "Executive (Layer 4)" in prompt, "Should identify layer"
    assert "Set system-wide policies" in prompt, "Should list responsibilities"
    assert "Worker" in prompt, "Can suppress Worker"
    assert "Tactical" in prompt, "Can suppress Tactical"
    assert "Strategic" in prompt, "Can suppress Strategic"
    print("  ✓ Executive prompt formatted correctly")
    
    # Test prompt with active suppression
    controller.suppress_agent('@strategic', 25, '@worker', 5, "For testing")
    prompt = controller.format_for_prompt('@worker', 5)
    assert "Currently Suppressed" in prompt, "Should show suppression status"
    assert "Yes" in prompt, "Should indicate suppressed"
    assert "@strategic" in prompt, "Should show suppressor"
    assert "For testing" in prompt, "Should show reason"
    print("  ✓ Suppression status shown in prompt")
    
    print("\n✅ Prompt formatting test passed!")
    print()


def test_failed_suppression():
    """Test that invalid suppressions fail gracefully."""
    print("=" * 70)
    print("TEST: Failed Suppression (Permission Denied)")
    print("=" * 70)
    
    controller = SubsumptionController()
    
    # Try to suppress higher layer from lower layer
    success, message = controller.suppress_agent(
        suppressor_id="@worker",
        suppressor_level=5,
        target_id="@executive",
        target_level=42,
        reason="This should fail"
    )
    assert not success, "Lower layer should not suppress higher layer"
    assert "cannot suppress" in message.lower(), "Error message should explain"
    assert not controller.is_suppressed("@executive"), "Executive should not be suppressed"
    print(f"  ✓ Invalid suppression failed: {message}")
    
    # Try to suppress same layer
    success, message = controller.suppress_agent(
        suppressor_id="@worker1",
        suppressor_level=5,
        target_id="@worker2",
        target_level=7,
        reason="This should also fail"
    )
    assert not success, "Same layer should not suppress each other"
    assert not controller.is_suppressed("@worker2"), "Worker2 should not be suppressed"
    print(f"  ✓ Same-layer suppression failed: {message}")
    
    print("\n✅ Failed suppression test passed!")
    print()


def test_layer_metadata():
    """Test that layer metadata is complete and accessible."""
    print("=" * 70)
    print("TEST: Layer Metadata Completeness")
    print("=" * 70)
    
    # Check all layers have metadata
    for layer in SubsumptionLayer:
        assert layer in LAYER_METADATA, f"Layer {layer} should have metadata"
        metadata = LAYER_METADATA[layer]
        assert 'name' in metadata, f"Layer {layer} should have name"
        assert 'description' in metadata, f"Layer {layer} should have description"
        assert 'responsibilities' in metadata, f"Layer {layer} should have responsibilities"
        assert isinstance(metadata['responsibilities'], list), \
            f"Layer {layer} responsibilities should be a list"
        print(f"  ✓ {metadata['name']} (Layer {layer.value}): {metadata['description']}")
    
    print("\n✅ Layer metadata test passed!")
    print()


def run_all_tests():
    """Run all test functions."""
    print("\n")
    print("=" * 70)
    print(" SUBSUMPTION CONTROLLER TEST SUITE (Brooks 1986)")
    print("=" * 70)
    print()
    
    tests = [
        test_layer_assignment,
        test_suppression_permission_checks,
        test_suppression_lifecycle,
        test_manual_release,
        test_max_turns_enforcement,
        test_execution_order,
        test_prompt_formatting,
        test_failed_suppression,
        test_layer_metadata,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n")
    print("=" * 70)
    print(f" TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!\n")
        sys.exit(0)


if __name__ == '__main__':
    run_all_tests()
