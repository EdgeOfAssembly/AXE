#!/usr/bin/env python3
"""
llmprep - Prepare a codebase for LLM analysis

Generates documentation, code statistics, dependency graphs, and LLM-ready
context files for a software project.

Author: EdgeOfAssembly
Email: haxbox2000@gmail.com
License: GPLv3 / Commercial
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

__version__ = "1.0.0"

# Language categories for detection
C_LANGUAGES = {"C", "C++", "C/C++ Header", "Objective-C", "CUDA", "Assembly"}
PYTHON_LANGUAGES = {"Python"}

# Default exclusions for tree command
DEFAULT_EXCLUDES = "__pycache__|build|dist|node_modules|.git|*.o|*.so|*.a|*.pyc|.venv|venv|env"


def run_command(cmd: List[str], stdout_file: Optional[Path] = None,
                check: bool = False, quiet: bool = False) -> bool:
    """Run a command, optionally capturing stdout to a file."""
    try:
        if stdout_file:
            with open(stdout_file, "w") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.DEVNULL, check=check)
        elif quiet:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=check)
        else:
            subprocess.run(cmd, check=check)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_tool(name: str) -> bool:
    """Check if a tool is available in PATH."""
    return shutil.which(name) is not None


def parse_cloc_output(stats_file: Path) -> Dict[str, int]:
    """Parse cloc output to get lines of code per language.

    Args:
        stats_file: Path to the cloc output file.

    Returns:
        Dictionary mapping language names to lines of code.
    """
    lang_code_lines: Dict[str, int] = {}
    if not stats_file.exists() or stats_file.stat().st_size == 0:
        return lang_code_lines

    lines = stats_file.read_text().splitlines()
    in_table = False
    for line in lines:
        if "files" in line.lower() and "blank" in line and "comment" in line and "code" in line:
            in_table = True
            continue
        if in_table and (line.startswith("------") or line.startswith("SUM:")):
            continue
        if in_table:
            parts = [p for p in line.split() if p]
            if len(parts) >= 5:
                lang = " ".join(parts[:-4])
                try:
                    code = int(parts[-1])
                    lang_code_lines[lang] = code
                except ValueError:
                    # Ignore lines where the code count is not an integer (malformed cloc output)
                    pass
    return lang_code_lines


def generate_tree(project_dir: Path, output_file: Path, depth: int,
                  excludes: str, verbose: bool) -> bool:
    """Generate directory tree structure."""
    if verbose:
        print("Generating directory structure...")

    if check_tool("tree"):
        return run_command([
            "tree", "-L", str(depth), "--dirsfirst", "-I", excludes
        ], stdout_file=output_file)
    else:
        # Fallback: use find if tree not available
        if verbose:
            print("  (tree not found, using fallback)")
        try:
            result = []
            for root, dirs, files in os.walk(project_dir):
                # Apply depth limit
                rel_root = Path(root).relative_to(project_dir)
                if len(rel_root.parts) >= depth:
                    dirs[:] = []
                    continue
                # Apply exclusions
                exclude_patterns = excludes.split("|")
                dirs[:] = [d for d in dirs if not any(
                    d == p.replace("*", "") for p in exclude_patterns
                )]
                level = len(rel_root.parts)
                indent = "  " * level
                result.append(f"{indent}{rel_root.name or '.'}/")
                for f in sorted(files)[:20]:  # Limit files per dir
                    if not any(f.endswith(p.replace("*", "")) for p in exclude_patterns):
                        result.append(f"{indent}  {f}")
                if len(files) > 20:
                    result.append(f"{indent}  ... and {len(files) - 20} more files")
            output_file.write_text("\n".join(result))
            return True
        except Exception:
            return False


def generate_cloc(project_dir: Path, output_file: Path, verbose: bool) -> bool:
    """Generate code statistics with cloc."""
    if verbose:
        print("Generating code statistics...")

    if check_tool("cloc"):
        return run_command([
            "cloc", ".", "--exclude-dir=build,dist,.git,__pycache__,node_modules,.venv,venv"
        ], stdout_file=output_file)
    else:
        if verbose:
            print("  (cloc not found, skipping statistics)")
        output_file.write_text("cloc not available - install with: apt install cloc\n")
        return False


def run_doxygen(project_dir: Path, prep_dir: Path, verbose: bool) -> bool:
    """Run Doxygen for C/C++ documentation."""
    if not check_tool("doxygen"):
        if verbose:
            print("  (doxygen not found, skipping)")
        return False

    if verbose:
        print("Running Doxygen for C/C++ documentation...")

    doxyfile = project_dir / "Doxyfile"
    if not doxyfile.exists():
        run_command(["doxygen", "-g"], quiet=True)

    # Configure Doxygen for LLM-friendly output
    updates = {
        "PROJECT_NAME": f'"{project_dir.name}"',
        "OUTPUT_DIRECTORY": str(prep_dir / "doxygen_output"),
        "RECURSIVE": "YES",
        "EXTRACT_ALL": "YES",
        "EXTRACT_PRIVATE": "YES",
        "EXTRACT_STATIC": "YES",
        "HIDE_UNDOC_MEMBERS": "NO",
        "HAVE_DOT": "YES" if check_tool("dot") else "NO",
        "DOT_CLEANUP": "NO",
        "CALL_GRAPH": "YES",
        "CALLER_GRAPH": "YES",
        "DIRECTORY_GRAPH": "YES",
        "INCLUDE_GRAPH": "YES",
        "INCLUDED_BY_GRAPH": "YES",
        "COLLABORATION_GRAPH": "YES",
        "UML_LOOK": "YES",
        "DOT_IMAGE_FORMAT": "svg",
        "DOT_GRAPH_MAX_NODES": "200",
        "GENERATE_TREEVIEW": "YES",
        "SEARCHENGINE": "YES",
        "BUILTIN_STL_SUPPORT": "YES",
        "QUIET": "YES",
        "WARNINGS": "NO",
    }

    try:
        config_text = doxyfile.read_text()
        for key, value in updates.items():
            pattern = rf"^({key}\s*=).*"
            if re.search(pattern, config_text, re.MULTILINE):
                config_text = re.sub(pattern, rf"\1 {value}", config_text, flags=re.MULTILINE)
            else:
                config_text += f"{key:<30} = {value}\n"
        doxyfile.write_text(config_text)

        run_command(["doxygen", "Doxyfile"], quiet=not verbose)

        # Copy DOT files to prep directory
        dot_dir = prep_dir / "dot_graphs_doxygen"
        html_dir = prep_dir / "doxygen_output" / "html"
        if html_dir.exists():
            for dot_file in html_dir.glob("*.dot"):
                shutil.copy(dot_file, dot_dir / dot_file.name)
        return True
    except Exception as e:
        if verbose:
            print(f"  Doxygen failed: {e}")
        return False


def run_pyreverse(project_dir: Path, prep_dir: Path, verbose: bool) -> bool:
    """Run pyreverse for Python UML diagrams."""
    if not check_tool("pyreverse"):
        if verbose:
            print("  (pyreverse not found - install with: pip install pylint)")
        return False

    if verbose:
        print("Running pyreverse for Python class diagrams...")

    try:
        run_command(["pyreverse", "-o", "dot", "."], quiet=True, check=True)
        dot_dir = prep_dir / "dot_graphs_pyreverse"
        for pattern in ["packages.dot", "classes.dot"]:
            p = Path(pattern)
            if p.exists():
                shutil.move(str(p), dot_dir / p.name)
        return True
    except Exception as e:
        if verbose:
            print(f"  Pyreverse failed (common if no package structure): {e}")
        return False


def run_ctags(project_dir: Path, prep_dir: Path, verbose: bool) -> bool:
    """Generate ctags for symbol navigation."""
    ctags_cmd = "ctags" if check_tool("ctags") else (
        "universal-ctags" if check_tool("universal-ctags") else None
    )
    if not ctags_cmd:
        if verbose:
            print("  (ctags not found, skipping)")
        return False

    if verbose:
        print("Generating ctags...")

    try:
        run_command([ctags_cmd, "-R"], quiet=True)
        tags_file = Path("tags")
        if tags_file.exists():
            shutil.move(str(tags_file), prep_dir / "tags")
        return True
    except Exception:
        return False


def generate_system_prompt(project_name: str, languages: List[str]) -> str:
    """Generate an LLM system prompt tailored to the project."""
    lang_str = ", ".join(languages) if languages else "general programming"
    return f"""You are analyzing the "{project_name}" codebase.

Primary languages: {lang_str}

Guidelines:
- Provide clear, concise explanations
- Reference specific files and functions when discussing code
- Suggest improvements that follow project conventions
- Consider security, performance, and maintainability

When modifying code:
- Match existing style and conventions
- Add appropriate comments for complex logic
- Consider edge cases and error handling
- Maintain backward compatibility when possible
"""


def generate_guidance(project_name: str, languages: List[str]) -> str:
    """Generate project guidance documentation."""
    sections = [f"# Project Guidance for {project_name}\n"]

    if any(lang in C_LANGUAGES for lang in languages):
        sections.append("""
## C/C++ Best Practices
- Use RAII and smart pointers
- Prefer modern C++ features (C++17/20/23)
- Enable warnings: -Wall -Wextra -Wpedantic
- Use sanitizers in debug builds: -fsanitize=address,undefined
""")

    if any(lang in PYTHON_LANGUAGES for lang in languages):
        sections.append("""
## Python Best Practices
- Follow PEP 8 style guide
- Use type hints for function signatures
- Write docstrings (Google or NumPy style)
- Use virtual environments
""")

    sections.append("""
## General Guidelines
- Write tests for new functionality
- Keep functions small and focused
- Document non-obvious code
- Profile before optimizing
""")

    return "\n".join(sections)


def generate_overview(prep_dir: Path, project_name: str, lang_lines: Dict[str, int],
                      has_doxygen: bool, has_pyreverse: bool, has_ctags: bool) -> None:
    """Generate the main overview markdown file."""
    overview_path = prep_dir / "codebase_overview.md"

    with open(overview_path, "w") as f:
        f.write(f"# LLM-Ready Codebase Overview — {datetime.date.today()}\n\n")
        f.write(f"**Project:** {project_name}\n\n")

        # Directory structure
        structure_file = prep_dir / "codebase_structure.txt"
        if structure_file.exists():
            f.write("## Directory Structure\n\n```text\n")
            f.write(structure_file.read_text())
            f.write("```\n\n")

        # Code statistics
        stats_file = prep_dir / "codebase_stats.txt"
        if stats_file.exists():
            f.write("## Code Statistics\n\n```text\n")
            f.write(stats_file.read_text())
            f.write("```\n\n")

        # Doxygen
        if has_doxygen:
            f.write("## Doxygen Documentation (C/C++)\n\n")
            f.write("- Browse: `llm_prep/doxygen_output/html/index.html`\n")
            dot_dir = prep_dir / "dot_graphs_doxygen"
            if dot_dir.exists() and any(dot_dir.iterdir()):
                f.write("- DOT graphs for LLM context:\n")
                for dot in sorted(dot_dir.iterdir()):
                    size_kb = dot.stat().st_size // 1024
                    f.write(f"  - `{dot.name}` ({size_kb} KB)\n")
            f.write("\n")

        # Pyreverse
        if has_pyreverse:
            f.write("## Python Class Diagrams (pyreverse)\n\n")
            dot_dir = prep_dir / "dot_graphs_pyreverse"
            if dot_dir.exists():
                for dot in sorted(dot_dir.iterdir()):
                    f.write(f"- `{dot.name}`\n")
            f.write("\n")

        # Ctags
        if has_ctags:
            f.write("## Symbol Index\n\n")
            f.write("- `llm_prep/tags` - ctags file for symbol navigation\n\n")

        # Generated files
        f.write("## LLM Context Files\n\n")
        f.write("- `llm_system_prompt.md` - System prompt for LLM sessions\n")
        f.write("- `project_guidance.md` - Best practices and guidelines\n\n")

        # Usage instructions
        f.write("## How to Use\n\n")
        f.write("1. Copy this file as initial context for your LLM\n")
        f.write("2. Paste relevant DOT graphs for architecture questions\n")
        f.write("3. Reference specific files when asking about code\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Prepare a codebase for LLM analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  llmprep .
  
  # Analyze a specific project
  llmprep /path/to/project
  
  # Custom output directory (created inside project)
  llmprep /path/to/project -o my_analysis
  
  # Skip heavy processing
  llmprep . --no-doxygen --no-pyreverse
  
  # Quiet mode
  llmprep . -q
"""
    )

    parser.add_argument("project_dir", nargs="?", default=".",
                        help="Project directory to analyze (default: current directory)")
    parser.add_argument("-o", "--output", default="llm_prep",
                        help="Output directory name (default: llm_prep)")
    parser.add_argument("-d", "--depth", type=int, default=4,
                        help="Directory tree depth (default: 4)")
    parser.add_argument("--exclude", default=DEFAULT_EXCLUDES,
                        help=f"Tree exclusion pattern (default: {DEFAULT_EXCLUDES})")
    parser.add_argument("--no-doxygen", action="store_true",
                        help="Skip Doxygen documentation")
    parser.add_argument("--no-pyreverse", action="store_true",
                        help="Skip pyreverse diagrams")
    parser.add_argument("--no-ctags", action="store_true",
                        help="Skip ctags generation")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress progress output")
    parser.add_argument("-v", "--version", action="version",
                        version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # Resolve project directory
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        print(f"Error: {project_dir} is not a directory.", file=sys.stderr)
        return 1

    verbose = not args.quiet

    if verbose:
        print(f"Analyzing codebase: {project_dir.name}")

    # Change to project directory
    original_dir = os.getcwd()
    os.chdir(project_dir)

    try:
        # Setup output directories
        prep_dir = Path(args.output)
        prep_dir.mkdir(exist_ok=True)
        (prep_dir / "dot_graphs_doxygen").mkdir(exist_ok=True)
        (prep_dir / "dot_graphs_pyreverse").mkdir(exist_ok=True)

        # Generate directory tree
        generate_tree(project_dir, prep_dir / "codebase_structure.txt",
                      args.depth, args.exclude, verbose)

        # Generate code statistics
        generate_cloc(project_dir, prep_dir / "codebase_stats.txt", verbose)

        # Parse language statistics
        lang_lines = parse_cloc_output(prep_dir / "codebase_stats.txt")
        primary_langs = [lang for lang, lines in sorted(
            lang_lines.items(), key=lambda x: x[1], reverse=True
        ) if lines > 50]

        if verbose and primary_langs:
            print(f"Detected languages: {', '.join(primary_langs)}")

        # Determine what to run
        has_c = sum(lang_lines.get(lang, 0) for lang in C_LANGUAGES) > 100
        has_python = sum(lang_lines.get(lang, 0) for lang in PYTHON_LANGUAGES) > 100

        # Run optional tools
        ran_doxygen = False
        ran_pyreverse = False
        ran_ctags = False

        if has_c and not args.no_doxygen:
            ran_doxygen = run_doxygen(project_dir, prep_dir, verbose)

        if has_python and not args.no_pyreverse:
            ran_pyreverse = run_pyreverse(project_dir, prep_dir, verbose)

        if not args.no_ctags:
            ran_ctags = run_ctags(project_dir, prep_dir, verbose)

        # Generate LLM context files
        if verbose:
            print("Generating LLM context files...")

        prompt = generate_system_prompt(project_dir.name, primary_langs)
        (prep_dir / "llm_system_prompt.md").write_text(prompt)

        guidance = generate_guidance(project_dir.name, primary_langs)
        (prep_dir / "project_guidance.md").write_text(guidance)

        # Generate overview
        generate_overview(prep_dir, project_dir.name, lang_lines,
                          ran_doxygen, ran_pyreverse, ran_ctags)

        if verbose:
            print(f"\nDone! Output in: {prep_dir}/")
            print(f"Start with: {prep_dir}/codebase_overview.md")

        return 0

    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    sys.exit(main())
