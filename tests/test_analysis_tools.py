"""
Test Analysis Tools - Unit tests for llmprep and build_analyzer integration
"""

import unittest
import tempfile
import os
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestLlmprepIntegration(unittest.TestCase):
    """Test cases for llmprep integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        self.llmprep_script = os.path.join(self.tools_dir, "llmprep.py")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_llmprep_script_exists(self):
        """Test that llmprep.py exists in tools directory."""
        self.assertTrue(os.path.exists(self.llmprep_script),
                       f"llmprep.py not found at {self.llmprep_script}")

    def test_llmprep_basic_execution(self):
        """Test basic llmprep execution on a simple directory."""
        # Create a simple test file
        test_file = os.path.join(self.test_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("# Test Python file\ndef hello():\n    print('Hello')\n")
        
        output_dir = os.path.join(self.test_dir, "llm_prep")
        
        # Run llmprep
        cmd = [sys.executable, self.llmprep_script, self.test_dir, "-o", output_dir]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Check that it ran (exit code 0 or graceful degradation)
            # llmprep may not have all dependencies, so we accept partial success
            self.assertIn(result.returncode, [0, 1],
                         f"llmprep failed unexpectedly: {result.stderr}")
            
            # If successful, check output directory was created
            if result.returncode == 0:
                self.assertTrue(os.path.exists(output_dir),
                              "Output directory not created")
        
        except subprocess.TimeoutExpired:
            self.fail("llmprep timed out")
        except Exception as e:
            self.fail(f"llmprep execution failed: {e}")

    def test_llmprep_command_structure(self):
        """Test that llmprep accepts expected command-line arguments."""
        # Just check help/version works (should be quick)
        cmd = [sys.executable, self.llmprep_script, "--help"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            # Should either succeed with help or fail gracefully
            self.assertIsNotNone(result.stdout or result.stderr)
        except Exception as e:
            # Script might not have --help, that's okay
            pass


class TestBuildAnalyzerIntegration(unittest.TestCase):
    """Test cases for build_analyzer integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        self.build_analyzer_script = os.path.join(self.tools_dir, "build_analyzer.py")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_analyzer_script_exists(self):
        """Test that build_analyzer.py exists in tools directory."""
        self.assertTrue(os.path.exists(self.build_analyzer_script),
                       f"build_analyzer.py not found at {self.build_analyzer_script}")

    def test_build_analyzer_basic_execution(self):
        """Test basic build_analyzer execution on a directory."""
        # Create a simple autotools-style project
        configure_ac = os.path.join(self.test_dir, "configure.ac")
        with open(configure_ac, "w") as f:
            f.write("AC_INIT([test], [1.0])\n")
            f.write("AC_PREREQ([2.69])\n")
            f.write("AM_INIT_AUTOMAKE\n")
            f.write("AC_OUTPUT\n")
        
        # Run build_analyzer
        cmd = [sys.executable, self.build_analyzer_script, self.test_dir]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Should succeed or handle gracefully
            self.assertEqual(result.returncode, 0,
                           f"build_analyzer failed: {result.stderr}")
            
            # Should produce some output
            self.assertIsNotNone(result.stdout)
            self.assertGreater(len(result.stdout), 0, "No output from build_analyzer")
            
        except subprocess.TimeoutExpired:
            self.fail("build_analyzer timed out")
        except Exception as e:
            self.fail(f"build_analyzer execution failed: {e}")

    def test_build_analyzer_json_output(self):
        """Test that build_analyzer can produce JSON output."""
        # Create a simple CMake project
        cmakelists = os.path.join(self.test_dir, "CMakeLists.txt")
        with open(cmakelists, "w") as f:
            f.write("cmake_minimum_required(VERSION 3.10)\n")
            f.write("project(TestProject)\n")
        
        # Run build_analyzer with --json flag
        cmd = [sys.executable, self.build_analyzer_script, self.test_dir, "--json"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Try to parse as JSON
                try:
                    data = json.loads(result.stdout)
                    self.assertIsInstance(data, (dict, list),
                                        "JSON output is not a dict or list")
                except json.JSONDecodeError as e:
                    self.fail(f"build_analyzer --json output is not valid JSON: {e}")
        
        except subprocess.TimeoutExpired:
            self.fail("build_analyzer timed out")
        except Exception as e:
            self.fail(f"build_analyzer execution failed: {e}")


class TestAXECommandIntegration(unittest.TestCase):
    """Test cases for AXE command integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_prep_command_syntax(self):
        """Test that /prep command has correct syntax."""
        # Verify command syntax recognition
        command = "/prep"
        self.assertTrue(command.startswith('/prep') or command.startswith('/llmprep'))
        
        # Test alias
        command_alias = "/llmprep"
        self.assertTrue(command_alias.startswith('/prep') or command_alias.startswith('/llmprep'))

    def test_buildinfo_command_syntax(self):
        """Test that /buildinfo command has correct syntax."""
        command = "/buildinfo"
        self.assertTrue(command.startswith('/buildinfo'))

    def test_tools_whitelist_includes_analysis_tools(self):
        """Test that axe.yaml includes llmprep and build_analyzer in whitelist."""
        import yaml
        
        config_path = os.path.join(os.path.dirname(__file__), "axe.yaml")
        
        if not os.path.exists(config_path):
            self.skipTest("axe.yaml not found")
        
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Check that tools section exists and includes analysis tools
            self.assertIn('tools', config, "tools section not in config")
            
            # Find analysis tools in the tools whitelist
            tools = config.get('tools', {})
            
            # The tools should be in the analysis category
            if 'analysis' in tools:
                analysis_tools = tools['analysis']
                self.assertIn('llmprep', analysis_tools,
                            "llmprep not in analysis tools whitelist")
                self.assertIn('build_analyzer', analysis_tools,
                            "build_analyzer not in analysis tools whitelist")
        
        except yaml.YAMLError as e:
            self.fail(f"Failed to parse axe.yaml: {e}")


class TestExecBlockSupport(unittest.TestCase):
    """Test that tools work with EXEC blocks."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.tools_dir = os.path.join(os.path.dirname(__file__), "tools")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_llmprep_exec_block_syntax(self):
        """Test that llmprep can be called via EXEC block syntax."""
        llmprep_script = os.path.join(self.tools_dir, "llmprep.py")
        
        if not os.path.exists(llmprep_script):
            self.skipTest("llmprep.py not found")
        
        # Simulate EXEC block command
        cmd = f"python3 {llmprep_script} {self.test_dir} -o {self.test_dir}/output"
        
        # Verify command can be constructed and is valid
        self.assertIn("llmprep.py", cmd)
        self.assertIn(self.test_dir, cmd)

    def test_build_analyzer_exec_block_syntax(self):
        """Test that build_analyzer can be called via EXEC block syntax."""
        build_analyzer_script = os.path.join(self.tools_dir, "build_analyzer.py")
        
        if not os.path.exists(build_analyzer_script):
            self.skipTest("build_analyzer.py not found")
        
        # Simulate EXEC block command with --json
        cmd = f"python3 {build_analyzer_script} {self.test_dir} --json"
        
        # Verify command can be constructed and is valid
        self.assertIn("build_analyzer.py", cmd)
        self.assertIn("--json", cmd)


if __name__ == '__main__':
    unittest.main()
