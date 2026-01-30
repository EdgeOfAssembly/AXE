#!/usr/bin/env python3
"""
Source Code Minifier for AXE
Minifies C, C++, Python, and Assembly source code to reduce token usage
when feeding code to LLMs while preserving compilability.
Features:
- Remove comments and docstrings (configurable)
- Strip whitespace and blank lines
- Preserve Python indentation
- Support recursive directory processing
- Language detection via guesslang or file extension
- Exclude common directories (tests, __pycache__, .git, venv, etc.)
Author: EdgeOfAssembly
License: GPLv3 / Commercial
"""
import os
import re
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import tokenize
import logging
__version__ = "1.0.0"
# Try to import guesslang for language detection
try:
    from guesslang import Guess
    HAS_GUESSLANG = True
except ImportError:
    HAS_GUESSLANG = False
# Supported file extensions
SUPPORTED_EXTS = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx', '.py', '.asm', '.s', '.S']
# Default directories to exclude
DEFAULT_EXCLUDE_DIRS = {
    'tests', '__pycache__', '.git', 'venv', '.venv', 'env',
    'node_modules', 'build', 'dist', '.pytest_cache', '.tox',
    'eggs', '.eggs', 'htmlcov', '.mypy_cache', '.ruff_cache'
}
# Set up logging
logger = logging.getLogger(__name__)
def comment_remover_c_cpp(text: str) -> str:
    """
    Remove C/C++ comments from source code.
    Preserves strings and character literals.
    Args:
        text: Source code text
    Returns:
        Text with comments removed
    """
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "  # Replace comment with space to preserve line structure
        else:
            return s  # Keep string/char literals
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)
def minify_c_cpp(code: str, keep_comments: bool = False) -> str:
    """
    Minify C/C++ source code.
    Args:
        code: Source code to minify
        keep_comments: If True, preserve comments
    Returns:
        Minified code
    """
    if not keep_comments:
        code = comment_remover_c_cpp(code)
    # Strip lines and remove empty ones
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    return '\n'.join(lines)
def remove_comments_and_docstrings(source: str) -> str:
    """
    Remove Python comments and docstrings from source code.
    Preserves regular strings and code structure.
    Args:
        source: Python source code
    Returns:
        Code with comments and docstrings removed
    """
    io_obj = StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    try:
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            # Skip comments
            if token_type == tokenize.COMMENT:
                pass
            # Skip docstrings (strings after INDENT or NEWLINE)
            elif token_type == tokenize.STRING:
                if prev_toktype != tokenize.INDENT and prev_toktype != tokenize.NEWLINE and start_col > 0:
                    out += token_string
            else:
                out += token_string
            prev_toktype = token_type
            last_col = end_col
            last_lineno = end_line
    except tokenize.TokenError:
        # If tokenization fails, return original source
        return source
    return out
def minify_python(code: str, keep_comments: bool = False) -> str:
    """
    Minify Python source code.
    IMPORTANT: Preserves indentation to maintain Python syntax correctness.
    Args:
        code: Source code to minify
        keep_comments: If True, preserve comments
    Returns:
        Minified code with proper indentation
    """
    if not keep_comments:
        minified = remove_comments_and_docstrings(code)
    else:
        minified = code
    # Remove empty lines but preserve indentation
    lines = [line.rstrip() for line in minified.splitlines() if line.strip()]
    return '\n'.join(lines)
def minify_asm(code: str, keep_comments: bool = False) -> str:
    """
    Minify Assembly source code.
    Args:
        code: Assembly source code
        keep_comments: If True, preserve comments
    Returns:
        Minified assembly code
    """
    lines = []
    for line in code.splitlines():
        if not keep_comments:
            # Remove semicolon comments (most common in x86 assembly)
            line = re.sub(r';.*', '', line).strip()
        else:
            line = line.strip()
        if line:
            lines.append(line)
    return '\n'.join(lines)
def detect_language(file_path: str, content: str) -> Optional[str]:
    """
    Detect the programming language of a file.
    Uses guesslang if available, otherwise falls back to extension-based detection.
    Args:
        file_path: Path to the file
        content: File content
    Returns:
        Language identifier ('c_cpp', 'python', 'asm') or None if unsupported
    """
    ext = os.path.splitext(file_path)[1].lower()
    # Extension-based detection (fallback)
    if ext in ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']:
        return 'c_cpp'
    elif ext in ['.py']:
        return 'python'
    elif ext in ['.asm', '.s', '.S']:
        return 'asm'
    # Use guesslang if available and extension didn't match
    if HAS_GUESSLANG:
        try:
            guess = Guess()
            language = guess.language_name(content)
            if language in ['C', 'C++', 'C#', 'Objective-C']:
                return 'c_cpp'
            elif language == 'Python':
                return 'python'
            elif language in ['Assembly', 'Assembly (x86)']:
                return 'asm'
        except Exception as e:
            logger.debug(f"Guesslang detection failed for {file_path}: {e}")
    return None
def collect_files(inputs: List[str], recursive: bool = False,
                  exclude_dirs: Optional[Set[str]] = None) -> List[Tuple[str, str]]:
    """
    Collect all supported source files from input paths.
    Args:
        inputs: List of file or directory paths
        recursive: If True, recurse into subdirectories
        exclude_dirs: Set of directory names to exclude
    Returns:
        List of tuples (full_path, relative_path)
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    all_files = []
    for inp in inputs:
        inp = os.path.normpath(inp)
        if os.path.isfile(inp):
            ext = os.path.splitext(inp)[1].lower()
            if ext in SUPPORTED_EXTS:
                rel_path = inp.lstrip(os.path.sep)
                all_files.append((inp, rel_path))
        elif os.path.isdir(inp):
            base_name = os.path.basename(inp)
            if recursive:
                for root, dirs, files in os.walk(inp):
                    # Exclude directories
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in SUPPORTED_EXTS:
                            full_path = os.path.join(root, file)
                            inner_rel = os.path.relpath(full_path, inp)
                            rel_path = os.path.join(base_name, inner_rel).lstrip(os.path.sep)
                            all_files.append((full_path, rel_path))
            else:
                for file in os.listdir(inp):
                    full_path = os.path.join(inp, file)
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(file)[1].lower()
                        if ext in SUPPORTED_EXTS:
                            inner_rel = file
                            rel_path = os.path.join(base_name, inner_rel).lstrip(os.path.sep)
                            all_files.append((full_path, rel_path))
    return all_files
class Minifier:
    """
    Source code minifier for AXE.
    Minifies C, C++, Python, and Assembly source code to reduce token usage
    while preserving compilability.
    """
    def __init__(self, exclude_dirs: Optional[Set[str]] = None):
        """
        Initialize the minifier.
        Args:
            exclude_dirs: Set of directory names to exclude from processing
        """
        self.exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
        self.stats = {
            'files_processed': 0,
            'bytes_original': 0,
            'bytes_minified': 0
        }
    def minify_file(self, file_path: str, keep_comments: bool = True) -> str:
        """
        Minify a single source file.
        Args:
            file_path: Path to the file to minify
            keep_comments: If True, preserve comments (default for AXE)
        Returns:
            Minified source code
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        language = detect_language(file_path, content)
        if language == 'c_cpp':
            minified = minify_c_cpp(content, keep_comments)
        elif language == 'python':
            minified = minify_python(content, keep_comments)
        elif language == 'asm':
            minified = minify_asm(content, keep_comments)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        # Update stats
        self.stats['files_processed'] += 1
        self.stats['bytes_original'] += len(content)
        self.stats['bytes_minified'] += len(minified)
        return minified
    def minify_directory(self, dir_path: str, recursive: bool = True,
                        keep_comments: bool = True,
                        exclude_dirs: Optional[Set[str]] = None) -> Dict[str, str]:
        """
        Minify all supported files in a directory.
        Args:
            dir_path: Path to directory
            recursive: If True, recurse into subdirectories
            keep_comments: If True, preserve comments
            exclude_dirs: Additional directories to exclude
        Returns:
            Dictionary mapping file paths to minified content
        """
        exclude = self.exclude_dirs.copy()
        if exclude_dirs:
            exclude.update(exclude_dirs)
        files = collect_files([dir_path], recursive=recursive, exclude_dirs=exclude)
        results = {}
        for full_path, rel_path in files:
            try:
                minified = self.minify_file(full_path, keep_comments)
                results[full_path] = minified
                logger.info(f"Minified: {rel_path}")
            except Exception as e:
                logger.warning(f"Failed to minify {rel_path}: {e}")
        return results
    def minify_workspace(self, workspace_path: str, keep_comments: bool = True,
                        output_mode: str = 'in_place',
                        output_dir: Optional[str] = None) -> Dict[str, int]:
        """
        Minify entire workspace.
        Args:
            workspace_path: Root directory of workspace
            keep_comments: If True, preserve comments
            output_mode: 'in_place' or 'separate_dir'
            output_dir: Output directory (only used if output_mode is 'separate_dir')
        Returns:
            Statistics dictionary with keys:
            - files_processed: Number of files minified
            - bytes_saved: Bytes saved by minification
            - bytes_original: Original total size
            - bytes_minified: Minified total size
        """
        self.stats = {
            'files_processed': 0,
            'bytes_original': 0,
            'bytes_minified': 0
        }
        results = self.minify_directory(workspace_path, recursive=True, keep_comments=keep_comments)
        # Write results
        if output_mode == 'in_place':
            for file_path, minified_content in results.items():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(minified_content)
        elif output_mode == 'separate_dir':
            if not output_dir:
                raise ValueError("output_dir required when output_mode is 'separate_dir'")
            os.makedirs(output_dir, exist_ok=True)
            for file_path, minified_content in results.items():
                # Compute relative path from workspace_path
                rel_path = os.path.relpath(file_path, workspace_path)
                output_path = os.path.join(output_dir, rel_path)
                # Create parent directories
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(minified_content)
        return {
            'files_processed': self.stats['files_processed'],
            'bytes_saved': self.stats['bytes_original'] - self.stats['bytes_minified'],
            'bytes_original': self.stats['bytes_original'],
            'bytes_minified': self.stats['bytes_minified']
        }
def minify_file(file_path: str, keep_comments: bool = True) -> str:
    """
    Convenience function to minify a single file.
    Args:
        file_path: Path to file
        keep_comments: If True, preserve comments
    Returns:
        Minified source code
    """
    minifier = Minifier()
    return minifier.minify_file(file_path, keep_comments)
def minify_directory(dir_path: str, recursive: bool = True,
                    keep_comments: bool = True,
                    exclude_dirs: Optional[Set[str]] = None) -> Dict[str, str]:
    """
    Convenience function to minify a directory.
    Args:
        dir_path: Path to directory
        recursive: If True, recurse into subdirectories
        keep_comments: If True, preserve comments
        exclude_dirs: Set of directory names to exclude
    Returns:
        Dictionary mapping file paths to minified content
    """
    minifier = Minifier(exclude_dirs=exclude_dirs)
    return minifier.minify_directory(dir_path, recursive, keep_comments, exclude_dirs)
def main():
    """Command-line interface for minifier."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Minify source code to reduce token usage for LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('inputs', nargs='+',
                       help='Files or directories to minify')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Recursively process directories')
    parser.add_argument('--remove-comments', action='store_true',
                       help='Remove comments (default: keep comments)')
    parser.add_argument('-o', '--output',
                       help='Output directory (default: in-place modification)')
    parser.add_argument('--exclude', action='append',
                       help='Additional directories to exclude')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    args = parser.parse_args()
    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    # Build exclude set
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    if args.exclude:
        exclude_dirs.update(args.exclude)
    minifier = Minifier(exclude_dirs=exclude_dirs)
    keep_comments = not args.remove_comments
    # Collect files
    files = collect_files(args.inputs, recursive=args.recursive, exclude_dirs=exclude_dirs)
    if not files:
        print("No supported files found.")
        return 1
    print(f"Found {len(files)} file(s) to minify")
    # Process files
    for full_path, rel_path in files:
        try:
            minified = minifier.minify_file(full_path, keep_comments)
            if args.output:
                # Write to output directory
                output_path = os.path.join(args.output, rel_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(minified)
                print(f"Minified: {rel_path} -> {output_path}")
            else:
                # In-place modification
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(minified)
                print(f"Minified: {rel_path}")
        except Exception as e:
            print(f"Error minifying {rel_path}: {e}", file=sys.stderr)
    # Print stats
    bytes_saved = minifier.stats['bytes_original'] - minifier.stats['bytes_minified']
    reduction_pct = (bytes_saved / minifier.stats['bytes_original'] * 100) if minifier.stats['bytes_original'] > 0 else 0
    print(f"\nStatistics:")
    print(f"  Files processed: {minifier.stats['files_processed']}")
    print(f"  Original size: {minifier.stats['bytes_original']:,} bytes")
    print(f"  Minified size: {minifier.stats['bytes_minified']:,} bytes")
    print(f"  Bytes saved: {bytes_saved:,} bytes ({reduction_pct:.1f}% reduction)")
    return 0
if __name__ == '__main__':
    sys.exit(main())