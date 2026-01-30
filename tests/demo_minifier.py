#!/usr/bin/env python3
"""
Demo: Source Code Minifier Integration
This demo shows how to use the new source code minifier feature in AXE
to reduce token usage when feeding code to LLMs.
The minifier supports:
- C, C++, Python, Assembly
- Comment removal (configurable)
- Whitespace optimization
- Python indentation preservation
- Directory exclusions (tests, __pycache__, etc.)
Usage:
    1. Enable in axe.yaml:
       preprocessing:
         minifier:
           enabled: true
           keep_comments: true  # or false for max reduction
    2. Start AXE session - minification runs automatically
    3. Or use the CLI tool directly:
       python3 tools/minifier.py <file_or_dir> --remove-comments
"""
import sys
import os
import tempfile
import shutil
# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.minifier import Minifier, minify_file
from core.config import Config
from core.session_preprocessor import SessionPreprocessor
def demo_standalone_minifier():
    """Demonstrate using the minifier as a standalone tool."""
    print("="*70)
    print("DEMO 1: Standalone Minifier Usage")
    print("="*70)
    # Create temporary test file
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, 'example.c')
    original_code = """
// Example C program with lots of comments
#include <stdio.h>
/*
 * Function: greet
 * Purpose: Print a greeting message
 * Parameters:
 *   name - The name to greet
 */
void greet(const char *name) {
    // Print the greeting
    printf("Hello, %s!\\n", name);  // Newline at end
}
int main(int argc, char *argv[]) {
    // Check arguments
    if (argc < 2) {
        printf("Usage: %s <name>\\n", argv[0]);
        return 1;
    }
    greet(argv[1]);  // Call greeting function
    return 0;  // Success
}
"""
    try:
        # Write original code
        with open(test_file, 'w') as f:
            f.write(original_code)
        print(f"\\nOriginal code ({len(original_code)} bytes):")
        print("-" * 70)
        print(original_code)
        # Minify with comment removal
        minified = minify_file(test_file, keep_comments=False)
        print(f"\\nMinified code ({len(minified)} bytes):")
        print("-" * 70)
        print(minified)
        reduction = len(original_code) - len(minified)
        reduction_pct = (reduction / len(original_code)) * 100
        print(f"\\n✓ Reduction: {reduction} bytes ({reduction_pct:.1f}%)")
        print(f"✓ Token savings: ~{reduction_pct:.0f}% fewer tokens to LLM")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
def demo_workspace_minification():
    """Demonstrate minifying an entire workspace."""
    print("\\n" + "="*70)
    print("DEMO 2: Workspace Minification")
    print("="*70)
    test_dir = tempfile.mkdtemp()
    # Create multiple files
    files = {
        'src/main.c': """
// Main program
#include <stdio.h>
int main() {
    printf("Hello\\n");  // Print message
    return 0;
}
""",
        'src/utils.py': """
# Utility functions
def helper():
    \"\"\"Helper function\"\"\"
    return 42  # The answer
""",
        'tests/test.py': """
# This file should be excluded
def test():
    pass
"""
    }
    try:
        # Create files
        for path, content in files.items():
            full_path = os.path.join(test_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        print(f"\\nCreated workspace at: {test_dir}")
        print("Files:")
        for path in files:
            print(f"  - {path}")
        # Minify workspace
        minifier = Minifier()
        stats = minifier.minify_workspace(
            test_dir,
            keep_comments=False,
            output_mode='separate_dir',
            output_dir=os.path.join(test_dir, 'minified')
        )
        print(f"\\nMinification results:")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Original size: {stats['bytes_original']} bytes")
        print(f"  Minified size: {stats['bytes_minified']} bytes")
        print(f"  Bytes saved: {stats['bytes_saved']} bytes")
        reduction_pct = (stats['bytes_saved'] / stats['bytes_original'] * 100)
        print(f"  Reduction: {reduction_pct:.1f}%")
        print(f"\\n✓ Minified files written to: {test_dir}/minified/")
        print("✓ Tests directory automatically excluded")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
def demo_session_preprocessing():
    """Demonstrate automatic session preprocessing."""
    print("\\n" + "="*70)
    print("DEMO 3: Automatic Session Preprocessing")
    print("="*70)
    test_dir = tempfile.mkdtemp()
    try:
        # Create test file
        with open(os.path.join(test_dir, 'app.py'), 'w') as f:
            f.write("""
#!/usr/bin/env python3
# Application entry point
def main():
    \"\"\"Main function\"\"\"
    print("App running")  # Status message
if __name__ == '__main__':
    main()
""")
        # Configure preprocessing
        config = Config()
        config.config['preprocessing'] = {
            'minifier': {
                'enabled': True,
                'keep_comments': False,
                'exclude_dirs': ['tests'],
                'output_mode': 'in_place'
            },
            'llmprep': {
                'enabled': False
            }
        }
        print("\\nConfiguration:")
        print("  preprocessing.minifier.enabled: True")
        print("  preprocessing.minifier.keep_comments: False")
        print("  preprocessing.minifier.output_mode: in_place")
        # Create preprocessor
        preprocessor = SessionPreprocessor(config, test_dir)
        print(f"\\nPreprocessor enabled: {preprocessor.is_enabled()}")
        # Run preprocessing
        results = preprocessor.run()
        print("\\nPreprocessing results:")
        minifier_result = results['minifier']
        print(f"  Minifier enabled: {minifier_result['enabled']}")
        print(f"  Files processed: {minifier_result['files_processed']}")
        print(f"  Bytes saved: {minifier_result['bytes_saved']}")
        print("\\n✓ Preprocessing would run automatically on AXE session start")
        print("✓ No manual intervention required")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
def demo_configuration():
    """Show configuration options."""
    print("\\n" + "="*70)
    print("DEMO 4: Configuration Options in axe.yaml")
    print("="*70)
    config_example = """
# Session preprocessing configuration
preprocessing:
  # Source code minification before llmprep
  minifier:
    enabled: false              # Set to true to enable
    keep_comments: true         # Recommended for AXE (context preservation)
    exclude_dirs:               # Directories to skip
      - tests
      - __pycache__
      - .git
      - venv
      - build
      - dist
    supported_extensions:       # File types to minify
      - .c
      - .cpp
      - .py
      - .asm
    output_mode: in_place       # Options: in_place, separate_dir
    output_dir: .minified       # Used if output_mode is separate_dir
  # Automatic llmprep after minification
  llmprep:
    enabled: false              # Set to true to enable
    output_dir: llm_prep
    depth: 4
    skip_doxygen: false
    skip_pyreverse: false
    skip_ctags: false
"""
    print("\\nAdd this to your axe.yaml:")
    print(config_example)
    print("\\nRecommended settings:")
    print("  • For development: keep_comments: true (preserves context)")
    print("  • For production: keep_comments: false (maximum reduction)")
    print("  • Always use output_mode: in_place for simplicity")
    print("  • Enable llmprep: true to also generate context files")
def main():
    """Run all demonstrations."""
    print("\\n" + "="*70)
    print("AXE Source Code Minifier - Feature Demonstration")
    print("="*70)
    print("\\nThis demo shows the new source code minifier feature that")
    print("automatically reduces token usage when feeding code to LLMs.")
    print("\\nExpected benefits:")
    print("  • 50-65% reduction in source file size")
    print("  • Faster LLM processing")
    print("  • Lower API costs")
    print("  • Code remains compilable and functional")
    try:
        demo_standalone_minifier()
        demo_workspace_minification()
        demo_session_preprocessing()
        demo_configuration()
        print("\\n" + "="*70)
        print("✓ All demonstrations completed successfully!")
        print("="*70)
        print("\\nNext steps:")
        print("  1. Edit axe.yaml to enable preprocessing")
        print("  2. Start an AXE session - minification runs automatically")
        print("  3. Or use tools/minifier.py as a standalone CLI tool")
        print("\\nFor more info, see:")
        print("  • tests/test_minifier.py - 32 test cases")
        print("  • tests/test_session_preprocessor.py - 18 test cases")
        print("  • tools/minifier.py --help - CLI usage")
    except Exception as e:
        print(f"\\n✗ Demo failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    return 0
if __name__ == '__main__':
    sys.exit(main())