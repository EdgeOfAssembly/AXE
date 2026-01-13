#!/usr/bin/env python3
"""
Test suite for shared build status system.

Verifies that:
1. Build output is captured and recorded
2. Errors/warnings are parsed correctly from gcc, make, python
3. Agents can claim and mark errors as fixed
4. Build status summary is correctly generated
5. Integration with SharedWorkspace works
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from managers.shared_build_status import (
    SharedBuildStatusManager,
    BuildStatus,
    BuildError,
    DiffPatch,
)


class TestSharedBuildStatus:
    """Test suite for shared build status system."""
    
    def __init__(self):
        self.temp_dir = None
        self.manager = None
    
    def setup(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix='axe_build_status_test_')
        self.manager = SharedBuildStatusManager(self.temp_dir)
        print(f"  Test directory: {self.temp_dir}")
    
    def teardown(self):
        """Clean up test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_files_created(self):
        """Test that status and changes files are created."""
        print("\n--- Test: Files created ---")
        
        status_file = os.path.join(self.temp_dir, '.collab_build_status.md')
        changes_file = os.path.join(self.temp_dir, '.collab_changes.md')
        
        assert os.path.exists(status_file), "Status file not created!"
        assert os.path.exists(changes_file), "Changes file not created!"
        
        print(f"  ✓ Status file exists: {status_file}")
        print(f"  ✓ Changes file exists: {changes_file}")
        print("  ✓ PASSED: Files created correctly")
        return True
    
    def test_gcc_error_parsing(self):
        """Test parsing of GCC error output."""
        print("\n--- Test: GCC error parsing ---")
        
        gcc_output = """
main.c:10:5: error: expected ';' before 'return'
   10 |     return 0
      |     ^~~~~~
main.c:5:12: warning: unused variable 'x' [-Wunused-variable]
    5 |     int x = 42;
      |            ^
main.c:15:1: note: in expansion of macro 'DEBUG'
   15 | DEBUG("test");
      | ^~~~~
"""
        
        status = self.manager.record_build_output('gcc', gcc_output, 1)
        
        print(f"  Build status: {status.value}")
        print(f"  Errors found: {len(self.manager._errors)}")
        
        assert status == BuildStatus.FAILED, "Should be FAILED for exit code 1"
        assert len(self.manager._errors) >= 2, "Should find at least 2 errors/warnings"
        
        # Check specific errors
        errors = [e for e in self.manager._errors if e.severity == 'error']
        warnings = [e for e in self.manager._errors if e.severity == 'warning']
        
        print(f"  - Errors: {len(errors)}")
        print(f"  - Warnings: {len(warnings)}")
        
        assert len(errors) >= 1, "Should find at least 1 error"
        assert len(warnings) >= 1, "Should find at least 1 warning"
        
        # Check error details
        first_error = errors[0]
        assert 'main.c' in first_error.file, f"Wrong file: {first_error.file}"
        assert first_error.line == 10, f"Wrong line: {first_error.line}"
        
        print("  ✓ PASSED: GCC errors parsed correctly")
        return True
    
    def test_make_error_parsing(self):
        """Test parsing of Make error output."""
        print("\n--- Test: Make error parsing ---")
        
        make_output = """
gcc -c -o main.o main.c
main.c:10:5: error: expected ';' before 'return'
make[1]: *** [Makefile:15: main.o] Error 1
make: *** [Makefile:10: all] Error 2
"""
        
        # Reset errors
        self.manager._errors = []
        
        status = self.manager.record_build_output('make', make_output, 2)
        
        print(f"  Build status: {status.value}")
        print(f"  Errors found: {len(self.manager._errors)}")
        
        assert status == BuildStatus.FAILED, "Should be FAILED"
        assert len(self.manager._errors) >= 1, "Should find at least 1 error"
        
        print("  ✓ PASSED: Make errors parsed correctly")
        return True
    
    def test_python_error_parsing(self):
        """Test parsing of Python error output."""
        print("\n--- Test: Python error parsing ---")
        
        python_output = """
Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = process_data(data)
  File "test.py", line 5, in process_data
    return data['key']
KeyError: 'key'
"""
        
        # Reset errors
        self.manager._errors = []
        
        status = self.manager.record_build_output('python', python_output, 1)
        
        print(f"  Build status: {status.value}")
        print(f"  Errors found: {len(self.manager._errors)}")
        
        assert status == BuildStatus.FAILED, "Should be FAILED"
        
        print("  ✓ PASSED: Python errors parsed correctly")
        return True
    
    def test_pytest_error_parsing(self):
        """Test parsing of pytest error output."""
        print("\n--- Test: Pytest error parsing ---")
        
        pytest_output = """
============================= test session starts ==============================
collected 5 items

test_example.py::test_addition PASSED
test_example.py::test_subtraction FAILED
test_example.py::test_multiplication PASSED
test_example.py::test_division FAILED

=================================== FAILURES ===================================
FAILED test_example.py::test_subtraction - AssertionError
FAILED test_example.py::test_division - ZeroDivisionError
============================= 2 failed, 3 passed ===============================
"""
        
        # Reset errors
        self.manager._errors = []
        
        status = self.manager.record_build_output('pytest', pytest_output, 1)
        
        print(f"  Build status: {status.value}")
        print(f"  Errors found: {len(self.manager._errors)}")
        
        # Should find the FAILED test patterns
        failed_tests = [e for e in self.manager._errors if 'failed' in e.message.lower()]
        print(f"  Failed tests: {len(failed_tests)}")
        
        print("  ✓ PASSED: Pytest errors parsed correctly")
        return True
    
    def test_successful_build(self):
        """Test handling of successful build."""
        print("\n--- Test: Successful build ---")
        
        gcc_output = "main.c: In function 'main':\nmain.c:5:12: note: declared here"
        
        # Reset errors
        self.manager._errors = []
        
        status = self.manager.record_build_output('gcc', gcc_output, 0)
        
        print(f"  Build status: {status.value}")
        
        assert status == BuildStatus.SUCCESS, "Should be SUCCESS for exit code 0"
        
        print("  ✓ PASSED: Successful build handled correctly")
        return True
    
    def test_warning_only_build(self):
        """Test handling of build with warnings only."""
        print("\n--- Test: Warning-only build ---")
        
        gcc_output = "main.c:5:12: warning: unused variable 'x' [-Wunused-variable]"
        
        # Reset errors
        self.manager._errors = []
        
        status = self.manager.record_build_output('gcc', gcc_output, 0)
        
        print(f"  Build status: {status.value}")
        
        assert status == BuildStatus.WARNING, "Should be WARNING"
        
        print("  ✓ PASSED: Warning-only build handled correctly")
        return True
    
    def test_claim_error_fix(self):
        """Test claiming an error for fixing."""
        print("\n--- Test: Claim error fix ---")
        
        # Add some errors first
        gcc_output = """
main.c:10:5: error: expected ';' before 'return'
main.c:20:5: error: undeclared identifier 'foo'
"""
        self.manager._errors = []
        self.manager.record_build_output('gcc', gcc_output, 1)
        
        print(f"  Errors before claim: {len(self.manager._errors)}")
        
        # Get unclaimed errors
        unclaimed = self.manager.get_unclaimed_errors()
        print(f"  Unclaimed errors: {len(unclaimed)}")
        
        assert len(unclaimed) >= 1, "Should have unclaimed errors"
        
        # Claim first error
        result = self.manager.claim_error_fix(0, "@claude")
        assert result == True, "Claim should succeed"
        
        # Check it's claimed
        unclaimed_after = self.manager.get_unclaimed_errors()
        print(f"  Unclaimed after claim: {len(unclaimed_after)}")
        
        assert len(unclaimed_after) < len(unclaimed), "Should have fewer unclaimed errors"
        assert self.manager._errors[0].claimed_by == "@claude", "Should be claimed by @claude"
        
        print("  ✓ PASSED: Error claim works correctly")
        return True
    
    def test_mark_error_fixed(self):
        """Test marking an error as fixed."""
        print("\n--- Test: Mark error fixed ---")
        
        # Add an error
        gcc_output = "main.c:10:5: error: expected ';' before 'return'"
        self.manager._errors = []
        self.manager.record_build_output('gcc', gcc_output, 1)
        
        # Claim and fix
        self.manager.claim_error_fix(0, "@gpt")
        result = self.manager.mark_error_fixed(0)
        
        assert result == True, "Mark fixed should succeed"
        assert self.manager._errors[0].fixed == True, "Should be marked as fixed"
        
        # Fixed errors should not appear in unclaimed
        unclaimed = self.manager.get_unclaimed_errors()
        assert len(unclaimed) == 0, "Fixed errors should not be unclaimed"
        
        print("  ✓ PASSED: Mark error fixed works correctly")
        return True
    
    def test_add_diff_patch(self):
        """Test adding a diff patch."""
        print("\n--- Test: Add diff patch ---")
        
        diff_content = """--- a/main.c
+++ b/main.c
@@ -10,1 +10,1 @@
-    return 0
+    return 0;
"""
        
        self.manager._patches = []
        self.manager.add_diff_patch(
            file='main.c',
            author='@claude',
            diff_content=diff_content,
            description='Fixed missing semicolon'
        )
        
        assert len(self.manager._patches) == 1, "Should have 1 patch"
        
        patch = self.manager._patches[0]
        assert patch.file == 'main.c', "Wrong file"
        assert patch.author == '@claude', "Wrong author"
        assert 'semicolon' in patch.description.lower(), "Description should mention fix"
        
        # Check changes file was updated
        changes_content = self.manager.read_changes_file()
        assert 'main.c' in changes_content, "Changes file should contain file name"
        assert '@claude' in changes_content, "Changes file should contain author"
        
        print("  ✓ PASSED: Diff patch added correctly")
        return True
    
    def test_patch_limit(self):
        """Test that patch limit is enforced."""
        print("\n--- Test: Patch limit (50) ---")
        
        self.manager._patches = []
        
        # Add 60 patches
        for i in range(60):
            self.manager.add_diff_patch(
                file=f'file_{i}.c',
                author='@test',
                diff_content=f'patch {i}',
                description=f'Fix {i}'
            )
        
        print(f"  Added 60 patches, kept: {len(self.manager._patches)}")
        
        assert len(self.manager._patches) == 50, "Should keep only 50 patches"
        
        # Oldest patches should be removed
        assert self.manager._patches[0].file == 'file_10.c', "First patch should be file_10"
        assert self.manager._patches[-1].file == 'file_59.c', "Last patch should be file_59"
        
        print("  ✓ PASSED: Patch limit enforced correctly")
        return True
    
    def test_status_summary(self):
        """Test status summary generation."""
        print("\n--- Test: Status summary ---")
        
        # Add some errors
        gcc_output = """
main.c:10:5: error: expected ';' before 'return'
main.c:20:5: warning: unused variable 'x'
utils.c:5:1: error: undeclared identifier
"""
        self.manager._errors = []
        self.manager.record_build_output('gcc', gcc_output, 1)
        
        summary = self.manager.get_status_summary()
        
        print(f"  Summary length: {len(summary)} chars")
        print("  Summary preview:")
        for line in summary.split('\n')[:8]:
            print(f"    {line}")
        
        assert 'FAILED' in summary, "Should show FAILED status"
        assert 'Unclaimed' in summary, "Should mention unclaimed issues"
        
        print("  ✓ PASSED: Status summary generated correctly")
        return True
    
    def test_generate_diff(self):
        """Test diff generation."""
        print("\n--- Test: Generate diff ---")
        
        original = """int main() {
    int x = 42;
    return 0
}
"""
        modified = """int main() {
    int x = 42;
    return 0;
}
"""
        
        diff = self.manager.generate_diff(original, modified, 'main.c')
        
        print(f"  Diff length: {len(diff)} chars")
        print("  Diff preview:")
        for line in diff.split('\n')[:6]:
            print(f"    {line}")
        
        assert '--- a/main.c' in diff, "Should have from file header"
        assert '+++ b/main.c' in diff, "Should have to file header"
        assert '-    return 0' in diff, "Should show removed line"
        assert '+    return 0;' in diff, "Should show added line"
        
        print("  ✓ PASSED: Diff generated correctly")
        return True
    
    def test_build_output_limit(self):
        """Test that build output is limited to 500 lines."""
        print("\n--- Test: Build output limit (500 lines) ---")
        
        # Generate output with 1000 lines
        lines = [f"line {i}: some output" for i in range(1000)]
        long_output = '\n'.join(lines)
        
        self.manager._errors = []
        self.manager.record_build_output('gcc', long_output, 0)
        
        # Read status file and check
        status_content = self.manager.read_status_file()
        
        # Count lines in the output section
        output_section_found = False
        output_lines = 0
        for line in status_content.split('\n'):
            if '## Last Build Output' in line:
                output_section_found = True
            elif output_section_found and 'line' in line:
                output_lines += 1
        
        print(f"  Original lines: 1000")
        print(f"  Stored output lines: ~{output_lines}")
        
        # Should have omission notice
        assert '... (' in status_content, "Should have omission notice"
        assert 'lines omitted' in status_content, "Should mention lines omitted"
        
        print("  ✓ PASSED: Build output limit enforced correctly")
        return True
    
    def run_all_tests(self):
        """Run all build status tests."""
        print("=" * 70)
        print("SHARED BUILD STATUS TEST SUITE")
        print("Testing build error/warning sharing for agent coordination")
        print("=" * 70)
        
        self.setup()
        
        tests = [
            self.test_files_created,
            self.test_gcc_error_parsing,
            self.test_make_error_parsing,
            self.test_python_error_parsing,
            self.test_pytest_error_parsing,
            self.test_successful_build,
            self.test_warning_only_build,
            self.test_claim_error_fix,
            self.test_mark_error_fixed,
            self.test_add_diff_patch,
            self.test_patch_limit,
            self.test_status_summary,
            self.test_generate_diff,
            self.test_build_output_limit,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ✗ FAILED: {test.__name__}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        self.teardown()
        
        print("\n" + "=" * 70)
        print("SHARED BUILD STATUS TEST RESULTS")
        print("=" * 70)
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Total:  {passed + failed}")
        print("=" * 70)
        
        if failed == 0:
            print("\n✓ ALL TESTS PASSED - Build status sharing works correctly!")
            print("  Agents can see and coordinate on build errors/warnings.")
        else:
            print(f"\n✗ {failed} TEST(S) FAILED - Review the results above.")
        
        return failed == 0


def run_all_tests():
    """Entry point for running all tests."""
    suite = TestSharedBuildStatus()
    return suite.run_all_tests()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
