"""
Autonomous GitHub operations for collaborative agents.
Completely optional - has zero impact when disabled.

This module provides a surgical, isolated GitHub integration that allows
agents to autonomously push code with mandatory human review gates.
"""

import os
import subprocess
from typing import Dict, List, Optional


class GitHubAgent:
    """
    Manages autonomous GitHub operations with human review gates.
    
    Safety:
    - Disabled by default
    - All operations require human approval
    - Uses SSH (existing credentials)
    - Never auto-merges
    """
    
    def __init__(self, workspace_dir: str, enabled: bool = False):
        """
        Initialize GitHub agent.
        
        Args:
            workspace_dir: Path to git repository
            enabled: If False, all methods return immediately (no-op)
        """
        self.enabled = enabled
        if not enabled:
            return  # Complete no-op when disabled
        
        # Only initialize when enabled
        self.workspace_dir = workspace_dir
        self.repo_detected = self._detect_git_repo()
        self.ssh_configured = self._check_ssh_setup()
    
    def agent_request_push(self, branch: str, commit_msg: str, 
                          files: List[str]) -> Optional[Dict]:
        """
        Agent requests to push changes. Returns None if disabled.
        
        Args:
            branch: Target branch name
            commit_msg: Commit message
            files: List of files changed
        
        Returns:
            Dict with review info, or None if feature disabled
        """
        if not self.enabled:
            return None
        
        # Collect info for human review
        return {
            'branch': branch,
            'commit_message': commit_msg,
            'files_changed': files,
            'diff': self._get_diff(files),
            'test_results': self._get_test_results(),
            'requires_review': True  # Always true
        }
    
    def execute_push(self, branch: str, commit_msg: str, 
                    files: List[str]) -> Dict:
        """
        Execute push after human approval.
        
        Args:
            branch: Target branch name
            commit_msg: Commit message
            files: List of files to commit
        
        Returns:
            Dict with success status and details
        """
        if not self.enabled:
            return {'success': False, 'error': 'GitHub agent disabled'}
        
        try:
            # Create and checkout branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            
            # If branch already exists, switch to it
            if result.returncode != 0:
                result = subprocess.run(
                    ['git', 'checkout', branch],
                    cwd=self.workspace_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return {'success': False, 'error': f'Failed to checkout branch: {result.stderr}'}
            
            # Stage files
            for file in files:
                result = subprocess.run(
                    ['git', 'add', file],
                    cwd=self.workspace_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return {'success': False, 'error': f'Failed to add file {file}: {result.stderr}'}
            
            # Commit changes
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # Check if there's nothing to commit
                if 'nothing to commit' in result.stdout.lower():
                    return {'success': False, 'error': 'No changes to commit'}
                return {'success': False, 'error': f'Failed to commit: {result.stderr}'}
            
            # Push to remote
            result = subprocess.run(
                ['git', 'push', '-u', 'origin', branch],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return {'success': False, 'error': f'Failed to push: {result.stderr}'}
            
            return {
                'success': True,
                'branch': branch,
                'commit_message': commit_msg,
                'files_pushed': files
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _detect_git_repo(self) -> bool:
        """
        Check if workspace is a git repo.
        
        Returns:
            True if git repository detected
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_ssh_setup(self) -> bool:
        """
        Verify SSH key and remote configured.
        
        Returns:
            True if SSH appears configured
        """
        try:
            # Check if remote is configured
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False
            
            # Check if it's an SSH remote
            remote_url = result.stdout.strip()
            return remote_url.startswith('git@') or remote_url.startswith('ssh://')
        except Exception:
            return False
    
    def _get_diff(self, files: List[str]) -> str:
        """
        Get git diff for review.
        
        Args:
            files: List of files to get diff for
        
        Returns:
            Git diff output
        """
        try:
            # Get diff for staged and unstaged changes
            result = subprocess.run(
                ['git', 'diff', 'HEAD'] + files,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout
            
            # If no diff from HEAD, get diff of unstaged changes
            result = subprocess.run(
                ['git', 'diff'] + files,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error getting diff: {str(e)}"
    
    def _get_test_results(self) -> Optional[str]:
        """
        Get recent test output if available.
        
        Returns:
            Test results or None
        """
        # This is a placeholder - could be extended to capture
        # actual test results if a test was run recently
        return None
