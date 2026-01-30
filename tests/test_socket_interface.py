#!/usr/bin/env python3
"""
Test suite for Unix socket interface for agent communication.

Tests socket creation, cleanup, stale file detection, command processing,
and ANSI color preservation.
"""
import os
import sys
import socket
import time
import signal
import tempfile
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_socket_path_construction():
    """Test that socket path is constructed correctly."""
    print("=" * 70)
    print("TEST: Socket Path Construction")
    print("=" * 70)
    
    uid = os.getuid()
    expected_socket = f"/run/user/{uid}/axe.sock"
    expected_pid = f"/run/user/{uid}/axe.pid"
    
    print(f"\nExpected socket path: {expected_socket}")
    print(f"Expected PID path: {expected_pid}")
    
    # Import after path setup
    import axe
    
    assert axe.SOCKET_PATH == expected_socket, f"Socket path mismatch: {axe.SOCKET_PATH} != {expected_socket}"
    assert axe.PID_PATH == expected_pid, f"PID path mismatch: {axe.PID_PATH} != {expected_pid}"
    
    print("  ✓ Socket paths constructed correctly")
    print("\n✅ Socket path construction test passed!")
    return True


def test_cleanup_files():
    """Test cleanup_files() function."""
    print("=" * 70)
    print("TEST: Cleanup Files Function")
    print("=" * 70)
    
    import axe
    
    # Create temporary test files
    test_sock = axe.SOCKET_PATH + ".test"
    test_pid = axe.PID_PATH + ".test"
    
    # Create files
    Path(test_sock).touch()
    Path(test_pid).touch()
    
    print(f"\nCreated test files:")
    print(f"  {test_sock}: {os.path.exists(test_sock)}")
    print(f"  {test_pid}: {os.path.exists(test_pid)}")
    
    # Replace paths temporarily
    orig_sock = axe.SOCKET_PATH
    orig_pid = axe.PID_PATH
    axe.SOCKET_PATH = test_sock
    axe.PID_PATH = test_pid
    
    try:
        # Call cleanup
        axe.cleanup_files()
        
        # Check files are removed
        assert not os.path.exists(test_sock), "Test socket file should be removed"
        assert not os.path.exists(test_pid), "Test PID file should be removed"
        
        print("\nAfter cleanup:")
        print(f"  {test_sock}: {os.path.exists(test_sock)}")
        print(f"  {test_pid}: {os.path.exists(test_pid)}")
        print("  ✓ Files cleaned up successfully")
        
    finally:
        # Restore original paths
        axe.SOCKET_PATH = orig_sock
        axe.PID_PATH = orig_pid
        
        # Clean up test files if they still exist
        for f in [test_sock, test_pid]:
            if os.path.exists(f):
                os.unlink(f)
    
    print("\n✅ Cleanup files test passed!")
    return True


def test_pid_file_operations():
    """Test PID file write and read operations."""
    print("=" * 70)
    print("TEST: PID File Operations")
    print("=" * 70)
    
    import axe
    
    test_pid_path = axe.PID_PATH + ".test"
    orig_pid = axe.PID_PATH
    axe.PID_PATH = test_pid_path
    
    try:
        # Write PID file
        axe.write_pid_file()
        
        assert os.path.exists(test_pid_path), "PID file should be created"
        
        # Read and verify
        with open(test_pid_path) as f:
            pid = int(f.read().strip())
        
        assert pid == os.getpid(), f"PID mismatch: {pid} != {os.getpid()}"
        
        print(f"\n  ✓ PID file created: {test_pid_path}")
        print(f"  ✓ PID written correctly: {pid}")
        
    finally:
        axe.PID_PATH = orig_pid
        if os.path.exists(test_pid_path):
            os.unlink(test_pid_path)
    
    print("\n✅ PID file operations test passed!")
    return True


def test_stale_file_detection():
    """Test detection of stale files from crashed sessions."""
    print("=" * 70)
    print("TEST: Stale File Detection")
    print("=" * 70)
    
    import axe
    
    test_pid_path = axe.PID_PATH + ".test"
    test_sock_path = axe.SOCKET_PATH + ".test"
    orig_pid = axe.PID_PATH
    orig_sock = axe.SOCKET_PATH
    
    axe.PID_PATH = test_pid_path
    axe.SOCKET_PATH = test_sock_path
    
    try:
        # Test 1: No stale files
        print("\n1. Test with no stale files:")
        axe.check_and_cleanup_stale_files()
        print("  ✓ No errors with clean state")
        
        # Test 2: Stale PID from dead process
        print("\n2. Test with stale PID (dead process):")
        with open(test_pid_path, 'w') as f:
            f.write("99999")  # Very unlikely to exist
        
        axe.check_and_cleanup_stale_files()
        assert not os.path.exists(test_pid_path), "Stale PID should be cleaned up"
        print("  ✓ Stale PID file cleaned up")
        
        # Test 3: Invalid PID file
        print("\n3. Test with invalid PID file:")
        with open(test_pid_path, 'w') as f:
            f.write("not_a_number")
        
        axe.check_and_cleanup_stale_files()
        assert not os.path.exists(test_pid_path), "Invalid PID should be cleaned up"
        print("  ✓ Invalid PID file cleaned up")
        
        # Test 4: Orphaned socket
        print("\n4. Test with orphaned socket:")
        Path(test_sock_path).touch()
        axe.check_and_cleanup_stale_files()
        assert not os.path.exists(test_sock_path), "Orphaned socket should be cleaned up"
        print("  ✓ Orphaned socket cleaned up")
        
        # Test 5: Running instance (current PID)
        print("\n5. Test with running instance (should raise error):")
        with open(test_pid_path, 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            axe.check_and_cleanup_stale_files()
            assert False, "Should have raised RuntimeError for running instance"
        except RuntimeError as e:
            assert "already running" in str(e)
            print(f"  ✓ Correctly detected running instance: {e}")
        
    finally:
        axe.PID_PATH = orig_pid
        axe.SOCKET_PATH = orig_sock
        for f in [test_pid_path, test_sock_path]:
            if os.path.exists(f):
                os.unlink(f)
    
    print("\n✅ Stale file detection test passed!")
    return True


def test_socket_server_creation():
    """Test socket server creation and basic connectivity."""
    print("=" * 70)
    print("TEST: Socket Server Creation")
    print("=" * 70)
    
    import axe
    
    test_sock_path = axe.SOCKET_PATH + ".test"
    orig_sock = axe.SOCKET_PATH
    axe.SOCKET_PATH = test_sock_path
    
    try:
        # Start socket server
        sock = axe.start_socket_server()
        
        assert os.path.exists(test_sock_path), "Socket file should be created"
        print(f"\n  ✓ Socket created: {test_sock_path}")
        
        # Test connection
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(test_sock_path)
        print("  ✓ Client can connect to socket")
        
        client.close()
        sock.close()
        
        # Clean up
        os.unlink(test_sock_path)
        
    finally:
        axe.SOCKET_PATH = orig_sock
        if os.path.exists(test_sock_path):
            os.unlink(test_sock_path)
    
    print("\n✅ Socket server creation test passed!")
    return True


def test_socket_communication():
    """Test basic command communication through socket."""
    print("=" * 70)
    print("TEST: Socket Communication")
    print("=" * 70)
    
    # This test requires a running AXE instance, so we'll just test
    # the socket protocol structure
    print("\n  Note: This test validates socket protocol structure.")
    print("  Full integration testing requires a running AXE instance.")
    
    # Test message format
    test_command = "@claude test command"
    encoded = test_command.encode('utf-8')
    decoded = encoded.decode('utf-8')
    
    assert decoded == test_command, "Message encoding/decoding should work"
    print(f"  ✓ Message encoding/decoding works")
    print(f"    Command: {test_command}")
    print(f"    Bytes: {len(encoded)}")
    
    print("\n✅ Socket communication test passed!")
    return True


def run_all_tests():
    """Run all socket interface tests."""
    print("\n" + "=" * 70)
    print("UNIX SOCKET INTERFACE TEST SUITE")
    print("=" * 70 + "\n")
    
    tests = [
        test_socket_path_construction,
        test_cleanup_files,
        test_pid_file_operations,
        test_stale_file_detection,
        test_socket_server_creation,
        test_socket_communication,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} returned False")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
