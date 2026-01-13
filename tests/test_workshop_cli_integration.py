#!/usr/bin/env python3
"""
Test Workshop CLI integration to verify /workshop commands work properly.
"""

import unittest
import sys
import io
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from axe import ChatSession, Config


class TestWorkshopCLIIntegration(unittest.TestCase):
    """Test workshop CLI command integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        self.session = ChatSession(self.config, '.')

    def test_workshop_help_command(self):
        """Test /workshop help displays correctly."""
        # Capture stdout
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('help')
        
        output = captured_output.getvalue()
        
        # Check for key components
        self.assertIn('Workshop - Dynamic Analysis Tools', output)
        self.assertIn('chisel', output)
        self.assertIn('saw', output)
        self.assertIn('plane', output)
        self.assertIn('hammer', output)
        self.assertIn('Symbolic execution', output)
        self.assertIn('Taint analysis', output)
        self.assertIn('workshop_quick_reference.md', output)

    def test_workshop_no_args_shows_help(self):
        """Test /workshop with no args shows help."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('')
        
        output = captured_output.getvalue()
        self.assertIn('Workshop - Dynamic Analysis Tools', output)

    def test_workshop_history_no_analyses(self):
        """Test /workshop history displays history data or empty message."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('history')
        
        output = captured_output.getvalue()
        # The shared database may have existing data from other tests
        # Either shows "No analyses found" or actual analysis history
        self.assertTrue(
            'No workshop analyses found' in output or 
            'Workshop Analysis History' in output,
            f"Expected history message or history data, got: {output}"
        )

    def test_workshop_stats_no_analyses(self):
        """Test /workshop stats displays stats or empty message."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('stats')
        
        output = captured_output.getvalue()
        # The shared database may have existing data from other tests
        # Either shows "No statistics available" or actual statistics
        self.assertTrue(
            'No workshop statistics available' in output or 
            'Workshop Usage Statistics' in output,
            f"Expected stats message or stats data, got: {output}"
        )

    def test_workshop_unknown_command(self):
        """Test /workshop with unknown subcommand."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('unknowncommand')
        
        output = captured_output.getvalue()
        self.assertIn('Unknown workshop command', output)
        self.assertIn('unknowncommand', output)

    def test_process_command_workshop(self):
        """Test /workshop command is processed by process_command."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = self.session.process_command('/workshop help')
        
        # Should return True (continue session)
        self.assertTrue(result)
        
        output = captured_output.getvalue()
        self.assertIn('Workshop - Dynamic Analysis Tools', output)

    def test_workshop_chisel_no_args(self):
        """Test /workshop chisel with no args shows usage."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('chisel')
        
        output = captured_output.getvalue()
        # Since chisel is not installed, should show not available message
        self.assertTrue('not available' in output.lower() or 'usage' in output.lower())

    def test_workshop_saw_no_args(self):
        """Test /workshop saw with no args shows usage."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('saw')
        
        output = captured_output.getvalue()
        # Saw should be available, should show usage
        self.assertIn('Usage', output)

    def test_workshop_plane_no_args(self):
        """Test /workshop plane with no args shows usage."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('plane')
        
        output = captured_output.getvalue()
        # Plane should be available, should show usage
        self.assertIn('Usage', output)

    def test_workshop_hammer_no_args(self):
        """Test /workshop hammer with no args shows usage."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.handle_workshop_command('hammer')
        
        output = captured_output.getvalue()
        # Since hammer is not installed, should show not available message
        self.assertTrue('not available' in output.lower() or 'usage' in output.lower())

    def test_workshop_tool_initialization(self):
        """Test workshop tools are initialized correctly."""
        # Check that workshop tools attributes exist
        self.assertTrue(hasattr(self.session, 'workshop_chisel'))
        self.assertTrue(hasattr(self.session, 'workshop_saw'))
        self.assertTrue(hasattr(self.session, 'workshop_plane'))
        self.assertTrue(hasattr(self.session, 'workshop_hammer'))
        
        # Saw and Plane should be available
        self.assertIsNotNone(self.session.workshop_saw)
        self.assertIsNotNone(self.session.workshop_plane)

    def test_help_includes_workshop(self):
        """Test /help includes workshop commands."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.session.print_help()
        
        output = captured_output.getvalue()
        self.assertIn('/workshop', output)
        self.assertIn('Workshop Tools', output)


if __name__ == '__main__':
    unittest.main()
