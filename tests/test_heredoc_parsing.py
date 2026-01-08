#!/usr/bin/env python3
"""
Test suite for heredoc parsing in shell code blocks.

Tests that the parse_shell_codeblocks() function correctly handles
heredocs without splitting them into separate commands.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.xml_tool_parser import parse_shell_codeblocks, parse_all_tool_formats


def test_simple_heredoc():
    """Test simple heredoc without redirect."""
    print("Testing simple heredoc...")
    
    response = """```bash
cat << EOF
line 1
line 2
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    # Should be a single command, not split into multiple
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert 'cat << EOF' in cmd, "Should contain heredoc start"
    assert 'line 1' in cmd, "Should contain line 1"
    assert 'line 2' in cmd, "Should contain line 2"
    assert 'EOF' in cmd.split('\n')[-1], "Should contain closing EOF"
    
    print("  ✓ Simple heredoc parsed correctly")


def test_heredoc_with_redirect():
    """Test heredoc with redirect to file."""
    print("Testing heredoc with redirect...")
    
    response = """```bash
cat << EOF > output.txt
- bullet point
1. numbered item
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert 'cat << EOF > output.txt' in cmd, "Should contain heredoc with redirect"
    assert '- bullet point' in cmd, "Should contain bullet point"
    assert '1. numbered item' in cmd, "Should contain numbered item"
    
    print("  ✓ Heredoc with redirect parsed correctly")


def test_indented_heredoc():
    """Test heredoc with indented delimiter (<<-)."""
    print("Testing indented heredoc...")
    
    response = """```bash
cat <<- ENDMARKER
	indented content
	more content
ENDMARKER
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert '<<-' in cmd, "Should contain <<- operator"
    assert 'indented content' in cmd, "Should contain content"
    assert 'ENDMARKER' in cmd, "Should contain delimiter"
    
    print("  ✓ Indented heredoc parsed correctly")


def test_here_string():
    """Test here-string (<<<)."""
    print("Testing here-string...")
    
    response = """```bash
cat <<< "single line input"
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert '<<<' in cmd, "Should contain <<< operator"
    assert 'single line input' in cmd, "Should contain input"
    
    print("  ✓ Here-string parsed correctly")


def test_quoted_delimiter():
    """Test heredoc with quoted delimiter."""
    print("Testing quoted delimiter...")
    
    response = """```bash
cat << 'EOF'
line with $var
line with `command`
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert "cat << 'EOF'" in cmd, "Should contain quoted delimiter"
    assert 'line with $var' in cmd, "Should contain variable line"
    
    print("  ✓ Quoted delimiter parsed correctly")


def test_mixed_commands_with_heredoc():
    """Test multiple commands where only some have heredocs."""
    print("Testing mixed commands...")
    
    response = """```bash
echo "Starting"
cat << EOF
content line 1
content line 2
EOF
echo "Done"
```"""
    
    calls = parse_shell_codeblocks(response)
    
    # Should have 3 commands: echo, cat with heredoc, echo
    assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}"
    
    assert 'echo "Starting"' in calls[0]['params']['command']
    
    heredoc_cmd = calls[1]['params']['command']
    assert 'cat << EOF' in heredoc_cmd
    assert 'content line 1' in heredoc_cmd
    assert 'content line 2' in heredoc_cmd
    
    assert 'echo "Done"' in calls[2]['params']['command']
    
    print("  ✓ Mixed commands parsed correctly")


def test_heredoc_problem_statement_example():
    """Test the exact example from the problem statement."""
    print("Testing problem statement example...")
    
    response = """```bash
cat << EOF > /tmp/AXE/shared_notes.md
## Analysis Results
- Item 1
- Item 2
1. First step
2. Second step
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    # Should be ONE command, not 7 separate ones
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}: {[c['params']['command'] for c in calls]}"
    
    cmd = calls[0]['params']['command']
    assert 'cat << EOF > /tmp/AXE/shared_notes.md' in cmd
    assert '## Analysis Results' in cmd
    assert '- Item 1' in cmd
    assert '- Item 2' in cmd
    assert '1. First step' in cmd
    assert '2. Second step' in cmd
    assert 'EOF' in cmd.split('\n')[-1]
    
    print("  ✓ Problem statement example parsed correctly")


def test_multiline_without_heredoc():
    """Test that regular multi-line commands still work (regression test)."""
    print("Testing multi-line without heredoc (regression)...")
    
    response = """```bash
cd /tmp
ls -la
pwd
```"""
    
    calls = parse_shell_codeblocks(response)
    
    # Should still split into 3 separate commands
    assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}"
    assert calls[0]['params']['command'] == 'cd /tmp'
    assert calls[1]['params']['command'] == 'ls -la'
    assert calls[2]['params']['command'] == 'pwd'
    
    print("  ✓ Multi-line without heredoc still works")


def test_comments_and_empty_lines():
    """Test that comments and empty lines are still handled correctly."""
    print("Testing comments and empty lines...")
    
    response = """```bash
# This is a comment
echo "test"

# Another comment
cat << EOF
content
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    # Should have 2 commands (echo and cat), comments ignored
    assert len(calls) == 2, f"Expected 2 calls, got {len(calls)}"
    assert 'echo "test"' in calls[0]['params']['command']
    assert 'cat << EOF' in calls[1]['params']['command']
    
    print("  ✓ Comments and empty lines handled correctly")


def test_heredoc_with_special_chars():
    """Test heredoc with special characters that could trigger errors."""
    print("Testing heredoc with special characters...")
    
    response = """```bash
cat << 'MARKER' > file.md
- Item with dash
1. Item with number
|| logical OR
&& logical AND
| pipe character
> redirect
< input redirect
MARKER
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    # Verify all special characters are preserved
    assert '- Item with dash' in cmd
    assert '1. Item with number' in cmd
    assert '|| logical OR' in cmd
    assert '&& logical AND' in cmd
    assert '| pipe character' in cmd
    
    print("  ✓ Special characters in heredoc preserved")


def test_multiple_heredocs_in_sequence():
    """Test multiple heredoc commands in sequence."""
    print("Testing multiple heredocs...")
    
    response = """```bash
cat << EOF1 > file1.txt
Content 1
EOF1
cat << EOF2 > file2.txt
Content 2
EOF2
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 2, f"Expected 2 calls, got {len(calls)}"
    
    assert 'cat << EOF1' in calls[0]['params']['command']
    assert 'Content 1' in calls[0]['params']['command']
    
    assert 'cat << EOF2' in calls[1]['params']['command']
    assert 'Content 2' in calls[1]['params']['command']
    
    print("  ✓ Multiple heredocs parsed correctly")


def test_heredoc_in_different_formats():
    """Test that heredocs work in all shell code block formats."""
    print("Testing heredocs in different formats...")
    
    # Test ```shell format
    response1 = """```shell
cat << EOF
test content
EOF
```"""
    calls1 = parse_shell_codeblocks(response1)
    assert len(calls1) == 1
    assert 'test content' in calls1[0]['params']['command']
    
    # Test ```sh format
    response2 = """```sh
cat << EOF
test content
EOF
```"""
    calls2 = parse_shell_codeblocks(response2)
    assert len(calls2) == 1
    assert 'test content' in calls2[0]['params']['command']
    
    print("  ✓ Heredocs work in all formats")


def test_parse_all_tool_formats_integration():
    """Test that heredocs work through parse_all_tool_formats."""
    print("Testing integration with parse_all_tool_formats...")
    
    response = """Here's what I'll do:

```bash
cat << EOF > notes.md
- Task 1
- Task 2
EOF
```

Done!"""
    
    calls = parse_all_tool_formats(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'EXEC'
    
    cmd = calls[0]['params']['command']
    assert 'cat << EOF' in cmd
    assert '- Task 1' in cmd
    assert '- Task 2' in cmd
    
    print("  ✓ Integration test passed")


def test_heredoc_with_hyphenated_delimiter():
    """Test heredoc with hyphens in delimiter name."""
    print("Testing heredoc with hyphenated delimiter...")
    
    response = """```bash
cat << END-OF-FILE
Content here
END-OF-FILE
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert 'END-OF-FILE' in cmd
    assert 'Content here' in cmd
    
    print("  ✓ Hyphenated delimiter parsed correctly")


def test_heredoc_with_underscore_delimiter():
    """Test heredoc with underscores in delimiter name."""
    print("Testing heredoc with underscore delimiter...")
    
    response = """```bash
cat << _MARKER_
Content here
_MARKER_
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert '_MARKER_' in cmd
    assert 'Content here' in cmd
    
    print("  ✓ Underscore delimiter parsed correctly")


def test_heredoc_without_closing_delimiter():
    """Test heredoc without closing delimiter (malformed)."""
    print("Testing heredoc without closing delimiter...")
    
    response = """```bash
cat << EOF
line 1
line 2
```"""
    
    calls = parse_shell_codeblocks(response)
    
    # Should still parse as one command, including all content
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    assert 'cat << EOF' in cmd
    assert 'line 1' in cmd
    assert 'line 2' in cmd
    
    print("  ✓ Malformed heredoc handled gracefully")


def test_heredoc_with_similar_content():
    """Test heredoc where content contains text similar to delimiter."""
    print("Testing heredoc with similar content...")
    
    response = """```bash
cat << EOF
This line says EOF in the middle
But this is not the EOF delimiter
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    lines = cmd.split('\n')
    assert 'This line says EOF in the middle' in cmd
    assert 'But this is not the EOF delimiter' in cmd
    # The last line should be the actual delimiter
    assert lines[-1].strip() == 'EOF'
    
    print("  ✓ Heredoc with similar content parsed correctly")


def test_multiple_heredocs_different_delimiters():
    """Test multiple heredocs with different delimiter styles."""
    print("Testing multiple heredocs with different delimiters...")
    
    response = """```bash
cat << EOF1
Content 1
EOF1
cat <<- END_MARKER
Content 2
END_MARKER
cat << 'QUOTED'
Content 3
QUOTED
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}"
    
    assert 'EOF1' in calls[0]['params']['command']
    assert 'Content 1' in calls[0]['params']['command']
    
    assert 'END_MARKER' in calls[1]['params']['command']
    assert 'Content 2' in calls[1]['params']['command']
    
    assert 'QUOTED' in calls[2]['params']['command']
    assert 'Content 3' in calls[2]['params']['command']
    
    print("  ✓ Multiple heredocs with different delimiters parsed correctly")


def test_empty_heredoc():
    """Test heredoc with no content between delimiters."""
    print("Testing empty heredoc...")
    
    response = """```bash
cat << EOF
EOF
```"""
    
    calls = parse_shell_codeblocks(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    
    cmd = calls[0]['params']['command']
    lines = cmd.split('\n')
    assert len(lines) == 2  # Start and end delimiter only
    assert 'cat << EOF' in lines[0]
    assert lines[1].strip() == 'EOF'
    
    print("  ✓ Empty heredoc parsed correctly")


def main():
    """Run all tests."""
    print("="*70)
    print("HEREDOC PARSING TEST SUITE")
    print("="*70)
    
    try:
        test_simple_heredoc()
        test_heredoc_with_redirect()
        test_indented_heredoc()
        test_here_string()
        test_quoted_delimiter()
        test_mixed_commands_with_heredoc()
        test_heredoc_problem_statement_example()
        test_multiline_without_heredoc()
        test_comments_and_empty_lines()
        test_heredoc_with_special_chars()
        test_multiple_heredocs_in_sequence()
        test_heredoc_in_different_formats()
        test_parse_all_tool_formats_integration()
        
        # New edge case tests
        test_heredoc_with_hyphenated_delimiter()
        test_heredoc_with_underscore_delimiter()
        test_heredoc_without_closing_delimiter()
        test_heredoc_with_similar_content()
        test_multiple_heredocs_different_delimiters()
        test_empty_heredoc()
        
        print("\n" + "="*70)
        print("✅ ALL HEREDOC PARSING TESTS PASSED!")
        print("="*70)
        print("\nThe fix ensures that:")
        print("  • Heredocs are preserved as single commands")
        print("  • Content within heredocs is not split into separate commands")
        print("  • Special characters in heredoc content don't trigger errors")
        print("  • Regular multi-line commands still work correctly")
        print("  • Edge cases like missing delimiters are handled gracefully")
        print("  • Various delimiter formats (hyphens, underscores) are supported")
        print("="*70)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
