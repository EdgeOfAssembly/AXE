#!/usr/bin/env python3
"""
Test suite for Source Code Minifier.

Tests minification for C, C++, Python, and Assembly code.
"""

import sys
import os
import tempfile
import shutil
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.minifier import (
    Minifier,
    minify_file,
    minify_directory,
    minify_c_cpp,
    minify_python,
    minify_asm,
    comment_remover_c_cpp,
    remove_comments_and_docstrings,
    detect_language,
    collect_files,
    DEFAULT_EXCLUDE_DIRS
)


class TestCCppMinification(unittest.TestCase):
    """Test C/C++ code minification."""
    
    def test_comment_removal(self):
        """Test C/C++ comment removal."""
        code = """
        // Single line comment
        int main() {
            /* Multi-line
               comment */
            return 0;
        }
        """
        result = comment_remover_c_cpp(code)
        self.assertNotIn('//', result)
        self.assertNotIn('/*', result)
        self.assertIn('int main()', result)
    
    def test_comment_preservation(self):
        """Test that comments are preserved when requested."""
        code = "// Comment\nint x = 5;"
        result = minify_c_cpp(code, keep_comments=True)
        self.assertIn('//', result)
    
    def test_string_preservation(self):
        """Test that strings with comment-like content are preserved."""
        code = 'char *s = "// not a comment";'
        result = comment_remover_c_cpp(code)
        self.assertIn('"// not a comment"', result)
    
    def test_whitespace_removal(self):
        """Test whitespace and blank line removal."""
        code = """
        int main() {
        
            int x = 5;
            
            return x;
        }
        """
        result = minify_c_cpp(code, keep_comments=False)
        self.assertNotIn('\n\n', result)
        lines = result.split('\n')
        self.assertTrue(all(line.strip() for line in lines))


class TestPythonMinification(unittest.TestCase):
    """Test Python code minification."""
    
    def test_comment_removal(self):
        """Test Python comment removal."""
        code = """
# This is a comment
def hello():
    # Another comment
    print("Hello")
"""
        result = remove_comments_and_docstrings(code)
        self.assertNotIn('#', result)
        self.assertIn('def hello()', result)
        self.assertIn('print', result)
    
    def test_docstring_removal(self):
        """Test Python docstring removal."""
        code = '''
def hello():
    """This is a docstring"""
    return "Hello"
'''
        result = remove_comments_and_docstrings(code)
        self.assertNotIn('This is a docstring', result)
        self.assertIn('return "Hello"', result)
    
    def test_string_preservation(self):
        """Test that regular strings are preserved."""
        code = 'message = "# Not a comment"'
        result = remove_comments_and_docstrings(code)
        self.assertIn('"# Not a comment"', result)
    
    def test_indentation_preservation(self):
        """Test that Python indentation is preserved."""
        code = """
def outer():
    def inner():
        if True:
            return 42
"""
        result = minify_python(code, keep_comments=False)
        lines = result.split('\n')
        
        # Check indentation levels are preserved
        for line in lines:
            if 'def outer' in line:
                self.assertEqual(len(line) - len(line.lstrip()), 0)
            elif 'def inner' in line:
                self.assertGreater(len(line) - len(line.lstrip()), 0)
            elif 'if True' in line:
                self.assertGreater(len(line) - len(line.lstrip()), 0)
            elif 'return 42' in line:
                self.assertGreater(len(line) - len(line.lstrip()), 0)
    
    def test_comment_preservation(self):
        """Test that comments are preserved when requested."""
        code = "# Important comment\nx = 5"
        result = minify_python(code, keep_comments=True)
        self.assertIn('#', result)


class TestAsmMinification(unittest.TestCase):
    """Test Assembly code minification."""
    
    def test_comment_removal(self):
        """Test assembly comment removal."""
        code = """
        mov eax, 5      ; Load 5 into eax
        add eax, 10     ; Add 10
        """
        result = minify_asm(code, keep_comments=False)
        self.assertNotIn(';', result)
        self.assertIn('mov eax, 5', result)
        self.assertIn('add eax, 10', result)
    
    def test_comment_preservation(self):
        """Test that comments are preserved when requested."""
        code = "mov eax, 5  ; comment"
        result = minify_asm(code, keep_comments=True)
        self.assertIn(';', result)
    
    def test_whitespace_removal(self):
        """Test whitespace removal."""
        code = """
        
        mov eax, 5
        
        ret
        """
        result = minify_asm(code, keep_comments=False)
        lines = result.split('\n')
        self.assertTrue(all(line.strip() for line in lines))


class TestLanguageDetection(unittest.TestCase):
    """Test language detection."""
    
    def test_c_detection_by_extension(self):
        """Test C detection by file extension."""
        lang = detect_language('test.c', 'int main() {}')
        self.assertEqual(lang, 'c_cpp')
    
    def test_cpp_detection_by_extension(self):
        """Test C++ detection by file extension."""
        for ext in ['.cpp', '.cc', '.cxx', '.hpp', '.h']:
            lang = detect_language(f'test{ext}', 'int main() {}')
            self.assertEqual(lang, 'c_cpp', f"Failed for extension {ext}")
    
    def test_python_detection_by_extension(self):
        """Test Python detection by file extension."""
        lang = detect_language('test.py', 'def hello(): pass')
        self.assertEqual(lang, 'python')
    
    def test_asm_detection_by_extension(self):
        """Test Assembly detection by file extension."""
        for ext in ['.asm', '.s', '.S']:
            lang = detect_language(f'test{ext}', 'mov eax, 5')
            self.assertEqual(lang, 'asm', f"Failed for extension {ext}")
    
    def test_unsupported_language(self):
        """Test unsupported language returns None."""
        lang = detect_language('test.txt', 'some text')
        self.assertIsNone(lang)


class TestFileCollection(unittest.TestCase):
    """Test file collection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_single_file_collection(self):
        """Test collecting a single file."""
        test_file = os.path.join(self.test_dir, 'test.c')
        with open(test_file, 'w') as f:
            f.write('int main() {}')
        
        files = collect_files([test_file])
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][0], test_file)
    
    def test_directory_collection_non_recursive(self):
        """Test collecting files from directory (non-recursive)."""
        # Create test files
        for name in ['test1.c', 'test2.py', 'readme.txt']:
            with open(os.path.join(self.test_dir, name), 'w') as f:
                f.write('test')
        
        files = collect_files([self.test_dir], recursive=False)
        # Should find test1.c and test2.py, but not readme.txt
        self.assertEqual(len(files), 2)
    
    def test_directory_collection_recursive(self):
        """Test collecting files from directory (recursive)."""
        # Create nested structure
        subdir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(subdir)
        
        with open(os.path.join(self.test_dir, 'test1.c'), 'w') as f:
            f.write('test')
        with open(os.path.join(subdir, 'test2.py'), 'w') as f:
            f.write('test')
        
        files = collect_files([self.test_dir], recursive=True)
        self.assertEqual(len(files), 2)
    
    def test_exclude_directories(self):
        """Test directory exclusion."""
        # Create test structure with excluded directories
        tests_dir = os.path.join(self.test_dir, 'tests')
        pycache_dir = os.path.join(self.test_dir, '__pycache__')
        os.makedirs(tests_dir)
        os.makedirs(pycache_dir)
        
        with open(os.path.join(self.test_dir, 'main.py'), 'w') as f:
            f.write('test')
        with open(os.path.join(tests_dir, 'test.py'), 'w') as f:
            f.write('test')
        with open(os.path.join(pycache_dir, 'cache.py'), 'w') as f:
            f.write('test')
        
        files = collect_files([self.test_dir], recursive=True, exclude_dirs=DEFAULT_EXCLUDE_DIRS)
        # Should only find main.py
        self.assertEqual(len(files), 1)
        self.assertIn('main.py', files[0][1])


class TestMinifierClass(unittest.TestCase):
    """Test Minifier class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.minifier = Minifier()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_minify_single_file(self):
        """Test minifying a single file."""
        test_file = os.path.join(self.test_dir, 'test.c')
        with open(test_file, 'w') as f:
            f.write('// Comment\nint main() {\n    return 0;\n}')
        
        result = self.minifier.minify_file(test_file, keep_comments=False)
        self.assertNotIn('//', result)
        self.assertIn('int main()', result)
    
    def test_minify_directory(self):
        """Test minifying a directory."""
        # Create test files
        for i, name in enumerate(['test1.c', 'test2.py']):
            with open(os.path.join(self.test_dir, name), 'w') as f:
                if name.endswith('.c'):
                    f.write('// Comment\nint main() { return 0; }')
                else:
                    f.write('# Comment\ndef hello(): pass')
        
        results = self.minifier.minify_directory(self.test_dir, recursive=False, keep_comments=False)
        self.assertEqual(len(results), 2)
    
    def test_minify_workspace_in_place(self):
        """Test workspace minification in-place."""
        # Create test file
        test_file = os.path.join(self.test_dir, 'test.c')
        with open(test_file, 'w') as f:
            f.write('// Comment\nint main() {\n    return 0;\n}')
        
        stats = self.minifier.minify_workspace(self.test_dir, keep_comments=False, output_mode='in_place')
        
        self.assertEqual(stats['files_processed'], 1)
        self.assertGreater(stats['bytes_saved'], 0)
        
        # Check file was modified
        with open(test_file, 'r') as f:
            content = f.read()
            self.assertNotIn('//', content)
    
    def test_minify_workspace_separate_dir(self):
        """Test workspace minification to separate directory."""
        # Create test file
        test_file = os.path.join(self.test_dir, 'test.c')
        with open(test_file, 'w') as f:
            f.write('// Comment\nint main() {\n    return 0;\n}')
        
        output_dir = os.path.join(self.test_dir, 'minified')
        stats = self.minifier.minify_workspace(
            self.test_dir,
            keep_comments=False,
            output_mode='separate_dir',
            output_dir=output_dir
        )
        
        self.assertEqual(stats['files_processed'], 1)
        self.assertTrue(os.path.exists(output_dir))
        
        # Check original file unchanged
        with open(test_file, 'r') as f:
            content = f.read()
            self.assertIn('//', content)
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        test_file = os.path.join(self.test_dir, 'test.c')
        original = '// Long comment\nint main() { return 0; }'
        with open(test_file, 'w') as f:
            f.write(original)
        
        self.minifier.minify_file(test_file, keep_comments=False)
        
        self.assertEqual(self.minifier.stats['files_processed'], 1)
        self.assertGreater(self.minifier.stats['bytes_original'], 0)
        self.assertGreater(self.minifier.stats['bytes_minified'], 0)
        self.assertLess(self.minifier.stats['bytes_minified'], self.minifier.stats['bytes_original'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.minifier = Minifier()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_empty_file(self):
        """Test minifying an empty file."""
        test_file = os.path.join(self.test_dir, 'empty.c')
        with open(test_file, 'w') as f:
            f.write('')
        
        result = self.minifier.minify_file(test_file)
        self.assertEqual(result, '')
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.minifier.minify_file('/nonexistent/file.c')
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file type."""
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('some text')
        
        with self.assertRaises(ValueError):
            self.minifier.minify_file(test_file)
    
    def test_malformed_python(self):
        """Test handling of malformed Python code."""
        test_file = os.path.join(self.test_dir, 'bad.py')
        with open(test_file, 'w') as f:
            f.write('def broken(\n    no closing paren')
        
        # Should handle gracefully (return original or similar)
        try:
            result = self.minifier.minify_file(test_file, keep_comments=False)
            # If it doesn't raise, it should return something
            self.assertIsInstance(result, str)
        except Exception:
            # Or it might raise, which is also acceptable
            pass


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_minify_file_function(self):
        """Test minify_file convenience function."""
        test_file = os.path.join(self.test_dir, 'test.c')
        with open(test_file, 'w') as f:
            f.write('// Comment\nint main() {}')
        
        result = minify_file(test_file, keep_comments=False)
        self.assertNotIn('//', result)
    
    def test_minify_directory_function(self):
        """Test minify_directory convenience function."""
        test_file = os.path.join(self.test_dir, 'test.c')
        with open(test_file, 'w') as f:
            f.write('// Comment\nint main() {}')
        
        results = minify_directory(self.test_dir, recursive=False, keep_comments=False)
        self.assertEqual(len(results), 1)


def run_tests():
    """Run all tests."""
    print("Running minifier tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCCppMinification))
    suite.addTests(loader.loadTestsFromTestCase(TestPythonMinification))
    suite.addTests(loader.loadTestsFromTestCase(TestAsmMinification))
    suite.addTests(loader.loadTestsFromTestCase(TestLanguageDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestFileCollection))
    suite.addTests(loader.loadTestsFromTestCase(TestMinifierClass))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
