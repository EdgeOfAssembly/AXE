#!/usr/bin/env python3
"""
SUID Shell Workaround Exploration

This test explores using a SUID shell as a workaround for environments
without user namespace support. The idea is to copy a shell binary,
set SUID bit, and use it inside sandbox to gain root-like privileges.

WARNING: This is experimental and for testing only.
"""
import os
import sys
import shutil
import stat
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.sandbox import SandboxManager, check_user_namespace_support
from utils.formatting import Colors, c


def test_suid_shell_workaround():
    """Test SUID shell workaround for gaining privileges in sandbox."""
    print("=" * 70)
    print("SUID SHELL WORKAROUND EXPLORATION")
    print("=" * 70)
    
    # Check user namespace support
    ns_supported, ns_message = check_user_namespace_support()
    print(f"\nUser namespace support: {ns_supported}")
    print(f"Message: {ns_message}\n")
    
    if ns_supported:
        print(c("ℹ️  User namespaces ARE supported in this environment", Colors.CYAN))
        print(c("   SUID workaround may not be necessary, but testing anyway...", Colors.DIM))
    else:
        print(c("⚠️  User namespaces NOT supported - SUID workaround could help", Colors.YELLOW))
    
    # Create test workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nTest workspace: {tmpdir}")
        
        # Step 1: Copy shell to workspace
        print("\n" + "=" * 70)
        print("STEP 1: Copy shell binary to workspace")
        print("=" * 70)
        
        # Try to find a shell
        shell_candidates = ['/bin/sh', '/bin/bash', '/bin/dash']
        shell_path = None
        
        for candidate in shell_candidates:
            if os.path.exists(candidate):
                shell_path = candidate
                print(f"  Found shell: {shell_path}")
                break
        
        if not shell_path:
            print(c("✗ No shell found", Colors.RED))
            return False
        
        # Copy shell to workspace
        suid_shell = os.path.join(tmpdir, 'suid_shell')
        try:
            shutil.copy2(shell_path, suid_shell)
            print(f"  ✓ Copied {shell_path} → {suid_shell}")
        except Exception as e:
            print(c(f"✗ Failed to copy shell: {e}", Colors.RED))
            return False
        
        # Step 2: Try to set SUID bit
        print("\n" + "=" * 70)
        print("STEP 2: Attempt to set SUID bit")
        print("=" * 70)
        
        try:
            # Get current permissions
            current_mode = os.stat(suid_shell).st_mode
            print(f"  Current mode: {oct(stat.S_IMODE(current_mode))}")
            
            # Try to set SUID bit (requires root or CAP_SETUID)
            new_mode = current_mode | stat.S_ISUID | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(suid_shell, new_mode)
            
            # Verify SUID bit was set
            final_mode = os.stat(suid_shell).st_mode
            is_suid = bool(final_mode & stat.S_ISUID)
            
            print(f"  New mode: {oct(stat.S_IMODE(final_mode))}")
            print(f"  SUID bit set: {is_suid}")
            
            if is_suid:
                print(c("  ✓ SUID bit successfully set!", Colors.GREEN))
            else:
                print(c("  ⚠️  SUID bit NOT set (probably need root privileges)", Colors.YELLOW))
                print(c("     This is expected in unprivileged environments", Colors.DIM))
                
        except Exception as e:
            print(c(f"  ✗ Failed to set SUID: {e}", Colors.RED))
            print(c("     This is expected in unprivileged environments", Colors.DIM))
        
        # Step 3: Test the SUID shell outside sandbox
        print("\n" + "=" * 70)
        print("STEP 3: Test SUID shell outside sandbox")
        print("=" * 70)
        
        try:
            # Test if SUID shell gives us elevated privileges
            result = subprocess.run(
                [suid_shell, '-c', 'id'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"  ✓ SUID shell works outside sandbox")
                print(f"  Output: {result.stdout.strip()}")
                
                # Check if we got root UID
                if 'uid=0' in result.stdout:
                    print(c("  🎉 SUID shell grants root privileges!", Colors.GREEN))
                else:
                    print(c("  ⚠️  SUID shell works but no root privileges", Colors.YELLOW))
            else:
                print(c(f"  ✗ SUID shell failed: {result.stderr}", Colors.RED))
                
        except Exception as e:
            print(c(f"  ✗ Error testing SUID shell: {e}", Colors.RED))
        
        # Step 4: Test inside sandbox (if available)
        print("\n" + "=" * 70)
        print("STEP 4: Test SUID shell inside sandbox")
        print("=" * 70)
        
        config = Config()
        config.config['sandbox']['enabled'] = True
        manager = SandboxManager(config, tmpdir)
        
        if not manager.is_available():
            print(c("  ⚠️  Sandbox not available - skipping sandbox test", Colors.YELLOW))
        else:
            print("  ✓ Sandbox available")
            
            # Test 1: Regular whoami
            print("\n  Test 1: Regular 'whoami' command")
            success, output = manager.run('whoami', timeout=10)
            if success:
                print(f"    Result: {output.strip()}")
            else:
                print(f"    Failed: {output[:100]}")
            
            # Test 2: whoami via SUID shell
            print("\n  Test 2: 'whoami' via SUID shell")
            suid_cmd = f'{suid_shell} -c whoami'
            success, output = manager.run(suid_cmd, timeout=10)
            if success:
                print(f"    Result: {output.strip()}")
                if output.strip() == 'root':
                    print(c("    🎉 SUID shell provides root inside sandbox!", Colors.GREEN))
                else:
                    print(c("    ⚠️  SUID shell works but not as root", Colors.YELLOW))
            else:
                print(f"    Failed: {output[:100]}")
            
            # Test 3: Full id command via SUID shell
            print("\n  Test 3: 'id' command via SUID shell")
            suid_cmd = f'{suid_shell} -c id'
            success, output = manager.run(suid_cmd, timeout=10)
            if success:
                print(f"    Result: {output.strip()}")
                if 'uid=0' in output:
                    print(c("    ✓ Confirmed: UID 0 (root) via SUID shell", Colors.GREEN))
            else:
                print(f"    Failed: {output[:100]}")
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
The SUID workaround approach:

1. **Pros**: Could provide root privileges without user namespaces
2. **Cons**: 
   - Requires root to set SUID bit in the first place
   - Security risk if not properly contained
   - May not work in all sandbox configurations
   - Modern systems often ignore SUID in certain contexts

3. **Recommendation**: 
   - User namespaces are the proper solution
   - SUID workaround is a hack for legacy systems
   - Better to document the limitation than rely on SUID

4. **Current Status**:
   - In unprivileged environments (CI, containers), can't set SUID bit
   - In privileged environments, user namespaces usually work anyway
   - Workaround has limited practical applicability
""")
    
    return True


if __name__ == "__main__":
    try:
        test_suid_shell_workaround()
        sys.exit(0)
    except Exception as e:
        print(c(f"\n✗ Test failed: {e}", Colors.RED))
        import traceback
        traceback.print_exc()
        sys.exit(1)
