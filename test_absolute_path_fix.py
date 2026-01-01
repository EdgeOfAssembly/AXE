#!/usr/bin/env python3
"""
Manual test to verify the absolute path fix works as described in the problem statement.
This simulates the scenario where an agent uses an absolute path like /tmp/AXE/copilot.txt
when the project directory is /tmp/AXE/.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, ResponseProcessor, ToolRunner


def test_problem_statement_scenario():
    """
    Reproduce the exact scenario from the problem statement:
    - Project directory: /tmp/AXE/
    - Agent tries to write to: /tmp/AXE/copilot.txt (absolute path)
    - Should succeed because the path is within the project directory
    """
    print("="*70)
    print("TESTING PROBLEM STATEMENT SCENARIO")
    print("="*70)
    
    # Create a temporary directory that mimics /tmp/AXE/
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use the tmpdir as our "project directory"
        project_dir = tmpdir
        print(f"\nProject directory: {project_dir}")
        
        config = Config()
        tool_runner = ToolRunner(config, project_dir)
        processor = ResponseProcessor(config, project_dir, tool_runner)
        
        # Test 1: Absolute path within project (the failing case from problem statement)
        abs_path_within = os.path.join(project_dir, "copilot.txt")
        print(f"\nTest 1: Agent uses absolute path: {abs_path_within}")
        print(f"        (This is WITHIN project directory)")
        
        response = f"""```WRITE {abs_path_within}
Hello from Copilot!
This file was created using an absolute path.
```"""
        
        result = processor.process_response(response, "copilot")
        print(f"\nResult: {result}")
        
        if "✓ File written successfully" in result:
            print("✅ SUCCESS: Absolute path within project directory is allowed!")
            if os.path.exists(abs_path_within):
                with open(abs_path_within, 'r') as f:
                    content = f.read()
                print(f"   File content:\n   {content}")
            else:
                print("❌ ERROR: Success message appeared but file doesn't exist!")
                return False
        else:
            print("❌ FAILED: Absolute path within project was rejected!")
            print(f"   This is the bug described in the problem statement.")
            return False
        
        # Test 2: Relative path (should still work)
        print(f"\nTest 2: Agent uses relative path: claude.txt")
        response2 = """```WRITE claude.txt
Hello from Claude!
This file was created using a relative path.
```"""
        
        result2 = processor.process_response(response2, "claude")
        
        if "✓ File written successfully" in result2:
            print("✅ SUCCESS: Relative path still works!")
        else:
            print("❌ FAILED: Relative path broke!")
            return False
        
        # Test 3: Absolute path OUTSIDE project (should be blocked)
        outside_path = "/etc/passwd"
        print(f"\nTest 3: Agent uses absolute path outside project: {outside_path}")
        
        response3 = f"""```WRITE {outside_path}
This should be blocked!
```"""
        
        result3 = processor.process_response(response3, "bad_agent")
        
        if "ERROR" in result3 or "outside" in result3.lower() or "denied" in result3.lower():
            print("✅ SUCCESS: Absolute path outside project is blocked!")
        else:
            print("❌ FAILED: Security issue - absolute path outside project was allowed!")
            return False
        
        # Test 4: Path traversal (should be blocked)
        print(f"\nTest 4: Agent tries path traversal: ../../../etc/passwd")
        
        response4 = """```WRITE ../../../etc/passwd
This should be blocked!
```"""
        
        result4 = processor.process_response(response4, "bad_agent")
        
        if "ERROR" in result4 or "outside" in result4.lower() or "denied" in result4.lower():
            print("✅ SUCCESS: Path traversal is blocked!")
        else:
            print("❌ FAILED: Security issue - path traversal was allowed!")
            return False
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nSummary:")
        print("  ✓ Absolute paths WITHIN project directory are now allowed")
        print("  ✓ Relative paths still work")
        print("  ✓ Absolute paths OUTSIDE project directory are blocked")
        print("  ✓ Path traversal attacks are blocked")
        print("\nThe fix resolves the issue described in the problem statement!")
        
        return True


if __name__ == '__main__':
    success = test_problem_statement_scenario()
    sys.exit(0 if success else 1)
