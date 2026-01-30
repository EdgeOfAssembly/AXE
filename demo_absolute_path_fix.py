#!/usr/bin/env python3
"""
Demonstration script showing the WRITE block absolute path fix.
This demonstrates the exact issue reported in the problem statement:
- Before: Agents using absolute paths like /tmp/AXE/copilot.txt would fail
- After: Agents can now use absolute paths within the project directory
Run this script to see the fix in action!
"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axe import Config, ResponseProcessor, ToolRunner
def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)
def print_test(test_num, description):
    """Print test info."""
    print(f"\n[Test {test_num}] {description}")
    print("-" * 70)
def demonstrate_fix():
    """Demonstrate the absolute path fix."""
    print_header("WRITE BLOCK ABSOLUTE PATH FIX DEMONSTRATION")
    print("\nPROBLEM STATEMENT:")
    print("  Before this fix, WRITE blocks rejected ALL absolute paths,")
    print("  even when they pointed to files within the project directory.")
    print("\n  Example:")
    print("    Project dir: /tmp/AXE/")
    print("    Agent writes: /tmp/AXE/copilot.txt")
    print("    Result: ❌ REJECTED with 'path traversal not allowed'")
    with tempfile.TemporaryDirectory() as project_dir:
        print(f"\nSetting up test project directory: {project_dir}")
        config = Config()
        tool_runner = ToolRunner(config, project_dir)
        processor = ResponseProcessor(config, project_dir, tool_runner)
        # Test 1: Relative path (was always working)
        print_test(1, "Relative Path (baseline - always worked)")
        relative_file = "relative_test.txt"
        response1 = f"""```WRITE {relative_file}
Hello from relative path!
```"""
        result1 = processor.process_response(response1, "agent")
        if "✓ File written successfully" in result1:
            print("✅ SUCCESS: Relative path works")
            print(f"   Created: {os.path.join(project_dir, relative_file)}")
        else:
            print("❌ FAILED: Relative path should work")
            return False
        # Test 2: Absolute path within project (THE FIX)
        print_test(2, "Absolute Path WITHIN Project (the fix!)")
        abs_file = os.path.join(project_dir, "absolute_test.txt")
        print(f"   Attempting to write to: {abs_file}")
        print(f"   This is within: {project_dir}")
        response2 = f"""```WRITE {abs_file}
Hello from absolute path within project!
This previously FAILED but now WORKS!
```"""
        result2 = processor.process_response(response2, "copilot")
        if "✓ File written successfully" in result2:
            print("✅ SUCCESS: Absolute path within project now works!")
            print(f"   Created: {abs_file}")
            print("\n   🎉 This is the FIX - previously this would fail!")
            if os.path.exists(abs_file):
                with open(abs_file, 'r') as f:
                    content = f.read()
                print("\n   File contents:")
                for line in content.split('\n'):
                    print(f"   > {line}")
        else:
            print("❌ FAILED: Absolute path within project should work now")
            print(f"   Result: {result2}")
            return False
        # Test 3: Absolute path in subdirectory
        print_test(3, "Absolute Path in SUBDIRECTORY (also fixed)")
        subdir = os.path.join(project_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        abs_subdir_file = os.path.join(subdir, "nested.txt")
        print(f"   Attempting to write to: {abs_subdir_file}")
        response3 = f"""```WRITE {abs_subdir_file}
Nested file via absolute path!
```"""
        result3 = processor.process_response(response3, "gpt")
        if "✓ File written successfully" in result3:
            print("✅ SUCCESS: Absolute path in subdirectory works!")
            print(f"   Created: {abs_subdir_file}")
        else:
            print("❌ FAILED: Absolute path in subdirectory should work")
            return False
        # Test 4: Security - absolute path OUTSIDE project
        print_test(4, "Security Check: Absolute Path OUTSIDE Project")
        outside_path = "/etc/passwd"
        print(f"   Attempting to write to: {outside_path}")
        print(f"   This is OUTSIDE: {project_dir}")
        response4 = f"""```WRITE {outside_path}
This should be blocked!
```"""
        result4 = processor.process_response(response4, "bad_agent")
        if "ERROR" in result4 or "outside" in result4.lower():
            print("✅ SUCCESS: Absolute path outside project is blocked!")
            print("   Security maintained - paths outside project are rejected")
        else:
            print("❌ SECURITY ISSUE: Absolute path outside project should be blocked!")
            return False
        # Test 5: Security - path traversal
        print_test(5, "Security Check: Path Traversal Attack")
        print("   Attempting: ../../../etc/passwd")
        response5 = """```WRITE ../../../etc/passwd
Path traversal attack!
```"""
        result5 = processor.process_response(response5, "bad_agent")
        if "ERROR" in result5 or "outside" in result5.lower():
            print("✅ SUCCESS: Path traversal is blocked!")
            print("   Security maintained - ../ traversal is rejected")
        else:
            print("❌ SECURITY ISSUE: Path traversal should be blocked!")
            return False
        # Summary
        print_header("DEMONSTRATION COMPLETE")
        print("\n✅ All tests passed! The fix works correctly:")
        print("\n  FIXED:")
        print("  ✓ Absolute paths WITHIN project directory now work")
        print("  ✓ Agents can use paths like /tmp/AXE/file.txt")
        print("  ✓ Both root and subdirectory absolute paths work")
        print("\n  MAINTAINED:")
        print("  ✓ Relative paths still work as before")
        print("  ✓ Absolute paths OUTSIDE project are blocked (security)")
        print("  ✓ Path traversal attacks are blocked (security)")
        print("\n  IMPACT:")
        print("  ✓ GitHub Copilot can now use absolute paths")
        print("  ✓ GPT can now use absolute paths")
        print("  ✓ All agents can specify exact locations")
        print("  ✓ No security vulnerabilities introduced")
        print("\n  FILES CREATED IN THIS DEMO:")
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, project_dir)
                print(f"    - {relpath}")
        print("\n" + "="*70)
        return True
if __name__ == '__main__':
    success = demonstrate_fix()
    sys.exit(0 if success else 1)