"""
Test Workshop Tools - Unit tests for dynamic analysis tools
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

class TestWorkshop(unittest.TestCase):
    """Test cases for workshop dynamic analysis tools."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_chisel_basic(self):
        """Test basic chisel symbolic execution."""
        try:
            from workshop.chisel import ChiselAnalyzer
            analyzer = ChiselAnalyzer()

            # Create a simple test binary (this would need actual binary)
            # For now, just test the class instantiation
            self.assertIsInstance(analyzer, ChiselAnalyzer)
        except ImportError:
            self.skipTest("angr not available")

    def test_saw_basic(self):
        """Test basic saw taint analysis."""
        from workshop.saw import SawTracker
        tracker = SawTracker()

        # Test simple code analysis
        code = """
def vulnerable_func(user_input):
    import os
    os.system(user_input)  # This should be flagged
"""

        result = tracker.analyze_code(code)
        self.assertIn('taint_flows', result)
        self.assertIn('vulnerabilities', result)

    def test_plane_basic(self):
        """Test basic plane source/sink enumeration."""
        from workshop.plane import PlaneEnumerator
        enumerator = PlaneEnumerator()

        # Create test Python file
        test_file = Path(self.test_dir) / "test.py"
        test_file.write_text("""
import os
user_input = input()
os.system(user_input)  # sink
""")

        result = enumerator.enumerate_file(str(test_file))
        self.assertIsInstance(result, tuple)
        sources, sinks = result
        self.assertGreater(len(sources), 0)
        self.assertGreater(len(sinks), 0)

    def test_hammer_basic(self):
        """Test basic hammer instrumentation."""
        try:
            from workshop.hammer import HammerInstrumentor
            instrumentor = HammerInstrumentor()

            # Just test instantiation
            self.assertIsInstance(instrumentor, HammerInstrumentor)
        except ImportError:
            self.skipTest("frida not available")

    def test_database_integration_chisel(self):
        """Test database integration with workshop analysis."""
        from database.agent_db import AgentDatabase
        from workshop import HAS_CHISEL
        import tempfile
        import os
        
        # Use isolated temp database with proper cleanup via context manager
        # This ensures cleanup even if test assertions fail
        temp_db_path = None
        try:
            temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
            os.close(temp_db_fd)  # Close file descriptor, we just need the path
            
            db = AgentDatabase(temp_db_path)
            
            # We can test database functionality without requiring chisel to be available
            # Just save a mock workshop analysis result
            analysis_id = db.save_workshop_analysis(
                'chisel', '/test/binary', 'agent_123',
                {'test': 'result', 'found_paths': 5, 'vulnerabilities': []}, 1.5
            )
            
            self.assertIsInstance(analysis_id, str)
            self.assertGreater(len(analysis_id), 0)
            
            # Test retrieval
            analyses = db.get_workshop_analyses(tool_name='chisel', limit=1)
            self.assertEqual(len(analyses), 1)
            self.assertEqual(analyses[0]['tool_name'], 'chisel')
        finally:
            if temp_db_path and os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_xp_system_integration(self):
        """Test XP system integration with workshop tools."""
        from progression.xp_system import award_xp_for_activity, get_workshop_xp_bonus
        
        # Test base XP awards
        chisel_xp = award_xp_for_activity('workshop_chisel')
        self.assertEqual(chisel_xp, 25)
        
        saw_xp = award_xp_for_activity('workshop_saw')
        self.assertEqual(saw_xp, 20)
        
        # Test bonus XP calculation
        chisel_results = {
            'found_paths': 50,
            'vulnerabilities': [{'type': 'overflow'}, {'type': 'injection'}]
        }
        bonus = get_workshop_xp_bonus(chisel_results, 'chisel')
        self.assertGreater(bonus, 0)  # Should get bonus for paths and vulns
        
        saw_results = {
            'taint_flows': [{'source': 'input', 'sink': 'exec'}],
            'vulnerabilities': [{'type': 'code_injection'}]
        }
        bonus = get_workshop_xp_bonus(saw_results, 'saw')
        self.assertGreater(bonus, 0)

    def test_workshop_stats(self):
        """Test workshop statistics retrieval."""
        from database.agent_db import AgentDatabase
        import tempfile
        import os
        
        # Use isolated temp database with proper cleanup via context manager
        # This ensures cleanup even if test assertions fail
        temp_db_path = None
        try:
            temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
            os.close(temp_db_fd)  # Close file descriptor, we just need the path
            
            db = AgentDatabase(temp_db_path)
            
            # Add some test data to fresh database
            db.save_workshop_analysis('chisel', 'test1', 'agent1', {'result': 'ok'}, 1.0)
            db.save_workshop_analysis('saw', 'test2', 'agent1', {'result': 'ok'}, 2.0)
            db.save_workshop_analysis('chisel', 'test3', 'agent1', {'error': 'fail'}, 0.5, 'Failed')
            
            # Get stats
            stats = db.get_workshop_stats('agent1')
            
            self.assertIn('chisel', stats)
            self.assertIn('saw', stats)
            self.assertEqual(stats['chisel']['total_analyses'], 2)
            self.assertEqual(stats['saw']['total_analyses'], 1)
        finally:
            if temp_db_path and os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

if __name__ == '__main__':
    unittest.main()