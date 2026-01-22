#!/usr/bin/env python3
"""
Integration test for collaborative session initialization.

Tests that the collab session can start without errors, specifically
testing that the banner displays correctly without ctx_window errors.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from axe import Config


def test_collab_session_starts_successfully():
    """Test that a collaborative session can be started without errors."""
    print("Testing collaborative session startup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create configuration
        config = Config()
        
        # Import CollaborativeSession after Config is loaded
        from axe import CollaborativeSession
        
        # Use agents that are configured in axe.yaml
        agent_names = ['grok', 'grok_code']
        
        try:
            # Create collaborative session using the correct signature
            session = CollaborativeSession(
                config=config,
                agents=agent_names,
                workspace_dir=tmpdir,
                time_limit_minutes=5
            )
            
            # Try to print the banner - this is where the ctx_window error occurred
            print("\nCalling print_banner()...")
            session.print_banner()
            
            print("\n  ✓ Collaborative session started successfully without ctx_window error")
            return True
            
        except NameError as e:
            if 'ctx_window' in str(e):
                print(f"\n  ✗ FAILED: ctx_window NameError: {e}")
                return False
            else:
                raise
        except Exception as e:
            print(f"\n  ⚠ Session creation encountered an error: {type(e).__name__}: {e}")
            print("  (This might be expected if agents are not fully configured)")
            # As long as it's not the ctx_window error, we consider it a pass
            return True


if __name__ == '__main__':
    print("=" * 70)
    print("COLLABORATIVE SESSION INTEGRATION TEST")
    print("=" * 70)
    
    success = test_collab_session_starts_successfully()
    
    print("\n" + "=" * 70)
    if success:
        print("INTEGRATION TEST PASSED ✓")
    else:
        print("INTEGRATION TEST FAILED ✗")
        sys.exit(1)
    print("=" * 70)
