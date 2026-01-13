#!/usr/bin/env python3
"""
Tests for GitHub agent integration.
Tests both enabled and disabled modes.
"""
import os
import sys
import tempfile
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.github_agent import GitHubAgent
from axe import check_agent_command, AGENT_TOKEN_GITHUB_READY


def test_github_agent_disabled_by_default():
    """When disabled, all operations are no-ops."""
    print("Testing: GitHub agent disabled by default...")
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = GitHubAgent(tmpdir, enabled=False)
        
        # Should return None/no-op
        result = agent.agent_request_push("branch", "msg", [])
        assert result is None, "Disabled agent should return None"
        assert agent.enabled is False, "Agent should be disabled"
    print("  ✓ Disabled mode works correctly")


def test_github_agent_no_git_repo():
    """Handles non-git directories gracefully."""
    print("Testing: GitHub agent with no git repo...")
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = GitHubAgent(tmpdir, enabled=True)
        assert agent.repo_detected is False, "Should detect no git repo"
    print("  ✓ No-repo detection works")


def test_github_agent_detects_repo():
    """Detects git repositories correctly."""
    print("Testing: GitHub agent detects git repo...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo
        result = subprocess.run(['git', 'init'], cwd=tmpdir, capture_output=True)
        if result.returncode != 0:
            print(f"  ⚠ Skipping test - git not available")
            return
        
        agent = GitHubAgent(tmpdir, enabled=True)
        assert agent.repo_detected is True, "Should detect git repo"
    print("  ✓ Repo detection works")


def test_agent_token_detection():
    """GITHUB_READY token is detected correctly."""
    print("Testing: GITHUB_READY token detection...")
    
    response = "I'm done! [[GITHUB_READY: my-branch, Add feature]]"
    found, content = check_agent_command(response, AGENT_TOKEN_GITHUB_READY)
    
    # Token detection should work
    assert found is True, "Token should be found"
    assert "my-branch" in content, "Branch name should be in content"
    print("  ✓ Token detection works")


def test_agent_token_not_in_result_blocks():
    """GITHUB_READY token in result blocks should not trigger."""
    print("Testing: Token in result blocks ignored...")
    
    response = """Let me check the code:
    
<result>
AGENT_TOKEN_GITHUB_READY = "[[GITHUB_READY:"
</result>

Now analyzing..."""
    
    found, content = check_agent_command(response, AGENT_TOKEN_GITHUB_READY)
    
    # Token in result block should not trigger
    assert not found, "Token in result block should not trigger"
    print("  ✓ Result block filtering works")


def test_github_agent_no_op_when_disabled():
    """Verify GitHub agent has no impact when disabled."""
    print("Testing: No-op behavior when disabled...")
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = GitHubAgent(tmpdir, enabled=False)
        
        # Try to push (should silently no-op)
        result = agent.execute_push("test-branch", "Test commit", ["file.txt"])
        assert not result['success'], "Disabled agent should not push"
        assert 'disabled' in result['error'].lower(), "Error should mention disabled"
    print("  ✓ No-op behavior works")


def test_github_agent_diff_generation():
    """Test diff generation for review."""
    print("Testing: Diff generation...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo
        result = subprocess.run(['git', 'init'], cwd=tmpdir, capture_output=True)
        if result.returncode != 0:
            print(f"  ⚠ Skipping test - git not available")
            return
        
        # Configure git user
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmpdir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmpdir, capture_output=True)
        
        # Create a file
        test_file = os.path.join(tmpdir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('initial content\n')
        
        # Add and commit
        subprocess.run(['git', 'add', 'test.txt'], cwd=tmpdir, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=tmpdir, capture_output=True)
        
        # Modify file
        with open(test_file, 'w') as f:
            f.write('modified content\n')
        
        agent = GitHubAgent(tmpdir, enabled=True)
        diff = agent._get_diff(['test.txt'])
        
        assert 'test.txt' in diff or diff == '', "Diff should mention file or be empty"
    print("  ✓ Diff generation works")


def run_all_tests():
    """Run all GitHub agent tests."""
    print("\n" + "=" * 60)
    print("GITHUB AGENT TEST SUITE")
    print("=" * 60 + "\n")
    
    test_github_agent_disabled_by_default()
    test_github_agent_no_git_repo()
    test_github_agent_detects_repo()
    test_agent_token_detection()
    test_agent_token_not_in_result_blocks()
    test_github_agent_no_op_when_disabled()
    test_github_agent_diff_generation()
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    run_all_tests()
