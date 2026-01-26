#!/usr/bin/env python3
"""
Demo script showing the Level-to-Privilege Mapping system.
Implements Simon's nearly-decomposable hierarchies (1969).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.privilege_mapping import (
    format_privileges_for_prompt,
    validate_command,
    get_privileges_for_level
)

def main():
    print("=" * 80)
    print("AXE LEVEL-TO-PRIVILEGE MAPPING DEMO")
    print("Based on Herbert Simon's Sciences of the Artificial (1969)")
    print("=" * 80)
    print()
    
    # Show different levels
    test_cases = [
        (5, "@worker", "A junior worker learning the ropes"),
        (15, "@llama", "An experienced Senior Worker guiding others"),
        (25, "@gpt", "A Team Leader coordinating sub-teams"),
        (40, "@boss", "A Supervisor overseeing the whole project"),
    ]
    
    for level, alias, description in test_cases:
        print("-" * 80)
        print(f"SCENARIO: {description}")
        print("-" * 80)
        print()
        print(format_privileges_for_prompt(level, alias))
        print()
        print()
    
    # Show command validation examples
    print("=" * 80)
    print("COMMAND VALIDATION EXAMPLES")
    print("=" * 80)
    print()
    
    validation_tests = [
        (5, "[[BROADCAST:FINDING:security issue]]", "Worker broadcasting finding"),
        (5, "[[SUPPRESS:@agent:reason]]", "Worker trying to suppress"),
        (5, "[[AGENT_TASK_COMPLETE:done]]", "Worker declaring task complete"),
        (15, "[[SUPPRESS:@worker:reason]]", "Senior suppressing worker"),
        (15, "[[AGENT_TASK_COMPLETE:done]]", "Senior declaring task complete"),
        (25, "[[ARBITRATE:id:resolution:winner]]", "Team Leader arbitrating"),
        (25, "[[SPAWN:model:role:reason]]", "Team Leader spawning agent"),
        (40, "[[AGENT_TASK_COMPLETE:done]]", "Supervisor declaring task complete"),
        (40, "[[AGENT_EMERGENCY:urgent]]", "Supervisor escalating emergency"),
    ]
    
    for level, command, description in validation_tests:
        is_valid, reason = validate_command(level, command)
        status = "✓ ALLOWED" if is_valid else "✗ DENIED"
        priv = get_privileges_for_level(level)
        title = priv['title']
        
        print(f"{status} | Level {level:2d} ({title:40s}) | {description}")
        if not is_valid:
            print(f"         | Reason: {reason}")
    
    print()
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
