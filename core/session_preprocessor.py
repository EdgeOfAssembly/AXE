"""
Session Preprocessor for AXE

Orchestrates workspace preprocessing at the start of each AXE session.

Workflow:
1. Check if preprocessing is enabled in config
2. If environment_probe enabled: generate .collab_env.md with system info (zero agent tokens)
3. If minifier enabled: minify supported source files (keeping comments)
4. If llmprep enabled: run llmprep to generate LLM context files
5. Report statistics to user

Author: EdgeOfAssembly
License: GPLv3 / Commercial
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionPreprocessor:
    """
    Orchestrates workspace preprocessing at the start of each AXE session.
    
    Handles environment probing, minification, and llmprep execution based on configuration.
    """
    
    def __init__(self, config, workspace_path: str):
        """
        Initialize the session preprocessor.
        
        Args:
            config: AXE Config object
            workspace_path: Path to the workspace directory
        """
        self.config = config
        self.workspace_path = os.path.abspath(workspace_path)
        
        # Get preprocessing configuration
        self.preprocessing_config = config.get('preprocessing', default={})
        self.environment_probe_config = self.preprocessing_config.get('environment_probe', {})
        self.minifier_config = self.preprocessing_config.get('minifier', {})
        self.llmprep_config = self.preprocessing_config.get('llmprep', {})
    
    def is_enabled(self) -> bool:
        """
        Check if any preprocessing is enabled.
        
        Returns:
            True if environment_probe, minifier, or llmprep is enabled
        """
        environment_probe_enabled = self.environment_probe_config.get('enabled', True)
        minifier_enabled = self.minifier_config.get('enabled', False)
        llmprep_enabled = self.llmprep_config.get('enabled', False)
        return environment_probe_enabled or minifier_enabled or llmprep_enabled
    
    def run(self) -> Dict[str, Any]:
        """
        Run all enabled preprocessing steps.
        
        Returns:
            Dictionary with results:
            {
                'environment_probe': {'success': bool, 'output_file': str, 'enabled': bool},
                'minifier': {'files_processed': int, 'bytes_saved': int, 'enabled': bool},
                'llmprep': {'success': bool, 'output_dir': str, 'enabled': bool}
            }
        """
        results = {
            'environment_probe': {'enabled': False, 'success': False, 'output_file': None},
            'minifier': {'enabled': False, 'files_processed': 0, 'bytes_saved': 0},
            'llmprep': {'enabled': False, 'success': False, 'output_dir': None}
        }
        
        # Run environment probe if enabled (enabled by default)
        if self.environment_probe_config.get('enabled', True):
            logger.info("Running environment probe...")
            environment_probe_results = self.run_environment_probe()
            results['environment_probe'] = environment_probe_results
            results['environment_probe']['enabled'] = True
        
        # Run minifier if enabled
        if self.minifier_config.get('enabled', False):
            logger.info("Running minifier preprocessing...")
            minifier_results = self.run_minifier()
            results['minifier'] = minifier_results
            results['minifier']['enabled'] = True
        
        # Run llmprep if enabled
        if self.llmprep_config.get('enabled', False):
            logger.info("Running llmprep preprocessing...")
            llmprep_results = self.run_llmprep()
            results['llmprep'] = llmprep_results
            results['llmprep']['enabled'] = True
        
        return results
    
    def run_environment_probe(self) -> Dict[str, Any]:
        """
        Run environment probe to generate .collab_env.md
        
        Returns:
            Dictionary with keys:
            - success: True if probe succeeded
            - output_file: Path to output file
            - error: Error message if failed (optional)
        """
        try:
            # Import here to avoid circular dependencies
            from core.environment_probe import EnvironmentProbe
            
            # Create probe
            probe = EnvironmentProbe(self.workspace_path, self.environment_probe_config)
            
            # Run probe
            output_file = probe.run()
            
            if output_file:
                return {
                    'success': True,
                    'output_file': output_file
                }
            else:
                return {
                    'success': False,
                    'output_file': None,
                    'error': 'Probe disabled or failed'
                }
        
        except Exception as e:
            logger.error(f"Environment probe failed: {e}")
            return {
                'success': False,
                'output_file': None,
                'error': str(e)
            }
    
    def run_minifier(self) -> Dict[str, int]:
        """
        Run minification on workspace.
        
        Returns:
            Dictionary with keys:
            - files_processed: Number of files minified
            - bytes_saved: Bytes saved by minification
            - success: True if minification succeeded
        """
        try:
            # Import here to avoid circular dependencies
            from tools.minifier import Minifier
            
            # Get configuration
            keep_comments = self.minifier_config.get('keep_comments', True)
            exclude_dirs = set(self.minifier_config.get('exclude_dirs', []))
            output_mode = self.minifier_config.get('output_mode', 'in_place')
            output_dir = self.minifier_config.get('output_dir', '.minified')
            
            # Create minifier
            minifier = Minifier(exclude_dirs=exclude_dirs)
            
            # Minify workspace
            stats = minifier.minify_workspace(
                self.workspace_path,
                keep_comments=keep_comments,
                output_mode=output_mode,
                output_dir=output_dir if output_mode == 'separate_dir' else None
            )
            
            return {
                'files_processed': stats['files_processed'],
                'bytes_saved': stats['bytes_saved'],
                'bytes_original': stats['bytes_original'],
                'bytes_minified': stats['bytes_minified'],
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Minifier preprocessing failed: {e}")
            return {
                'files_processed': 0,
                'bytes_saved': 0,
                'bytes_original': 0,
                'bytes_minified': 0,
                'success': False,
                'error': str(e)
            }
    
    def run_llmprep(self) -> Dict[str, Any]:
        """
        Run llmprep to generate context files.
        
        Returns:
            Dictionary with keys:
            - success: True if llmprep succeeded
            - output_dir: Path to output directory
            - error: Error message if failed (optional)
        """
        try:
            # Get configuration
            output_dir = self.llmprep_config.get('output_dir', 'llm_prep')
            depth = self.llmprep_config.get('depth', 4)
            skip_doxygen = self.llmprep_config.get('skip_doxygen', False)
            skip_pyreverse = self.llmprep_config.get('skip_pyreverse', False)
            skip_ctags = self.llmprep_config.get('skip_ctags', False)
            
            # Build llmprep command
            tools_dir = Path(__file__).parent.parent / 'tools'
            llmprep_script = tools_dir / 'llmprep.py'
            
            if not llmprep_script.exists():
                raise FileNotFoundError(f"llmprep.py not found at {llmprep_script}")
            
            cmd = [
                sys.executable,
                str(llmprep_script),
                self.workspace_path,
                '-o', output_dir,
                '-d', str(depth)
            ]
            
            if skip_doxygen:
                cmd.append('--skip-doxygen')
            if skip_pyreverse:
                cmd.append('--skip-pyreverse')
            if skip_ctags:
                cmd.append('--skip-ctags')
            
            # Run llmprep
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output_dir': output_dir
                }
            else:
                logger.warning(f"llmprep exited with code {result.returncode}: {result.stderr}")
                return {
                    'success': False,
                    'output_dir': output_dir,
                    'error': result.stderr
                }
        
        except subprocess.TimeoutExpired:
            logger.error("llmprep timed out")
            return {
                'success': False,
                'output_dir': None,
                'error': "Timeout (5 minutes)"
            }
        except Exception as e:
            logger.error(f"llmprep preprocessing failed: {e}")
            return {
                'success': False,
                'output_dir': None,
                'error': str(e)
            }


def create_session_preprocessor(config, workspace_path: str) -> SessionPreprocessor:
    """
    Factory function to create a SessionPreprocessor.
    
    Args:
        config: AXE Config object
        workspace_path: Path to workspace directory
        
    Returns:
        SessionPreprocessor instance
    """
    return SessionPreprocessor(config, workspace_path)
