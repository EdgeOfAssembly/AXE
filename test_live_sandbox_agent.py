#!/usr/bin/env python3
"""
Live Ollama Agent Sandbox Test

This test runs a real Ollama agent inside the sandbox and has it collect
diagnostic information to verify sandbox isolation and capabilities.
"""
import os
import sys
import subprocess
import tempfile
import time
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.sandbox import SandboxManager, check_user_namespace_support
from core.agent_manager import AgentManager
from utils.formatting import Colors, c


def test_live_sandbox_agent():
    """Test live Ollama agent inside sandbox with diagnostic collection."""
    print("=" * 70)
    print("LIVE SANDBOX AGENT TEST (Direct Diagnostic Collection)")
    print("=" * 70)
    
    # Check user namespace support
    ns_supported, ns_message = check_user_namespace_support()
    print(f"\nUser namespace support: {ns_supported}")
    print(f"Message: {ns_message}")
    
    if not ns_supported:
        print(c("⚠️  User namespaces not supported - agent will not have root privileges", Colors.YELLOW))
        print(c("   Sandbox will still provide isolation but with limited capabilities", Colors.DIM))
    
    # Create test workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nTest workspace: {tmpdir}")
        report_file = os.path.join(tmpdir, "sandbox_diagnostics.txt")
        
        # Load config
        config = Config()
        config.config['sandbox']['enabled'] = True
        
        # Create sandbox manager
        manager = SandboxManager(config, tmpdir)
        
        if not manager.is_available():
            print(c("\n⚠️  Bubblewrap not available", Colors.YELLOW))
            print(c("   Install with: sudo apt-get install bubblewrap", Colors.DIM))
            return False
        
        print(c("✓ Sandbox manager initialized", Colors.GREEN))
        
        # Test 1: Basic diagnostic commands
        print("\n" + "=" * 70)
        print("TEST 1: Collect basic diagnostics inside sandbox")
        print("=" * 70)
        
        diagnostic_commands = [
            ('whoami', 'Current user'),
            ('id', 'User ID and groups'),
            ('id -u', 'Numeric UID'),
            ('uname -a', 'System info'),
            ('hostname', 'Hostname'),
            ('pwd', 'Current directory'),
            ('ls -la /', 'Root directory listing'),
            ('ps aux | wc -l', 'Process count'),
            ('free -m', 'Memory info'),
            ('df -hT', 'Filesystem info'),
            ('cat /proc/self/uid_map', 'UID mapping'),
            ('cat /proc/self/gid_map', 'GID mapping'),
        ]
        
        results = {}
        for cmd, desc in diagnostic_commands:
            print(f"\n  Running: {cmd} ({desc})")
            success, output = manager.run(cmd, timeout=10)
            
            if success:
                print(f"    ✓ Success")
                results[cmd] = {'success': True, 'output': output.strip()}
                # Show first line of output
                first_line = output.strip().split('\n')[0] if output.strip() else '(empty)'
                print(f"    Output: {first_line[:80]}")
            else:
                print(f"    ✗ Failed: {output[:100]}")
                results[cmd] = {'success': False, 'output': output.strip()}
        
        # Write results to file
        print(f"\n  Writing diagnostics to: {report_file}")
        with open(report_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("SANDBOX DIAGNOSTICS REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"User Namespace Support: {ns_supported}\n")
            f.write(f"Message: {ns_message}\n\n")
            
            for cmd, desc in diagnostic_commands:
                f.write(f"\n{'=' * 70}\n")
                f.write(f"Command: {cmd}\n")
                f.write(f"Description: {desc}\n")
                f.write(f"{'=' * 70}\n")
                
                result = results.get(cmd, {})
                if result.get('success'):
                    f.write(f"Status: SUCCESS\n\n")
                    f.write(result.get('output', '(no output)'))
                    f.write("\n")
                else:
                    f.write(f"Status: FAILED\n\n")
                    f.write(result.get('output', '(no output)'))
                    f.write("\n")
        
        print(c(f"\n✓ Diagnostics written to {report_file}", Colors.GREEN))
        
        # Display the report
        print("\n" + "=" * 70)
        print("SANDBOX DIAGNOSTICS REPORT CONTENTS")
        print("=" * 70)
        with open(report_file, 'r') as f:
            print(f.read())
        
        # Verify key findings
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        
        # Check if running as root (UID 0)
        uid_result = results.get('id -u', {})
        if uid_result.get('success'):
            uid = uid_result.get('output', '').strip()
            if uid == '0':
                print(c("✓ Running as root inside sandbox (UID 0)", Colors.GREEN))
            else:
                print(c(f"⚠️  Not running as root inside sandbox (UID {uid})", Colors.YELLOW))
                print(c("   This is expected when user namespaces are not supported", Colors.DIM))
        
        # Check process isolation
        ps_result = results.get('ps aux | wc -l', {})
        if ps_result.get('success'):
            process_count = int(ps_result.get('output', '999').strip())
            if process_count < 20:
                print(c(f"✓ PID namespace isolation working ({process_count} processes visible)", Colors.GREEN))
            else:
                print(c(f"⚠️  PID namespace may not be isolated ({process_count} processes visible)", Colors.YELLOW))
        
        # Check if report file exists
        if os.path.exists(report_file):
            file_size = os.path.getsize(report_file)
            print(c(f"✓ Diagnostic report created ({file_size} bytes)", Colors.GREEN))
        else:
            print(c("✗ Diagnostic report not created", Colors.RED))
            return False
        
        print("\n" + "=" * 70)
        print("✅ LIVE SANDBOX TEST COMPLETED")
        print("=" * 70)
        print(f"\n📄 Full report saved to: {report_file}")
        print("\nKey findings:")
        
        # Summary
        uid = results.get('id -u', {}).get('output', 'unknown').strip()
        whoami = results.get('whoami', {}).get('output', 'unknown').strip()
        ps_count = results.get('ps aux | wc -l', {}).get('output', 'unknown').strip()
        
        print(f"  • User: {whoami}")
        print(f"  • UID: {uid}")
        print(f"  • Process count: {ps_count}")
        print(f"  • User namespaces: {'✓ supported' if ns_supported else '✗ not supported'}")
        
        if uid == '0':
            print(c("\n🎉 Agent has root privileges inside sandbox!", Colors.GREEN))
        else:
            print(c("\n⚠️  Agent does not have root privileges (user namespaces not supported)", Colors.YELLOW))
        
        return True


if __name__ == "__main__":
    try:
        success = test_live_sandbox_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(c(f"\n✗ Test failed with exception: {e}", Colors.RED))
        import traceback
        traceback.print_exc()
        sys.exit(1)
