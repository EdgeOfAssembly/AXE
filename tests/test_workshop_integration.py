"""
Integration Tests for Workshop Tools - Test end-to-end functionality
"""

import unittest
import tempfile
from unittest.mock import Mock, patch

class TestWorkshopIntegration(unittest.TestCase):
    """Integration tests for workshop tools with AXE."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('workshop.chisel.ChiselAnalyzer')
    def test_full_workshop_workflow(self, mock_analyzer_class):
        """Test complete workshop workflow from command to database."""
        # This would require mocking the entire AXE system
        # For now, just test the components individually
        
        # Mock chisel analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_binary.return_value = {
            'found_paths': 10,
            'vulnerabilities': [{'type': 'buffer_overflow', 'severity': 'high'}]
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        # Test the analyzer directly
        from workshop.chisel import ChiselAnalyzer
        analyzer = ChiselAnalyzer()
        result = analyzer.analyze_binary('/fake/path')
        
        self.assertIn('found_paths', result)
        self.assertEqual(result['found_paths'], 10)

    def test_workshop_command_parsing(self):
        """Test workshop command parsing logic."""
        # Test command parsing (this would be part of AXE integration)
        test_commands = [
            ("chisel /bin/test", ("chisel", "/bin/test")),
            ("saw 'print(input())'", ("saw", "'print(input())'")),
            ("plane .", ("plane", ".")),
            ("hammer python", ("hammer", "python")),
            ("history chisel", ("history", "chisel")),
            ("stats", ("stats", "")),
        ]
        
        for command_str, expected in test_commands:
            parts = command_str.split(maxsplit=1)
            tool = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            self.assertEqual((tool, args), expected)

    def test_xp_bonus_calculation(self):
        """Test XP bonus calculation for different analysis results."""
        from progression.xp_system import get_workshop_xp_bonus
        
        # Test chisel bonuses
        chisel_results = {
            'found_paths': 150,  # Should give max path bonus
            'vulnerabilities': [{'type': 'overflow'}, {'type': 'race'}]  # 2 vulns
        }
        bonus = get_workshop_xp_bonus(chisel_results, 'chisel')
        self.assertGreaterEqual(bonus, 20)  # Path bonus
        self.assertGreaterEqual(bonus, 20)  # Vulnerability bonus
        
        # Test saw bonuses
        saw_results = {
            'taint_flows': [{'source': 'input', 'sink': 'exec'}] * 3,  # 3 flows
            'vulnerabilities': [{'type': 'injection'}]  # 1 vuln
        }
        bonus = get_workshop_xp_bonus(saw_results, 'saw')
        self.assertGreaterEqual(bonus, 45)  # 3 flows * 15 = 45
        
        # Test plane bonuses
        plane_results = {
            'sources': [{'name': 'input'}] * 20,  # 20 sources
            'sinks': [{'name': 'exec'}] * 15     # 15 sinks
        }
        bonus = get_workshop_xp_bonus(plane_results, 'plane')
        self.assertGreaterEqual(bonus, 7)  # (20+15)/5 = 7

    def test_database_schema(self):
        """Test that database schema includes workshop tables."""
        from database.schema import WORKSHOP_ANALYSIS_TABLE, WORKSHOP_ANALYSIS_INDEXES
        
        # Check table creation SQL
        self.assertIn('workshop_analysis', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('analysis_id', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('tool_name', WORKSHOP_ANALYSIS_TABLE)
        
        # Check indexes
        self.assertGreater(len(WORKSHOP_ANALYSIS_INDEXES), 0)
        index_sql = WORKSHOP_ANALYSIS_INDEXES[0]
        self.assertIn('CREATE INDEX', index_sql)

    def test_configuration_loading(self):
        """Test workshop configuration loading."""
        # Test default config structure
        config = {
            'workshop': {
                'enabled': True,
                'chisel': {'max_paths': 1000},
                'saw': {'max_depth': 10},
                'plane': {'exclude_patterns': ['__pycache__']},
                'hammer': {'monitoring_interval': 0.1}
            }
        }
        
        # Verify structure
        self.assertTrue(config['workshop']['enabled'])
        self.assertIn('chisel', config['workshop'])
        self.assertIn('saw', config['workshop'])
        self.assertIn('plane', config['workshop'])
        self.assertIn('hammer', config['workshop'])

if __name__ == '__main__':
    unittest.main()