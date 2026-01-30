#!/usr/bin/env python3
"""
Demonstration of the Subsumption Controller.
Shows layer assignment, suppression mechanics, execution ordering,
and prompt formatting in action.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.subsumption_layer import SubsumptionController, SubsumptionLayer
from progression import get_title_for_level
def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")
def demo_layer_assignment():
    """Demonstrate layer assignment from XP levels."""
    print_section("1. Layer Assignment from XP Levels")
    controller = SubsumptionController()
    test_levels = [
        (5, "Worker"),
        (10, "Senior Worker"),
        (15, "Tactical"),
        (20, "Team Leader"),
        (25, "Strategic"),
        (30, "Deputy Supervisor"),
        (40, "Supervisor-Eligible"),
    ]
    for level, title in test_levels:
        layer = controller.get_layer_for_level(level)
        print(f"  Level {level:2d} ({title:20s}) → Layer {layer.value} ({layer.name})")
def demo_suppression():
    """Demonstrate suppression mechanics."""
    print_section("2. Suppression Mechanics")
    controller = SubsumptionController()
    # Successful suppression
    print("Attempting: Strategic (@strategic, L25) suppresses Worker (@worker, L5)")
    success, message = controller.suppress_agent(
        suppressor_id="@strategic",
        suppressor_level=25,
        target_id="@worker",
        target_level=5,
        reason="Strategic planning requires worker to pause"
    )
    print(f"  Result: {message}\n")
    # Failed suppression (same layer)
    print("Attempting: Worker (@worker1, L5) suppresses Worker (@worker2, L7)")
    success, message = controller.suppress_agent(
        suppressor_id="@worker1",
        suppressor_level=5,
        target_id="@worker2",
        target_level=7,
        reason="This should fail"
    )
    print(f"  Result: {message}\n")
    # Failed suppression (lower → higher)
    print("Attempting: Worker (@worker, L5) suppresses Executive (@exec, L40)")
    success, message = controller.suppress_agent(
        suppressor_id="@worker",
        suppressor_level=5,
        target_id="@exec",
        target_level=40,
        reason="This should also fail"
    )
    print(f"  Result: {message}\n")
def demo_execution_order():
    """Demonstrate execution ordering with suppressions."""
    print_section("3. Execution Order (with Suppressions)")
    controller = SubsumptionController()
    # Create team of agents
    agents = [
        {'id': '@alice', 'alias': '@alice', 'level': 5, 'name': 'Alice (Worker)'},
        {'id': '@bob', 'alias': '@bob', 'level': 15, 'name': 'Bob (Tactical)'},
        {'id': '@carol', 'alias': '@carol', 'level': 25, 'name': 'Carol (Strategic)'},
        {'id': '@dave', 'alias': '@dave', 'level': 8, 'name': 'Dave (Worker)'},
        {'id': '@eve', 'alias': '@eve', 'level': 40, 'name': 'Eve (Executive)'},
    ]
    print("Initial team:")
    for agent in agents:
        layer = controller.get_layer_for_level(agent['level'])
        print(f"  {agent['name']:25s} - Level {agent['level']:2d} (Layer {layer.value})")
    # Get execution order without suppressions
    print("\nExecution order (no suppressions):")
    ordered = controller.get_execution_order(agents)
    for i, agent in enumerate(ordered, 1):
        print(f"  {i}. {agent['name']}")
    # Add some suppressions
    print("\nApplying suppressions:")
    controller.suppress_agent('@carol', 25, '@bob', 15, "Strategic override")
    print("  ✓ Carol suppresses Bob")
    controller.suppress_agent('@eve', 40, '@dave', 8, "Executive decision")
    print("  ✓ Eve suppresses Dave")
    # Get execution order with suppressions
    print("\nExecution order (with suppressions):")
    ordered = controller.get_execution_order(agents)
    for i, agent in enumerate(ordered, 1):
        print(f"  {i}. {agent['name']}")
    print("\n  (Bob and Dave are suppressed and excluded)")
def demo_suppression_lifecycle():
    """Demonstrate suppression lifecycle with ticking."""
    print_section("4. Suppression Lifecycle")
    controller = SubsumptionController()
    # Create suppression
    print("Creating suppression: @tactical (L15) suppresses @worker (L5) for 3 turns")
    controller.suppress_agent('@tactical', 15, '@worker', 5, "Testing lifecycle", turns=3)
    supp = controller.get_suppression_info('@worker')
    print(f"  Initial state: {supp.turns_remaining} turns remaining\n")
    # Tick through turns
    for turn in range(1, 5):
        print(f"Turn {turn}:")
        expired = controller.tick_suppressions()
        if controller.is_suppressed('@worker'):
            supp = controller.get_suppression_info('@worker')
            print(f"  @worker still suppressed ({supp.turns_remaining} turns left)")
        else:
            print(f"  @worker suppression EXPIRED")
            print(f"  Expired this turn: {expired}")
            break
def demo_prompt_formatting():
    """Demonstrate prompt formatting for different layers."""
    print_section("5. Prompt Formatting")
    controller = SubsumptionController()
    # Worker prompt
    print("Worker Agent Prompt (@worker, Level 5):")
    print("-" * 70)
    prompt = controller.format_for_prompt('@worker', 5)
    print(prompt)
    # Executive prompt
    print("\n\nExecutive Agent Prompt (@exec, Level 42):")
    print("-" * 70)
    prompt = controller.format_for_prompt('@exec', 42)
    print(prompt)
    # Suppressed agent prompt
    print("\n\nSuppressed Worker Prompt:")
    print("-" * 70)
    controller.suppress_agent('@strategic', 25, '@worker2', 5, "Example suppression")
    prompt = controller.format_for_prompt('@worker2', 5)
    print(prompt)
def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" SUBSUMPTION CONTROLLER DEMONSTRATION")
    print(" (Rodney Brooks' Architecture - 1986)")
    print("=" * 70)
    demo_layer_assignment()
    demo_suppression()
    demo_execution_order()
    demo_suppression_lifecycle()
    demo_prompt_formatting()
    print("\n" + "=" * 70)
    print(" End of Demonstration")
    print("=" * 70 + "\n")
if __name__ == '__main__':
    main()