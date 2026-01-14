#!/usr/bin/env python3
"""
Test suite for Environment Probe.
Tests environment discovery, probe execution, and .collab_env.md generation.
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.environment_probe import EnvironmentProbe, create_environment_probe


def test_environment_probe_creation():
    """Test EnvironmentProbe initialization"""
    print("Testing EnvironmentProbe creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test default configuration
        probe = EnvironmentProbe(tmpdir)
        assert probe.workspace_dir == tmpdir
        assert probe.enabled == True
        assert probe.output_file == os.path.join(tmpdir, '.collab_env.md')
        assert probe.timeout == 5
        
        print("  ✓ Default configuration works")
        
        # Test custom configuration
        config = {
            'enabled': False,
            'output_file': 'custom_env.md',
            'probe_timeout': 10
        }
        probe = EnvironmentProbe(tmpdir, config)
        assert probe.enabled == False
        assert probe.output_file == os.path.join(tmpdir, 'custom_env.md')
        assert probe.timeout == 10
        
        print("  ✓ Custom configuration works")
    print()


def test_environment_probe_disabled():
    """Test that probe returns None when disabled"""
    print("Testing disabled environment probe...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {'enabled': False}
        probe = EnvironmentProbe(tmpdir, config)
        
        result = probe.run()
        assert result is None
        
        # Verify no file was created
        output_file = os.path.join(tmpdir, '.collab_env.md')
        assert not os.path.exists(output_file)
        
        print("  ✓ Disabled probe returns None and creates no file")
    print()


def test_environment_probe_basic_execution():
    """Test basic probe execution and file generation"""
    print("Testing basic probe execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        probe = EnvironmentProbe(tmpdir)
        
        result = probe.run()
        assert result is not None
        assert os.path.exists(result)
        
        # Read generated file
        with open(result, 'r') as f:
            content = f.read()
        
        # Verify file contains expected sections
        assert '# Environment Summary' in content
        assert '## System' in content
        assert '## Resources' in content
        assert '## Build Toolchain' in content
        assert '## Reverse Engineering Tools' in content
        assert '## Documentation Access' in content
        assert '## Quick Reference' in content
        assert '## Notes for Agents' in content
        
        print("  ✓ Probe generates .collab_env.md with all sections")
    print()


def test_environment_probe_content():
    """Test that probe captures actual system information"""
    print("Testing probe content accuracy...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        probe = EnvironmentProbe(tmpdir)
        
        result = probe.run()
        assert result is not None
        
        # Read generated file
        with open(result, 'r') as f:
            content = f.read()
        
        # Verify system info is captured (these should be available on any Linux system)
        assert 'Kernel' in content
        assert 'Architecture' in content
        
        # Verify at least some tools are detected
        # Python should be available since we're running in Python
        assert 'Python 3' in content
        
        print("  ✓ Probe captures real system information")
    print()


def test_custom_probes():
    """Test adding custom probes"""
    print("Testing custom probes...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            'custom_probes': {
                'test_echo': 'echo "test_value"',
                'test_pwd': 'pwd'
            }
        }
        probe = EnvironmentProbe(tmpdir, config)
        
        # Execute probes
        results = probe._execute_probes()
        
        # Verify custom probes ran
        assert 'test_echo' in results
        assert results['test_echo'] == 'test_value'
        assert 'test_pwd' in results
        assert tmpdir in results['test_pwd']
        
        print("  ✓ Custom probes execute correctly")
    print()


def test_disabled_probes():
    """Test disabling specific probes"""
    print("Testing disabled probes...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            'disabled_probes': ['rustc', 'cargo', 'go', 'node']
        }
        probe = EnvironmentProbe(tmpdir, config)
        
        # Verify disabled probes are not in probe list
        assert 'rustc' not in probe.probes
        assert 'cargo' not in probe.probes
        assert 'go' not in probe.probes
        assert 'node' not in probe.probes
        
        # Verify other probes still exist
        assert 'gcc' in probe.probes
        assert 'python3' in probe.probes
        
        print("  ✓ Specific probes can be disabled")
    print()


def test_probe_timeout():
    """Test probe timeout handling"""
    print("Testing probe timeout...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            'probe_timeout': 1,  # 1 second timeout
            'custom_probes': {
                'slow_command': 'sleep 5 && echo "done"'
            }
        }
        probe = EnvironmentProbe(tmpdir, config)
        
        # Execute probes
        results = probe._execute_probes()
        
        # Verify timeout was handled
        assert 'slow_command' in results
        assert 'timed out' in results['slow_command'].lower()
        
        print("  ✓ Probe timeout is handled gracefully")
    print()


def test_factory_function():
    """Test create_environment_probe factory function"""
    print("Testing factory function...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        probe = create_environment_probe(tmpdir)
        assert isinstance(probe, EnvironmentProbe)
        assert probe.workspace_dir == tmpdir
        
        probe_with_config = create_environment_probe(tmpdir, {'enabled': False})
        assert probe_with_config.enabled == False
        
        print("  ✓ Factory function works correctly")
    print()


def test_tool_availability_detection():
    """Test that tool availability is correctly detected"""
    print("Testing tool availability detection...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        probe = EnvironmentProbe(tmpdir)
        
        result = probe.run()
        assert result is not None
        
        # Read generated file
        with open(result, 'r') as f:
            content = f.read()
        
        # Check that availability markers are present
        assert '✓' in content or '✗' in content
        
        # Python 3 should be available (we're running in Python)
        # Check that it's marked as available in the table
        lines = content.split('\n')
        python_line = None
        for line in lines:
            if 'Python 3' in line and '|' in line:
                python_line = line
                break
        
        if python_line:
            assert '✓' in python_line
            print("  ✓ Tool availability correctly detected (Python 3 found)")
        else:
            print("  ⚠ Warning: Could not verify Python 3 detection in table")
    print()


def test_probe_error_handling():
    """Test probe error handling for failed commands"""
    print("Testing probe error handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            'custom_probes': {
                'invalid_command': 'this_command_does_not_exist_12345'
            }
        }
        probe = EnvironmentProbe(tmpdir, config)
        
        # Execute probes - should not raise exception
        results = probe._execute_probes()
        
        # Verify error was captured
        assert 'invalid_command' in results
        # Command should either return empty or error message
        assert results['invalid_command'] in ['not available', ''] or 'not found' in results['invalid_command'].lower()
        
        print("  ✓ Probe handles command errors gracefully")
    print()


def test_output_file_custom_location():
    """Test custom output file location"""
    print("Testing custom output file location...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_filename = 'my_environment.md'
        config = {
            'output_file': custom_filename
        }
        probe = EnvironmentProbe(tmpdir, config)
        
        result = probe.run()
        expected_path = os.path.join(tmpdir, custom_filename)
        
        assert result == expected_path
        assert os.path.exists(expected_path)
        
        print("  ✓ Custom output file location works")
    print()


def run_all_tests():
    """Run all test functions"""
    print("=" * 70)
    print("Environment Probe Test Suite")
    print("=" * 70)
    print()
    
    test_functions = [
        test_environment_probe_creation,
        test_environment_probe_disabled,
        test_environment_probe_basic_execution,
        test_environment_probe_content,
        test_custom_probes,
        test_disabled_probes,
        test_probe_timeout,
        test_factory_function,
        test_tool_availability_detection,
        test_probe_error_handling,
        test_output_file_custom_location,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"  ✗ ERROR: {e}")
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
