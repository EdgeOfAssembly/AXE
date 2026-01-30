#!/usr/bin/env python3
"""
Demo script showing the heredoc parsing fix in action.
This demonstrates that heredoc content is no longer incorrectly parsed as commands.
"""
import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axe import Config, ToolRunner
import tempfile
def demo_before_and_after():
    """Show what would have happened before vs after the fix."""
    print("="*70)
    print("HEREDOC PARSING FIX DEMONSTRATION")
    print("="*70)
    print()
    print("PROBLEM: Heredoc content was being parsed as commands")
    print("         causing false positive whitelist errors")
    print()
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        runner = ToolRunner(config, tmpdir)
        # Example 1: Markdown content
        print("-" * 70)
        print("Example 1: Heredoc with Markdown")
        print("-" * 70)
        cmd1 = """cat >> notes.md << 'EOF'
## Tasks
- Task 1: Implement feature
- Task 2: Write tests
### Priorities:
1. Error handling
2. Documentation
---
EOF"""
        print(f"Command:\n{cmd1}\n")
        commands = runner._extract_commands_from_shell(cmd1)
        print(f"Commands extracted: {commands}")
        allowed, reason = runner.is_tool_allowed(cmd1)
        print(f"Allowed: {allowed}")
        print(f"Reason: {reason}")
        if allowed:
            print("✅ WORKS! No false positives for '-', '1.', '2.', '---'")
        else:
            print(f"❌ BLOCKED: {reason}")
        # Example 2: Content with operators
        print("\n" + "-" * 70)
        print("Example 2: Heredoc with Shell Operators in Content")
        print("-" * 70)
        cmd2 = """cat << 'EOF'
Line with pipe | character
Line with && operator
Line with || operator
Line with ; semicolon
EOF"""
        print(f"Command:\n{cmd2}\n")
        commands2 = runner._extract_commands_from_shell(cmd2)
        print(f"Commands extracted: {commands2}")
        allowed2, reason2 = runner.is_tool_allowed(cmd2)
        print(f"Allowed: {allowed2}")
        print(f"Reason: {reason2}")
        if allowed2:
            print("✅ WORKS! Operators in content don't cause false splits")
        else:
            print(f"❌ BLOCKED: {reason2}")
        # Example 3: Heredoc with pipe after
        print("\n" + "-" * 70)
        print("Example 3: Heredoc with Pipe (should parse both commands)")
        print("-" * 70)
        cmd3 = """cat << EOF | grep test
line 1
test line 2
line 3
EOF"""
        print(f"Command:\n{cmd3}\n")
        commands3 = runner._extract_commands_from_shell(cmd3)
        print(f"Commands extracted: {commands3}")
        allowed3, reason3 = runner.is_tool_allowed(cmd3)
        print(f"Allowed: {allowed3}")
        print(f"Reason: {reason3}")
        if allowed3 and 'cat' in commands3 and 'grep' in commands3:
            print("✅ WORKS! Both 'cat' and 'grep' correctly identified")
        else:
            print(f"❌ ISSUE: Expected ['cat', 'grep'], got {commands3}")
        print("\n" + "="*70)
        print("DEMONSTRATION COMPLETE")
        print("="*70)
        print()
        print("Summary:")
        print("  - Heredoc content is stripped before parsing operators")
        print("  - No false positives from markdown/code content")
        print("  - Operators after heredoc marker still work correctly")
        print("  - All existing shell features remain functional")
if __name__ == '__main__':
    demo_before_and_after()