#!/usr/bin/env python3
"""
Comprehensive validation test for PR #23 Workshop Dynamic Analysis Integration
Tests all workshop tools, database integration, XP system, and configuration.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestWorkshopPR23Validation(unittest.TestCase):
    """Comprehensive validation tests for PR #23 Workshop features."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_workshop_module_imports(self):
        """Test that workshop module can be imported."""
        try:
            from workshop import ChiselAnalyzer, SawTracker, PlaneEnumerator, HammerInstrumentor
            self.assertTrue(True, "Workshop imports successful")
        except ImportError as e:
            # Check if it's due to missing dependencies (acceptable)
            if 'angr' in str(e) or 'frida' in str(e):
                self.skipTest(f"Optional dependency not available: {e}")
            else:
                self.fail(f"Workshop import failed: {e}")

    def test_02_database_schema_workshop_tables(self):
        """Test that database schema includes workshop tables."""
        from database.schema import WORKSHOP_ANALYSIS_TABLE, WORKSHOP_ANALYSIS_INDEXES
        
        # Check table definition
        self.assertIn('workshop_analysis', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('analysis_id', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('tool_name', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('target', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('agent_id', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('results_json', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('status', WORKSHOP_ANALYSIS_TABLE)
        self.assertIn('duration_seconds', WORKSHOP_ANALYSIS_TABLE)
        
        # Check indexes
        self.assertIsInstance(WORKSHOP_ANALYSIS_INDEXES, list)
        self.assertGreater(len(WORKSHOP_ANALYSIS_INDEXES), 0)
        self.assertIn('idx_workshop_tool', WORKSHOP_ANALYSIS_INDEXES[0])

    def test_03_database_workshop_methods(self):
        """Test database workshop analysis methods."""
        from database.agent_db import AgentDatabase
        import tempfile
        import os
        
        # Create temp database for isolated testing
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            db = AgentDatabase(temp_db.name)
            
            # Test save_workshop_analysis
            analysis_id = db.save_workshop_analysis(
                'chisel', '/test/binary', 'agent_123',
                {'test': 'result'}, 1.5
            )
            
            self.assertIsInstance(analysis_id, str)
            self.assertGreater(len(analysis_id), 0)
            
            # Test get_workshop_analyses
            analyses = db.get_workshop_analyses(tool_name='chisel', limit=10)
            self.assertEqual(len(analyses), 1)
            self.assertEqual(analyses[0]['tool_name'], 'chisel')
            self.assertEqual(analyses[0]['target'], '/test/binary')
            
            # Test get_workshop_stats
            stats = db.get_workshop_stats()
            self.assertIn('chisel', stats)
            self.assertEqual(stats['chisel']['total_analyses'], 1)
        finally:
            # Cleanup
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)

    def test_04_xp_system_workshop_awards(self):
        """Test XP system workshop activity awards."""
        from progression.xp_system import award_xp_for_activity, get_workshop_xp_bonus, XP_AWARDS
        
        # Test base XP awards
        self.assertIn('workshop_chisel', XP_AWARDS)
        self.assertIn('workshop_saw', XP_AWARDS)
        self.assertIn('workshop_plane', XP_AWARDS)
        self.assertIn('workshop_hammer', XP_AWARDS)
        
        # Test award calculation
        chisel_xp = award_xp_for_activity('workshop_chisel')
        self.assertEqual(chisel_xp, 25)
        
        saw_xp = award_xp_for_activity('workshop_saw')
        self.assertEqual(saw_xp, 20)
        
        # Test bonus XP
        chisel_results = {
            'found_paths': 50,
            'vulnerabilities': [{'type': 'overflow'}, {'type': 'injection'}]
        }
        bonus = get_workshop_xp_bonus(chisel_results, 'chisel')
        self.assertGreaterEqual(bonus, 20)  # Should get bonus for paths and vulns

    def test_05_saw_taint_analysis_basic(self):
        """Test Saw taint analysis basic functionality."""
        from workshop.saw import SawTracker
        
        tracker = SawTracker()
        
        # Test simple vulnerable code
        code = """
def vulnerable_func(user_input):
    import os
    os.system(user_input)  # This should be flagged
"""
        
        result = tracker.analyze_code(code)
        self.assertIn('sources_found', result)
        self.assertIn('sinks_found', result)
        self.assertIn('taint_flows', result)
        self.assertIn('vulnerabilities', result)

    def test_06_plane_source_sink_enumeration(self):
        """Test Plane source/sink enumeration."""
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

    def test_07_chisel_basic_instantiation(self):
        """Test Chisel analyzer basic instantiation."""
        # Skip if angr not available
        import workshop
        if not workshop.HAS_CHISEL:
            self.skipTest("angr not available")
        
        from workshop.chisel import ChiselAnalyzer
        
        analyzer = ChiselAnalyzer()
        self.assertIsInstance(analyzer, ChiselAnalyzer)

    def test_08_hammer_basic_instantiation(self):
        """Test Hammer instrumentor basic instantiation."""
        # Skip if frida not available
        import workshop
        if not workshop.HAS_HAMMER:
            self.skipTest("frida not available")
        
        from workshop.hammer import HammerInstrumentor
        
        instrumentor = HammerInstrumentor()
        self.assertIsInstance(instrumentor, HammerInstrumentor)

    def test_09_workshop_configuration_structure(self):
        """Test workshop configuration in axe.yaml."""
        import yaml
        
        with open('axe.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check workshop config exists
        self.assertIn('workshop', config)
        workshop_config = config['workshop']
        
        # Check enabled flag
        self.assertIn('enabled', workshop_config)
        
        # Check tool configs
        self.assertIn('chisel', workshop_config)
        self.assertIn('saw', workshop_config)
        self.assertIn('plane', workshop_config)
        self.assertIn('hammer', workshop_config)
        
        # Check chisel config details
        self.assertIn('max_paths', workshop_config['chisel'])
        self.assertIn('timeout', workshop_config['chisel'])

    def test_10_dependencies_in_requirements(self):
        """Test that workshop dependencies are in requirements.txt."""
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        self.assertIn('angr', requirements)
        self.assertIn('frida-python', requirements)
        self.assertIn('psutil', requirements)

    def test_11_workshop_test_files_present(self):
        """Test that workshop test files are present."""
        self.assertTrue(Path('test_workshop.py').exists())
        self.assertTrue(Path('test_workshop_integration.py').exists())

    def test_12_workshop_documentation_present(self):
        """Test that workshop documentation files are present."""
        self.assertTrue(Path('workshop_quick_reference.md').exists())
        self.assertTrue(Path('workshop_benchmarks.md').exists())
        self.assertTrue(Path('workshop_security_audit.md').exists())
        self.assertTrue(Path('workshop_dependency_validation.md').exists())
        self.assertTrue(Path('workshop_test_results.md').exists())

    def test_13_no_hardcoded_secrets(self):
        """Test that no API keys or secrets are hardcoded in workshop files."""
        secret_patterns = [
            'api_key',
            'API_KEY',
            'secret_key',
            'SECRET_KEY',
            'password',
            'PASSWORD',
            'token',
            'TOKEN',
        ]
        
        # Check all workshop Python files
        workshop_files = list(Path('workshop').glob('*.py'))
        
        for file_path in workshop_files:
            with open(file_path, 'r') as f:
                content = f.read().lower()
                
            # Check for suspicious patterns (but allow variable names)
            for pattern in secret_patterns:
                if f'{pattern}=' in content or f'{pattern} =' in content:
                    # Check if it's not just a variable assignment
                    if not ('None' in content or 'config.get' in content):
                        self.fail(f"Potential hardcoded secret in {file_path}: {pattern}")

    def test_14_database_integration_end_to_end(self):
        """Test complete database integration workflow."""
        from database.agent_db import AgentDatabase
        import tempfile
        import os
        
        # Create temp database for isolated testing
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            db = AgentDatabase(temp_db.name)
            
            # Save multiple analyses
            db.save_workshop_analysis('chisel', 'test1', 'agent1', {'result': 'ok'}, 1.0)
            db.save_workshop_analysis('saw', 'test2', 'agent1', {'result': 'ok'}, 2.0)
            db.save_workshop_analysis('chisel', 'test3', 'agent1', {'error': 'fail'}, 0.5, 'Failed')
            
            # Get stats
            stats = db.get_workshop_stats('agent1')
            
            self.assertIn('chisel', stats)
            self.assertIn('saw', stats)
            self.assertEqual(stats['chisel']['total_analyses'], 2)
            self.assertEqual(stats['saw']['total_analyses'], 1)
            self.assertEqual(stats['chisel']['failed'], 1)
        finally:
            # Cleanup
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)

    def test_15_workshop_module_structure(self):
        """Test workshop module structure and exports."""
        import workshop
        
        # Check __all__ exports
        self.assertTrue(hasattr(workshop, '__all__'))
        self.assertIn('ChiselAnalyzer', workshop.__all__)
        self.assertIn('SawTracker', workshop.__all__)
        self.assertIn('PlaneEnumerator', workshop.__all__)
        self.assertIn('HammerInstrumentor', workshop.__all__)


def run_validation_suite():
    """Run the complete validation suite and generate report."""
    print("=" * 70)
    print("PR #23 Workshop Dynamic Analysis Framework Validation")
    print("=" * 70)
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWorkshopPR23Validation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()
    
    if result.wasSuccessful():
        print("✅ All validation tests PASSED!")
        return 0
    else:
        print("❌ Some validation tests FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_validation_suite())
