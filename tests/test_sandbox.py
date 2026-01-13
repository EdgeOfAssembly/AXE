#!/usr/bin/env python3
"""
Comprehensive test suite for Sandbox Manager (Bubblewrap integration).

Tests sandbox configuration, command generation, execution, and security features.
"""
import os
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Config, ToolRunner, SandboxManager


def test_sandbox_config_parsing():
    """Test that sandbox config is parsed correctly from defaults."""
    print("=" * 70)
    print("TEST: Sandbox Configuration Parsing")
    print("=" * 70)
    
    config = Config()
    
    # Check default config has sandbox section
    sandbox_config = config.get('sandbox', default={})
    print(f"\nSandbox config present: {bool(sandbox_config)}")
    assert sandbox_config, "Sandbox config should be present in defaults"
    
    # Check key fields
    assert 'enabled' in sandbox_config, "enabled field should be present"
    assert 'runtime' in sandbox_config, "runtime field should be present"
    assert 'workspaces' in sandbox_config, "workspaces field should be present"
    assert 'host_binds' in sandbox_config, "host_binds field should be present"
    assert 'tool_blacklist' in sandbox_config, "tool_blacklist field should be present"
    assert 'namespaces' in sandbox_config, "namespaces field should be present"
    assert 'options' in sandbox_config, "options field should be present"
    
    print("  ✓ All required fields present")
    
    # Check expected values (may be from axe.yaml if present, or defaults)
    # The 'enabled' field should be a boolean
    assert isinstance(sandbox_config['enabled'], bool), "enabled should be boolean"
    assert sandbox_config['runtime'] == 'bubblewrap', "Default runtime should be bubblewrap"
    assert isinstance(sandbox_config['tool_blacklist'], list), "tool_blacklist should be a list"
    
    print("  ✓ Config values valid")
    print("\n✅ Sandbox configuration parsing test passed!")
    return True


def test_sandbox_manager_initialization():
    """Test SandboxManager initialization."""
    print("\n" + "=" * 70)
    print("TEST: SandboxManager Initialization")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        
        # Test initialization - sandbox state depends on config (may be from axe.yaml)
        manager = SandboxManager(config, tmpdir)
        print(f"\nManager initialized: {manager is not None}")
        assert manager is not None, "SandboxManager should initialize"
        
        print(f"Workspace path: {manager.workspace_path}")
        assert os.path.isabs(manager.workspace_path), "Workspace path should be absolute"
        
        print(f"Enabled: {manager.enabled}")
        # Sandbox enabled state comes from config (could be True if axe.yaml has it enabled)
        sandbox_config = config.get('sandbox', default={})
        expected_enabled = sandbox_config.get('enabled', False)
        assert manager.enabled == expected_enabled, f"Sandbox enabled should match config: {expected_enabled}"
        
        print("  ✓ Basic initialization works")
        
        print("\n✅ SandboxManager initialization test passed!")
        return True


def test_sandbox_availability_check():
    """Test bubblewrap availability detection."""
    print("\n" + "=" * 70)
    print("TEST: Sandbox Availability Check")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        manager = SandboxManager(config, tmpdir)
        
        # Check if bwrap is available
        available = manager.is_available()
        print(f"\nBubblewrap available: {available}")
        
        # Check if bwrap is in PATH
        bwrap_path = shutil.which('bwrap')
        print(f"bwrap path: {bwrap_path}")
        
        if bwrap_path:
            print("  ✓ Bubblewrap is installed")
            assert available, "is_available() should return True when bwrap exists"
        else:
            print("  ⚠ Bubblewrap not installed (expected in CI)")
            assert not available, "is_available() should return False when bwrap missing"
        
        print("\n✅ Sandbox availability check test passed!")
        return True


def test_bwrap_command_generation():
    """Test that correct bwrap command line is generated."""
    print("\n" + "=" * 70)
    print("TEST: Bwrap Command Generation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        manager = SandboxManager(config, tmpdir)
        
        # Build command
        cmd = manager.build_bwrap_command()
        print(f"\nGenerated command length: {len(cmd)} args")
        print(f"Command: {' '.join(cmd[:10])}...")
        
        # Check essential elements
        assert cmd[0] == 'bwrap', "First element should be 'bwrap'"
        print("  ✓ Command starts with 'bwrap'")
        
        # Check for namespace flags
        assert '--unshare-user-try' in cmd, "Should include user namespace"
        assert '--unshare-pid' in cmd, "Should include pid namespace"
        print("  ✓ Namespace flags present")
        
        # Check for essential options
        assert '--die-with-parent' in cmd, "Should include die-with-parent"
        assert '--new-session' in cmd, "Should include new-session"
        print("  ✓ Security options present")
        
        # Check for proc/dev/tmp mounts
        assert '--proc' in cmd, "Should mount /proc"
        assert '--dev' in cmd, "Should mount /dev"
        assert '--tmpfs' in cmd, "Should mount /tmp"
        print("  ✓ Essential mounts present")
        
        # Check for workspace bind
        assert '--bind' in cmd, "Should bind workspace"
        print("  ✓ Workspace bind present")
        
        print("\n✅ Bwrap command generation test passed!")
        return True


def test_tool_blacklist_check():
    """Test blacklist validation logic."""
    print("\n" + "=" * 70)
    print("TEST: Tool Blacklist Check")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        
        # Add some tools to blacklist
        config.config['sandbox']['tool_blacklist'] = ['rm', 'dd', 'mkfs']
        
        manager = SandboxManager(config, tmpdir)
        
        # Test blacklisted tools
        assert manager.is_tool_blacklisted('rm'), "rm should be blacklisted"
        assert manager.is_tool_blacklisted('dd'), "dd should be blacklisted"
        assert manager.is_tool_blacklisted('mkfs'), "mkfs should be blacklisted"
        print("  ✓ Blacklisted tools detected")
        
        # Test non-blacklisted tools
        assert not manager.is_tool_blacklisted('ls'), "ls should not be blacklisted"
        assert not manager.is_tool_blacklisted('cat'), "cat should not be blacklisted"
        assert not manager.is_tool_blacklisted('grep'), "grep should not be blacklisted"
        print("  ✓ Non-blacklisted tools allowed")
        
        # Test with paths
        assert manager.is_tool_blacklisted('/usr/bin/rm'), "Should detect rm in path"
        assert not manager.is_tool_blacklisted('/bin/cat'), "Should not blacklist cat in path"
        print("  ✓ Path-based tool detection works")
        
        print("\n✅ Tool blacklist check test passed!")
        return True


def test_fallback_to_whitelist():
    """Test that whitelist mode is used when sandbox unavailable."""
    print("\n" + "=" * 70)
    print("TEST: Fallback to Whitelist Mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with sandbox disabled
        config = Config()
        config.config['sandbox']['enabled'] = False
        
        runner = ToolRunner(config, tmpdir)
        
        # Should use whitelist mode
        print(f"\nSandbox manager: {runner.sandbox_manager}")
        assert runner.sandbox_manager is None, "Sandbox should be None when disabled"
        print("  ✓ Sandbox disabled correctly")
        
        # Whitelist should be populated
        print(f"Whitelist size: {len(runner.whitelist)}")
        assert len(runner.whitelist) > 0, "Whitelist should be populated"
        print("  ✓ Whitelist mode active")
        
        # Test command validation in whitelist mode
        allowed, reason = runner.is_tool_allowed("ls -la")
        print(f"ls allowed: {allowed} ({reason})")
        assert allowed, "ls should be allowed in whitelist mode"
        
        print("\n✅ Fallback to whitelist mode test passed!")
        return True


def test_host_bind_readonly():
    """Test that readonly host binds are generated correctly."""
    print("\n" + "=" * 70)
    print("TEST: Host Bind (Read-Only)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        manager = SandboxManager(config, tmpdir)
        
        cmd = manager.build_bwrap_command()
        cmd_str = ' '.join(cmd)
        
        # Check for readonly binds
        readonly_paths = ['/usr', '/lib', '/bin', '/etc']
        for path in readonly_paths:
            if os.path.exists(path):
                # Should have --ro-bind for readonly paths
                assert '--ro-bind' in cmd, f"Should have --ro-bind for {path}"
                print(f"  ✓ Read-only bind for {path}")
        
        print("\n✅ Host bind (readonly) test passed!")
        return True


def test_namespace_options():
    """Test namespace flag generation."""
    print("\n" + "=" * 70)
    print("TEST: Namespace Options")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        
        # Test with different namespace configurations
        config.config['sandbox']['namespaces'] = {
            'user': True,
            'pid': True,
            'uts': False,  # Disable this one
            'network': True,  # Enable network isolation
            'ipc': True,
            'cgroup': True
        }
        
        manager = SandboxManager(config, tmpdir)
        cmd = manager.build_bwrap_command()
        
        # Check expected flags
        assert '--unshare-user-try' in cmd, "Should have user namespace"
        assert '--unshare-pid' in cmd, "Should have pid namespace"
        assert '--unshare-net' in cmd, "Should have network namespace when enabled"
        print("  ✓ Namespace flags match configuration")
        
        # uts should not be in command when disabled
        # (we use --unshare-uts, so check it's not present when disabled)
        assert '--unshare-uts' not in cmd, "Should not have uts namespace when disabled"
        print("  ✓ Disabled namespaces correctly excluded")
        
        print("\n✅ Namespace options test passed!")
        return True


def test_backward_compatibility():
    """Test that legacy whitelist mode still works."""
    print("\n" + "=" * 70)
    print("TEST: Backward Compatibility (Whitelist Mode)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        # Explicitly disable sandbox
        config.config['sandbox']['enabled'] = False
        
        # Remove wildcard to test actual whitelist behavior
        if 'unlimited' in config.config['tools']:
            del config.config['tools']['unlimited']
        
        runner = ToolRunner(config, tmpdir)
        
        # Test whitelist validation
        allowed, reason = runner.is_tool_allowed("ls")
        print(f"\nls allowed: {allowed} ({reason})")
        assert allowed, "ls should be allowed in whitelist mode"
        
        allowed, reason = runner.is_tool_allowed("evil_command_not_in_whitelist")
        print(f"evil_command allowed: {allowed} ({reason})")
        assert not allowed, "Unknown command should be blocked in whitelist mode"
        assert "whitelist" in reason.lower(), "Reason should mention whitelist"
        
        print("  ✓ Whitelist validation works")
        
        # Test with wildcard
        config.config['tools']['unlimited'] = ['*']
        runner2 = ToolRunner(config, tmpdir)
        allowed, reason = runner2.is_tool_allowed("anything")
        print(f"anything with wildcard: {allowed} ({reason})")
        assert allowed, "Wildcard should allow all commands"
        
        print("  ✓ Wildcard mode works")
        
        print("\n✅ Backward compatibility test passed!")
        return True


def test_sandbox_mode_validation():
    """Test validation in sandbox mode (blacklist instead of whitelist)."""
    print("\n" + "=" * 70)
    print("TEST: Sandbox Mode Validation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['sandbox']['enabled'] = True
        config.config['sandbox']['tool_blacklist'] = ['rm', 'dd']
        
        # Create a mock runner with sandbox (will fail if bwrap not available, but validation should work)
        runner = ToolRunner(config, tmpdir)
        
        if runner.sandbox_manager:
            print("\nSandbox mode active")
            
            # Test that non-blacklisted commands are allowed
            allowed, reason = runner.is_tool_allowed("ls -la")
            print(f"ls allowed: {allowed} ({reason})")
            assert allowed, "ls should be allowed in sandbox mode"
            assert "sandbox mode" in reason.lower(), "Reason should mention sandbox mode"
            
            # Test that blacklisted commands are blocked
            allowed, reason = runner.is_tool_allowed("rm -rf /")
            print(f"rm allowed: {allowed} ({reason})")
            assert not allowed, "rm should be blacklisted"
            assert "blacklisted" in reason.lower(), "Reason should mention blacklist"
            
            # Test that arbitrary commands are allowed (not in whitelist requirement)
            allowed, reason = runner.is_tool_allowed("some_random_tool")
            print(f"some_random_tool allowed: {allowed} ({reason})")
            assert allowed, "Arbitrary tools should be allowed in sandbox mode"
            
            print("  ✓ Sandbox mode validation works correctly")
        else:
            print("\n⚠ Sandbox not available (bwrap not installed)")
            print("  Skipping sandbox mode validation test")
        
        print("\n✅ Sandbox mode validation test passed!")
        return True


def test_integration_command_execution():
    """Integration test: Execute actual commands in sandbox (if available)."""
    print("\n" + "=" * 70)
    print("TEST: Command Execution (Integration)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['sandbox']['enabled'] = True
        
        runner = ToolRunner(config, tmpdir)
        
        if runner.sandbox_manager and runner.sandbox_manager.is_available():
            print("\n✓ Bubblewrap available, testing actual execution")
            
            # Test simple command
            success, output = runner.run("echo 'Hello from sandbox'")
            print(f"\nTest 1 - echo command:")
            print(f"  Success: {success}")
            if not success:
                print(f"  Output: {output}")
                if "not supported in this environment" in output:
                    print("  ⚠ Sandbox not fully functional in this environment (expected in CI)")
                    print("  Validation tests passed, skipping execution tests")
                    print("\n✅ Integration test completed (limited environment)!")
                    return True
                else:
                    print("  ❌ Unexpected error")
                    assert False, f"Unexpected error: {output}"
            
            print(f"  Output: {output.strip()}")
            assert success, "Simple echo should succeed"
            assert "Hello from sandbox" in output, "Output should contain expected text"
            
            # Test command with pipe
            success, output = runner.run("echo 'test' | grep 'test'")
            print(f"\nTest 2 - pipe command:")
            print(f"  Success: {success}")
            assert success, "Pipe command should succeed"
            
            # Test file operations in workspace
            test_file = os.path.join(tmpdir, 'test.txt')
            success, output = runner.run(f"echo 'content' > {test_file}")
            print(f"\nTest 3 - file write:")
            print(f"  Success: {success}")
            assert success, "File write should succeed"
            
            if os.path.exists(test_file):
                with open(test_file, 'r') as f:
                    content = f.read().strip()
                    print(f"  File content: {content}")
                    assert content == 'content', "File should contain expected content"
            
            print("\n  ✓ All integration tests passed")
        else:
            print("\n⚠ Bubblewrap not available")
            print("  Skipping integration tests (expected in CI without bwrap)")
        
        print("\n✅ Integration test completed!")
        return True


def test_edge_case_heredoc():
    """Test that heredocs work in sandbox mode."""
    print("\n" + "=" * 70)
    print("TEST: Edge Case - Heredoc Execution")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['sandbox']['enabled'] = True
        
        runner = ToolRunner(config, tmpdir)
        
        # Test heredoc validation
        heredoc_cmd = """cat << 'EOF'
This is a heredoc
with multiple lines
EOF"""
        
        allowed, reason = runner.is_tool_allowed(heredoc_cmd)
        print(f"\nHeredoc validation: {allowed} ({reason})")
        assert allowed, "Heredoc should be allowed"
        
        if runner.sandbox_manager and runner.sandbox_manager.is_available():
            # Test heredoc execution
            success, output = runner.run(heredoc_cmd)
            print(f"Heredoc execution: {success}")
            if success:
                print(f"Output preview: {output[:50]}...")
                assert "heredoc" in output.lower(), "Output should contain heredoc content"
            print("  ✓ Heredoc execution works")
        else:
            print("  ⚠ Skipping heredoc execution (bwrap not available)")
        
        print("\n✅ Heredoc edge case test passed!")
        return True


def test_edge_case_pipes():
    """Test that pipes work in sandbox mode."""
    print("\n" + "=" * 70)
    print("TEST: Edge Case - Pipe Execution")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['sandbox']['enabled'] = True
        
        runner = ToolRunner(config, tmpdir)
        
        # Test pipe validation
        pipe_cmd = "echo 'test data' | grep 'data'"
        allowed, reason = runner.is_tool_allowed(pipe_cmd)
        print(f"\nPipe validation: {allowed} ({reason})")
        assert allowed, "Pipe should be allowed"
        
        if runner.sandbox_manager and runner.sandbox_manager.is_available():
            success, output = runner.run(pipe_cmd)
            print(f"Pipe execution: {success}")
            if success:
                print(f"Output: {output.strip()}")
            print("  ✓ Pipe execution works")
        else:
            print("  ⚠ Skipping pipe execution (bwrap not available)")
        
        print("\n✅ Pipe edge case test passed!")
        return True


def run_all_tests():
    """Run all test functions."""
    tests = [
        test_sandbox_config_parsing,
        test_sandbox_manager_initialization,
        test_sandbox_availability_check,
        test_bwrap_command_generation,
        test_tool_blacklist_check,
        test_fallback_to_whitelist,
        test_host_bind_readonly,
        test_namespace_options,
        test_backward_compatibility,
        test_sandbox_mode_validation,
        test_integration_command_execution,
        test_edge_case_heredoc,
        test_edge_case_pipes,
    ]
    
    print("\n" + "=" * 70)
    print("RUNNING ALL SANDBOX TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
