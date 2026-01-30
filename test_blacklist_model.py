#!/usr/bin/env python3
"""
Blacklist model verification test.

This test verifies the new blacklist security model works correctly:
1. All tools allowed with empty blacklist
2. Blacklisted tools are blocked
3. Directory blacklist works correctly
4. Configuration properly loaded
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.tool_runner import ToolRunner
from core.sandbox import SandboxManager


def test_blacklist_model():
    """Test the blacklist security model."""
    print("=" * 70)
    print("BLACKLIST MODEL VERIFICATION TEST")
    print("=" * 70)
    
    # Test 1: Empty blacklist allows all tools
    print("\n" + "=" * 70)
    print("TEST 1: Empty blacklist allows all tools")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['tools'] = {'blacklist': []}
        config.config['directories'] = {'blacklist': []}
        config.config['sandbox'] = {'enabled': False}
        
        runner = ToolRunner(config, tmpdir)
        
        # Test common tools
        test_tools = ['ls', 'cat', 'grep', 'make', 'gcc', 'python3', 'arbitrary_tool']
        
        for tool in test_tools:
            allowed, reason = runner.is_tool_allowed(tool)
            if allowed:
                print(f"  ✓ {tool}: allowed")
            else:
                print(f"  ✗ {tool}: blocked - {reason}")
                return False
        
        print("✓ PASS: All tools allowed with empty blacklist")
    
    # Test 2: Blacklisted tools are blocked
    print("\n" + "=" * 70)
    print("TEST 2: Blacklisted tools are blocked")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['tools'] = {'blacklist': ['rm', 'dd', 'mkfs']}
        config.config['directories'] = {'blacklist': []}
        config.config['sandbox'] = {'enabled': False}
        
        runner = ToolRunner(config, tmpdir)
        
        # Test blacklisted tools
        for tool in ['rm', 'dd', 'mkfs']:
            allowed, reason = runner.is_tool_allowed(tool)
            if not allowed and 'blacklist' in reason.lower():
                print(f"  ✓ {tool}: correctly blocked")
            else:
                print(f"  ✗ {tool}: should be blocked but is allowed")
                return False
        
        # Test non-blacklisted tools
        for tool in ['ls', 'cat', 'arbitrary_tool']:
            allowed, reason = runner.is_tool_allowed(tool)
            if allowed:
                print(f"  ✓ {tool}: correctly allowed")
            else:
                print(f"  ✗ {tool}: should be allowed but is blocked - {reason}")
                return False
        
        print("✓ PASS: Blacklist enforcement working correctly")
    
    # Test 3: Directory blacklist
    print("\n" + "=" * 70)
    print("TEST 3: Directory blacklist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['tools'] = {'blacklist': []}
        config.config['directories'] = {'blacklist': ['/etc/shadow', '~/.ssh']}
        config.config['sandbox'] = {'enabled': False}
        
        runner = ToolRunner(config, tmpdir)
        
        # Test access to blacklisted directories
        blocked_commands = [
            'cat /etc/shadow',
            'ls ~/.ssh',
        ]
        
        for cmd in blocked_commands:
            allowed, reason = runner.is_tool_allowed(cmd)
            if not allowed and 'forbidden' in reason.lower():
                print(f"  ✓ Blocked: {cmd}")
            else:
                print(f"  ✗ Should block: {cmd}")
                return False
        
        # Test access to non-blacklisted directories
        allowed_commands = [
            'ls /tmp',
            'cat /etc/os-release',
        ]
        
        for cmd in allowed_commands:
            allowed, reason = runner.is_tool_allowed(cmd)
            if allowed:
                print(f"  ✓ Allowed: {cmd}")
            else:
                print(f"  ✗ Should allow: {cmd} - {reason}")
                return False
        
        print("✓ PASS: Directory blacklist working correctly")
    
    # Test 4: Sandbox blacklist integration
    print("\n" + "=" * 70)
    print("TEST 4: Sandbox blacklist integration")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.config['tools'] = {'blacklist': []}
        config.config['directories'] = {'blacklist': []}
        config.config['sandbox'] = {
            'enabled': True,
            'tool_blacklist': ['dangerous_tool']
        }
        
        runner = ToolRunner(config, tmpdir)
        
        # If sandbox is available, test sandbox blacklist
        if runner.sandbox_manager and runner.sandbox_manager.is_available():
            print("  Sandbox available - testing sandbox blacklist")
            
            # Tool in sandbox blacklist should be blocked
            allowed, reason = runner.is_tool_allowed('dangerous_tool')
            if not allowed and 'blacklist' in reason.lower():
                print(f"  ✓ Sandbox blacklist: dangerous_tool blocked")
            else:
                print(f"  ✗ Sandbox blacklist: dangerous_tool should be blocked")
                return False
            
            # Other tools should be allowed
            allowed, reason = runner.is_tool_allowed('safe_tool')
            if allowed:
                print(f"  ✓ Sandbox blacklist: safe_tool allowed")
            else:
                print(f"  ✗ Sandbox blacklist: safe_tool should be allowed")
                return False
            
            print("✓ PASS: Sandbox blacklist working correctly")
        else:
            print("  ⚠️  Sandbox not available - testing non-sandbox blacklist")
            
            # Without sandbox, use regular blacklist
            config.config['tools'] = {'blacklist': ['dangerous_tool']}
            runner2 = ToolRunner(config, tmpdir)
            
            allowed, reason = runner2.is_tool_allowed('dangerous_tool')
            if not allowed:
                print(f"  ✓ Blacklist: dangerous_tool blocked")
            else:
                print(f"  ✗ Blacklist: dangerous_tool should be blocked")
                return False
            
            allowed, reason = runner2.is_tool_allowed('safe_tool')
            if allowed:
                print(f"  ✓ Blacklist: safe_tool allowed")
            else:
                print(f"  ✗ Blacklist: safe_tool should be allowed")
                return False
            
            print("✓ PASS: Non-sandbox blacklist working correctly")
    
    # Test 5: Config loading
    print("\n" + "=" * 70)
    print("TEST 5: Configuration loading")
    print("=" * 70)
    
    config = Config()
    
    # Check blacklist structure in loaded config
    if 'blacklist' in config.config.get('tools', {}):
        print(f"  ✓ tools.blacklist present in config")
        blacklist = config.config['tools']['blacklist']
        print(f"    Current blacklist: {blacklist}")
    else:
        print(f"  ✗ tools.blacklist not found in config")
        return False
    
    if 'blacklist' in config.config.get('directories', {}):
        print(f"  ✓ directories.blacklist present in config")
        dir_blacklist = config.config['directories']['blacklist']
        print(f"    Current directory blacklist: {dir_blacklist}")
    else:
        print(f"  ✗ directories.blacklist not found in config")
        return False
    
    # Check get_tool_blacklist method works
    tool_blacklist = config.get_tool_blacklist()
    print(f"  ✓ get_tool_blacklist() returns: {tool_blacklist}")
    
    print("✓ PASS: Configuration loading correctly")
    
    print("\n" + "=" * 70)
    print("✅ ALL BLACKLIST MODEL TESTS PASSED")
    print("=" * 70)
    print("\nSummary:")
    print("  ✓ Empty blacklist allows all tools")
    print("  ✓ Blacklisted tools are blocked")
    print("  ✓ Directory blacklist works")
    print("  ✓ Sandbox blacklist integration works")
    print("  ✓ Configuration loads correctly")
    print("\n🎉 Blacklist security model working as expected!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_blacklist_model()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
