#!/usr/bin/env python3
"""
Test suite for Session Preprocessor.

Tests preprocessing workflow including minifier and llmprep integration.
"""

import sys
import os
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.session_preprocessor import SessionPreprocessor, create_session_preprocessor
from core.config import Config


class TestSessionPreprocessorInit(unittest.TestCase):
    """Test SessionPreprocessor initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test basic initialization."""
        config = Mock()
        config.get.return_value = {}
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        
        self.assertEqual(os.path.abspath(self.test_dir), preprocessor.workspace_path)
        self.assertIsNotNone(preprocessor.config)
    
    def test_is_enabled_both_disabled(self):
        """Test is_enabled when both minifier and llmprep are disabled."""
        config = Mock()
        config.get.return_value = {
            'environment_probe': {'enabled': False},
            'minifier': {'enabled': False},
            'llmprep': {'enabled': False}
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        self.assertFalse(preprocessor.is_enabled())
    
    def test_is_enabled_minifier_only(self):
        """Test is_enabled when only minifier is enabled."""
        config = Mock()
        config.get.return_value = {
            'minifier': {'enabled': True},
            'llmprep': {'enabled': False}
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        self.assertTrue(preprocessor.is_enabled())
    
    def test_is_enabled_llmprep_only(self):
        """Test is_enabled when only llmprep is enabled."""
        config = Mock()
        config.get.return_value = {
            'minifier': {'enabled': False},
            'llmprep': {'enabled': True}
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        self.assertTrue(preprocessor.is_enabled())
    
    def test_is_enabled_both_enabled(self):
        """Test is_enabled when both are enabled."""
        config = Mock()
        config.get.return_value = {
            'minifier': {'enabled': True},
            'llmprep': {'enabled': True}
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        self.assertTrue(preprocessor.is_enabled())


class TestMinifierPreprocessing(unittest.TestCase):
    """Test minifier preprocessing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test file
        self.test_file = os.path.join(self.test_dir, 'test.c')
        with open(self.test_file, 'w') as f:
            f.write('// Comment\nint main() {\n    return 0;\n}')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_run_minifier_success(self):
        """Test successful minifier execution."""
        config = Mock()
        config.get.return_value = {
            'minifier': {
                'enabled': True,
                'keep_comments': False,
                'exclude_dirs': ['tests'],
                'output_mode': 'in_place'
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        
        result = preprocessor.run_minifier()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['files_processed'], 1)
        self.assertGreater(result['bytes_saved'], 0)
    
    def test_run_minifier_with_comments(self):
        """Test minifier with comment preservation."""
        config = Mock()
        config.get.return_value = {
            'minifier': {
                'enabled': True,
                'keep_comments': True,
                'exclude_dirs': [],
                'output_mode': 'in_place'
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        
        result = preprocessor.run_minifier()
        
        self.assertTrue(result['success'])
        # With comments kept, savings might be minimal
        self.assertGreaterEqual(result['bytes_saved'], 0)
    
    def test_run_minifier_separate_dir(self):
        """Test minifier with separate output directory."""
        config = Mock()
        config.get.return_value = {
            'minifier': {
                'enabled': True,
                'keep_comments': False,
                'exclude_dirs': [],
                'output_mode': 'separate_dir',
                'output_dir': 'minified'
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        
        result = preprocessor.run_minifier()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['files_processed'], 1)
        
        # Original file should be unchanged
        with open(self.test_file, 'r') as f:
            content = f.read()
            self.assertIn('//', content)
    
    def test_run_minifier_error_handling(self):
        """Test minifier error handling."""
        config = Mock()
        config.get.return_value = {
            'minifier': {
                'enabled': True,
                'keep_comments': False,
                'exclude_dirs': [],
                'output_mode': 'invalid_mode'  # Invalid mode
            }
        }
        
        preprocessor = SessionPreprocessor(config, '/nonexistent/path')
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        
        result = preprocessor.run_minifier()
        
        # Should handle error gracefully
        self.assertIn('success', result)
        if not result['success']:
            self.assertIn('error', result)


class TestLlmprepPreprocessing(unittest.TestCase):
    """Test llmprep preprocessing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_run_llmprep_success(self, mock_run):
        """Test successful llmprep execution."""
        mock_run.return_value = Mock(returncode=0, stderr='', stdout='')
        
        config = Mock()
        config.get.return_value = {
            'llmprep': {
                'enabled': True,
                'output_dir': 'llm_prep',
                'depth': 4,
                'skip_doxygen': False,
                'skip_pyreverse': False,
                'skip_ctags': False
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        result = preprocessor.run_llmprep()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['output_dir'], 'llm_prep')
        
        # Verify subprocess.run was called
        self.assertTrue(mock_run.called)
    
    @patch('subprocess.run')
    def test_run_llmprep_with_skip_options(self, mock_run):
        """Test llmprep with skip options."""
        mock_run.return_value = Mock(returncode=0, stderr='', stdout='')
        
        config = Mock()
        config.get.return_value = {
            'llmprep': {
                'enabled': True,
                'output_dir': 'llm_prep',
                'depth': 4,
                'skip_doxygen': True,
                'skip_pyreverse': True,
                'skip_ctags': True
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        result = preprocessor.run_llmprep()
        
        self.assertTrue(result['success'])
        
        # Verify skip flags were included in command
        call_args = mock_run.call_args[0][0]
        self.assertIn('--skip-doxygen', call_args)
        self.assertIn('--skip-pyreverse', call_args)
        self.assertIn('--skip-ctags', call_args)
    
    @patch('subprocess.run')
    def test_run_llmprep_failure(self, mock_run):
        """Test llmprep failure handling."""
        mock_run.return_value = Mock(returncode=1, stderr='Error occurred', stdout='')
        
        config = Mock()
        config.get.return_value = {
            'llmprep': {
                'enabled': True,
                'output_dir': 'llm_prep',
                'depth': 4,
                'skip_doxygen': False,
                'skip_pyreverse': False,
                'skip_ctags': False
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        result = preprocessor.run_llmprep()
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    def test_run_llmprep_timeout(self, mock_run):
        """Test llmprep timeout handling."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 300)
        
        config = Mock()
        config.get.return_value = {
            'llmprep': {
                'enabled': True,
                'output_dir': 'llm_prep',
                'depth': 4,
                'skip_doxygen': False,
                'skip_pyreverse': False,
                'skip_ctags': False
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        result = preprocessor.run_llmprep()
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Timeout', result['error'])


class TestFullWorkflow(unittest.TestCase):
    """Test full preprocessing workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files
        with open(os.path.join(self.test_dir, 'test.c'), 'w') as f:
            f.write('// Comment\nint main() { return 0; }')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_run_both_disabled(self):
        """Test run with both minifier and llmprep disabled."""
        config = Mock()
        config.get.return_value = {
            'minifier': {'enabled': False},
            'llmprep': {'enabled': False}
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        results = preprocessor.run()
        
        self.assertFalse(results['minifier']['enabled'])
        self.assertFalse(results['llmprep']['enabled'])
    
    @patch('subprocess.run')
    def test_run_both_enabled(self, mock_run):
        """Test run with both minifier and llmprep enabled."""
        mock_run.return_value = Mock(returncode=0, stderr='', stdout='')
        
        config = Mock()
        config.get.return_value = {
            'minifier': {
                'enabled': True,
                'keep_comments': True,
                'exclude_dirs': [],
                'output_mode': 'in_place'
            },
            'llmprep': {
                'enabled': True,
                'output_dir': 'llm_prep',
                'depth': 4,
                'skip_doxygen': False,
                'skip_pyreverse': False,
                'skip_ctags': False
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        results = preprocessor.run()
        
        self.assertTrue(results['minifier']['enabled'])
        self.assertTrue(results['llmprep']['enabled'])
        self.assertTrue(results['minifier']['files_processed'] > 0)
        self.assertTrue(results['llmprep']['success'])
    
    def test_run_minifier_only(self):
        """Test run with only minifier enabled."""
        config = Mock()
        config.get.return_value = {
            'minifier': {
                'enabled': True,
                'keep_comments': False,
                'exclude_dirs': [],
                'output_mode': 'in_place'
            },
            'llmprep': {'enabled': False}
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        results = preprocessor.run()
        
        self.assertTrue(results['minifier']['enabled'])
        self.assertFalse(results['llmprep']['enabled'])
        self.assertGreater(results['minifier']['files_processed'], 0)
    
    @patch('subprocess.run')
    def test_run_llmprep_only(self, mock_run):
        """Test run with only llmprep enabled."""
        mock_run.return_value = Mock(returncode=0, stderr='', stdout='')
        
        config = Mock()
        config.get.return_value = {
            'minifier': {'enabled': False},
            'llmprep': {
                'enabled': True,
                'output_dir': 'llm_prep',
                'depth': 4,
                'skip_doxygen': False,
                'skip_pyreverse': False,
                'skip_ctags': False
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.minifier_config = preprocessor.preprocessing_config['minifier']
        preprocessor.llmprep_config = preprocessor.preprocessing_config['llmprep']
        
        results = preprocessor.run()
        
        self.assertFalse(results['minifier']['enabled'])
        self.assertTrue(results['llmprep']['enabled'])
        self.assertTrue(results['llmprep']['success'])


class TestEnvironmentProbePreprocessing(unittest.TestCase):
    """Test environment probe preprocessing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_run_environment_probe_success(self):
        """Test successful environment probe execution."""
        config = Mock()
        config.get.return_value = {
            'environment_probe': {
                'enabled': True,
                'output_file': '.collab_env.md'
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.environment_probe_config = preprocessor.preprocessing_config['environment_probe']
        
        result = preprocessor.run_environment_probe()
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['output_file'])
        
        # Verify file was created
        output_file = result['output_file']
        self.assertTrue(os.path.exists(output_file))
        
        # Verify file has content
        with open(output_file, 'r') as f:
            content = f.read()
        self.assertGreater(len(content), 0)
        self.assertIn('# Environment Summary', content)
    
    def test_run_environment_probe_disabled(self):
        """Test environment probe when disabled."""
        config = Mock()
        config.get.return_value = {
            'environment_probe': {
                'enabled': False
            }
        }
        
        preprocessor = SessionPreprocessor(config, self.test_dir)
        preprocessor.preprocessing_config = config.get.return_value
        preprocessor.environment_probe_config = preprocessor.preprocessing_config['environment_probe']
        
        result = preprocessor.run_environment_probe()
        
        self.assertFalse(result['success'])
        self.assertIsNone(result['output_file'])


class TestFactoryFunction(unittest.TestCase):
    """Test factory function."""
    
    def test_create_session_preprocessor(self):
        """Test create_session_preprocessor factory function."""
        config = Mock()
        config.get.return_value = {}
        
        test_dir = tempfile.mkdtemp()
        try:
            preprocessor = create_session_preprocessor(config, test_dir)
            self.assertIsInstance(preprocessor, SessionPreprocessor)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


def run_tests():
    """Run all tests."""
    print("Running session preprocessor tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSessionPreprocessorInit))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentProbePreprocessing))
    suite.addTests(loader.loadTestsFromTestCase(TestMinifierPreprocessing))
    suite.addTests(loader.loadTestsFromTestCase(TestLlmprepPreprocessing))
    suite.addTests(loader.loadTestsFromTestCase(TestFullWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestFactoryFunction))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
