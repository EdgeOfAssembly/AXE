#!/usr/bin/env python3
"""
Test script for task completion detection fixes.
Tests the is_genuine_task_completion function to prevent false positives.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import is_genuine_task_completion


def test_file_content_not_trigger():
    """TASK COMPLETE in file content should not end session."""
    print("Testing: File content with TASK COMPLETE...")
    response = '''Let me read the mission file:
    
<result>
<function_result>
<result>
⚠️ WARNING: Saying "TASK COMPLETE" without actual code changes
will be considered task failure.
</result>
</function_result>
</result>

Now let me analyze this...'''
    
    assert not is_genuine_task_completion(response), "File content should not trigger"
    print("✓ PASSED: File content does not trigger")


def test_quoted_not_trigger():
    """TASK COMPLETE in quotes should not end session."""
    print("\nTesting: Quoted TASK COMPLETE...")
    response = '''The instructions say "TASK COMPLETE" should only be said when done.'''
    assert not is_genuine_task_completion(response), "Quoted text should not trigger"
    print("✓ PASSED: Quoted text does not trigger")


def test_single_quoted_not_trigger():
    """TASK COMPLETE in single quotes should not end session."""
    print("\nTesting: Single-quoted TASK COMPLETE...")
    response = """The file says 'TASK COMPLETE' at the end."""
    assert not is_genuine_task_completion(response), "Single-quoted text should not trigger"
    print("✓ PASSED: Single-quoted text does not trigger")


def test_codeblock_not_trigger():
    """TASK COMPLETE in code blocks should not end session."""
    print("\nTesting: Code block with TASK COMPLETE...")
    response = '''Here's the code:
```python
if done:
    print("TASK COMPLETE")
```
'''
    assert not is_genuine_task_completion(response), "Code block should not trigger"
    print("✓ PASSED: Code block does not trigger")


def test_blockquote_not_trigger():
    """TASK COMPLETE in blockquotes should not end session."""
    print("\nTesting: Blockquote with TASK COMPLETE...")
    response = '''>The instruction says TASK COMPLETE when done.

I will follow this instruction.'''
    assert not is_genuine_task_completion(response), "Blockquote should not trigger"
    print("✓ PASSED: Blockquote does not trigger")


def test_read_block_not_trigger():
    """TASK COMPLETE in [READ ...] blocks should not end session."""
    print("\nTesting: READ block with TASK COMPLETE...")
    response = '''[READ MISSION.md]
⚠️ WARNING: Saying "TASK COMPLETE" without actual code changes
will be considered task failure.

This is important to note.'''
    assert not is_genuine_task_completion(response), "READ block should not trigger"
    print("✓ PASSED: READ block does not trigger")


def test_lowercase_read_block_not_trigger():
    """TASK COMPLETE in [read ...] blocks (lowercase) should not end session."""
    print("\nTesting: lowercase read block with TASK COMPLETE...")
    response = '''[read mission.md]
⚠️ WARNING: Saying "TASK COMPLETE" without actual code changes
will be considered task failure.

This is important to note.'''
    assert not is_genuine_task_completion(response), "Lowercase read block should not trigger"
    print("✓ PASSED: Lowercase read block does not trigger")


def test_genuine_with_colon_triggers():
    """Genuine TASK COMPLETE: summary should trigger."""
    print("\nTesting: Genuine TASK COMPLETE with colon...")
    response = "TASK COMPLETE: We finished all three phases."
    assert is_genuine_task_completion(response), "Genuine with colon should trigger"
    print("✓ PASSED: Genuine declaration with colon triggers")


def test_genuine_with_checkmark_triggers():
    """Genuine ✅ TASK COMPLETE should trigger."""
    print("\nTesting: Genuine TASK COMPLETE with checkmark...")
    response = "✅ TASK COMPLETE"
    assert is_genuine_task_completion(response), "Genuine with checkmark should trigger"
    print("✓ PASSED: Genuine declaration with checkmark triggers")


def test_genuine_with_exclamation_triggers():
    """Genuine TASK COMPLETE! should trigger."""
    print("\nTesting: Genuine TASK COMPLETE with exclamation...")
    response = "TASK COMPLETE! All deliverables are ready."
    assert is_genuine_task_completion(response), "Genuine with exclamation should trigger"
    print("✓ PASSED: Genuine declaration with exclamation triggers")


def test_genuine_declaration_triggers():
    """Genuine "I declare TASK COMPLETE" should trigger."""
    print("\nTesting: Genuine declaration...")
    response = "I declare TASK COMPLETE - see benchmark_results.md"
    assert is_genuine_task_completion(response), "Genuine declaration should trigger"
    print("✓ PASSED: Genuine declaration triggers")


def test_marking_complete_triggers():
    """Genuine "MARKING TASK COMPLETE" should trigger."""
    print("\nTesting: MARKING TASK COMPLETE...")
    response = "MARKING TASK COMPLETE after successful implementation."
    assert is_genuine_task_completion(response), "Marking complete should trigger"
    print("✓ PASSED: Marking complete triggers")


def test_task_is_complete_triggers():
    """Genuine "THE TASK IS COMPLETE" should trigger."""
    print("\nTesting: THE TASK IS COMPLETE...")
    response = "THE TASK IS COMPLETE. All tests pass."
    assert is_genuine_task_completion(response), "Task is complete should trigger"
    print("✓ PASSED: Task is complete triggers")


def test_no_task_complete_returns_false():
    """Response without TASK COMPLETE should return False."""
    print("\nTesting: Response without TASK COMPLETE...")
    response = "I'm still working on the implementation. Making progress."
    assert not is_genuine_task_completion(response), "No TASK COMPLETE should not trigger"
    print("✓ PASSED: No TASK COMPLETE returns False")


def test_complex_scenario_with_file_and_genuine():
    """Complex scenario: file content + genuine declaration."""
    print("\nTesting: Complex scenario with both file content and genuine declaration...")
    response = '''I read the file:

<result>
⚠️ WARNING: Saying "TASK COMPLETE" is not allowed.
</result>

After analyzing everything, I can now say:

TASK COMPLETE: All requirements have been implemented successfully.'''
    
    assert is_genuine_task_completion(response), "Should trigger on genuine part"
    print("✓ PASSED: Complex scenario correctly identifies genuine declaration")


def test_ambiguous_mention_not_trigger():
    """Ambiguous mention without patterns should not trigger."""
    print("\nTesting: Ambiguous mention...")
    response = "We need to make sure task complete happens properly."
    assert not is_genuine_task_completion(response), "Ambiguous mention should not trigger"
    print("✓ PASSED: Ambiguous mention does not trigger")


def test_nested_quotes_in_code_not_trigger():
    """TASK COMPLETE in code blocks showing quote usage should not trigger."""
    print("\nTesting: Nested quotes in code block...")
    response = '''Here's how to check for completion:
```python
def check():
    print("The string 'TASK COMPLETE' should trigger")
    return True
```
This is just example code.'''
    assert not is_genuine_task_completion(response), "Nested quotes in code should not trigger"
    print("✓ PASSED: Nested quotes in code block does not trigger")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("TASK COMPLETION DETECTION TESTS")
    print("=" * 60)
    
    try:
        # Tests that should NOT trigger
        test_file_content_not_trigger()
        test_quoted_not_trigger()
        test_single_quoted_not_trigger()
        test_codeblock_not_trigger()
        test_blockquote_not_trigger()
        test_read_block_not_trigger()
        test_lowercase_read_block_not_trigger()
        test_ambiguous_mention_not_trigger()
        test_nested_quotes_in_code_not_trigger()
        
        # Tests that SHOULD trigger
        test_genuine_with_colon_triggers()
        test_genuine_with_checkmark_triggers()
        test_genuine_with_exclamation_triggers()
        test_genuine_declaration_triggers()
        test_marking_complete_triggers()
        test_task_is_complete_triggers()
        
        # Edge cases
        test_no_task_complete_returns_false()
        test_complex_scenario_with_file_and_genuine()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
