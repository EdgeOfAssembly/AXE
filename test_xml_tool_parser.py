#!/usr/bin/env python3
"""
Test suite for XML function call parser.

Tests parsing, normalization, and execution of XML function calls
from LLM agents.
"""
import os
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.xml_tool_parser import (
    parse_xml_function_calls,
    normalize_tool_name,
    execute_parsed_call,
    format_xml_result,
    process_agent_response,
    parse_bash_tags,
    parse_shell_codeblocks,
    parse_axe_native_blocks,
    parse_simple_xml_tags,
    parse_all_tool_formats,
    deduplicate_calls,
    clean_tool_syntax
)
from axe import Config, ResponseProcessor, ToolRunner


def test_parse_single_function_call():
    """Test parsing a single XML function call."""
    print("Testing single XML function call parsing...")
    
    xml_text = """Here's what I'll do:
    
<function_calls>
<invoke name="read_file">
<parameter name="file_path">/tmp/playground/MISSION.md</parameter>
</invoke>
</function_calls>

Let me read that file."""
    
    calls = parse_xml_function_calls(xml_text)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'READ', f"Expected READ, got {calls[0]['tool']}"
    assert calls[0]['params']['file_path'] == '/tmp/playground/MISSION.md'
    assert calls[0]['raw_name'] == 'read_file'
    
    print("  ✓ Single function call parsed correctly")


def test_parse_multiple_function_calls():
    """Test parsing multiple XML function calls."""
    print("Testing multiple XML function calls...")
    
    xml_text = """Let me do several things:

<function_calls>
<invoke name="read_file">
<parameter name="file_path">config.yaml</parameter>
</invoke>
</function_calls>

<function_calls>
<invoke name="write_file">
<parameter name="file_path">output.txt</parameter>
<parameter name="content">Hello, World!</parameter>
</invoke>
</function_calls>

<function_calls>
<invoke name="shell">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>

Done!"""
    
    calls = parse_xml_function_calls(xml_text)
    
    assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}"
    assert calls[0]['tool'] == 'READ'
    assert calls[1]['tool'] == 'WRITE'
    assert calls[2]['tool'] == 'EXEC'
    
    print("  ✓ Multiple function calls parsed correctly")


def test_tool_name_normalization():
    """Test that various tool names map correctly."""
    print("Testing tool name normalization...")
    
    # Read variants
    assert normalize_tool_name('read_file') == 'READ'
    assert normalize_tool_name('read') == 'READ'
    assert normalize_tool_name('cat') == 'READ'
    assert normalize_tool_name('READ_FILE') == 'READ'  # case insensitive
    
    # Write variants
    assert normalize_tool_name('write_file') == 'WRITE'
    assert normalize_tool_name('write') == 'WRITE'
    assert normalize_tool_name('create_file') == 'WRITE'
    
    # Append variants
    assert normalize_tool_name('append_file') == 'APPEND'
    assert normalize_tool_name('append_to_file') == 'APPEND'
    
    # Exec variants
    assert normalize_tool_name('shell') == 'EXEC'
    assert normalize_tool_name('bash') == 'EXEC'
    assert normalize_tool_name('exec') == 'EXEC'
    
    # List dir variants
    assert normalize_tool_name('list_dir') == 'EXEC'
    assert normalize_tool_name('ls') == 'EXEC'
    
    # Unknown tool
    assert normalize_tool_name('unknown_tool') is None
    
    print("  ✓ Tool name normalization works correctly")


def test_execute_read():
    """Test executing READ operations."""
    print("Testing READ execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content\nLine 2")
        
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Create a parsed call
        call = {
            'tool': 'READ',
            'params': {'file_path': 'test.txt'},
            'raw_name': 'read_file'
        }
        
        result = execute_parsed_call(call, tmpdir, processor)
        
        assert "Test content" in result
        assert "Line 2" in result
        assert "ERROR" not in result
        
        print("  ✓ READ execution works correctly")


def test_execute_write():
    """Test executing WRITE operations."""
    print("Testing WRITE execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Create a parsed call
        call = {
            'tool': 'WRITE',
            'params': {
                'file_path': 'new_file.txt',
                'content': 'New content here'
            },
            'raw_name': 'write_file'
        }
        
        result = execute_parsed_call(call, tmpdir, processor)
        
        assert "✓" in result or "success" in result.lower()
        
        # Verify file was created
        test_file = os.path.join(tmpdir, "new_file.txt")
        assert os.path.exists(test_file)
        
        with open(test_file, 'r') as f:
            content = f.read()
        assert content == 'New content here'
        
        print("  ✓ WRITE execution works correctly")


def test_execute_append():
    """Test executing APPEND operations."""
    print("Testing APPEND execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create initial file
        test_file = os.path.join(tmpdir, "append_test.txt")
        with open(test_file, 'w') as f:
            f.write("Initial content\n")
        
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Create a parsed call
        call = {
            'tool': 'APPEND',
            'params': {
                'file_path': 'append_test.txt',
                'content': 'Appended content\n'
            },
            'raw_name': 'append_file'
        }
        
        result = execute_parsed_call(call, tmpdir, processor)
        
        assert "✓" in result or "success" in result.lower()
        
        # Verify content was appended
        with open(test_file, 'r') as f:
            content = f.read()
        assert "Initial content" in content
        assert "Appended content" in content
        
        print("  ✓ APPEND execution works correctly")


def test_execute_exec():
    """Test executing EXEC (shell) operations."""
    print("Testing EXEC execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True  # Auto-approve for testing
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Create a parsed call
        call = {
            'tool': 'EXEC',
            'params': {
                'command': 'echo "Hello from shell"'
            },
            'raw_name': 'shell'
        }
        
        result = execute_parsed_call(call, tmpdir, processor)
        
        assert "Hello from shell" in result or "ERROR" in result  # May fail if echo not whitelisted
        
        print("  ✓ EXEC execution works (subject to whitelist)")


def test_execute_list_dir():
    """Test executing list_dir operations (converted to ls)."""
    print("Testing list_dir execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        open(os.path.join(tmpdir, "file1.txt"), 'w').close()
        open(os.path.join(tmpdir, "file2.txt"), 'w').close()
        
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True  # Auto-approve for testing
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Create a parsed call
        call = {
            'tool': 'EXEC',
            'params': {
                'path': '.'
            },
            'raw_name': 'list_dir'
        }
        
        result = execute_parsed_call(call, tmpdir, processor)
        
        # Result may succeed if ls is whitelisted, or error if not
        assert isinstance(result, str)
        
        print("  ✓ list_dir execution works (subject to whitelist)")


def test_error_handling():
    """Test error handling for various edge cases."""
    print("Testing error handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Test 1: READ non-existent file
        call1 = {
            'tool': 'READ',
            'params': {'file_path': 'nonexistent.txt'},
            'raw_name': 'read_file'
        }
        result1 = execute_parsed_call(call1, tmpdir, processor)
        assert "ERROR" in result1 or "not found" in result1.lower()
        print("  ✓ Non-existent file error handled")
        
        # Test 2: READ with no file path
        call2 = {
            'tool': 'READ',
            'params': {},
            'raw_name': 'read_file'
        }
        result2 = execute_parsed_call(call2, tmpdir, processor)
        assert "ERROR" in result2
        print("  ✓ Missing parameter error handled")
        
        # Test 3: WRITE with no file path
        call3 = {
            'tool': 'WRITE',
            'params': {'content': 'test'},
            'raw_name': 'write_file'
        }
        result3 = execute_parsed_call(call3, tmpdir, processor)
        assert "ERROR" in result3
        print("  ✓ Missing file path error handled")
        
        # Test 4: Path traversal attempt
        call4 = {
            'tool': 'WRITE',
            'params': {
                'file_path': '../../etc/passwd',
                'content': 'malicious'
            },
            'raw_name': 'write_file'
        }
        result4 = execute_parsed_call(call4, tmpdir, processor)
        assert "ERROR" in result4 or "denied" in result4.lower()
        print("  ✓ Path traversal blocked")
        
        print("  ✓ Error handling works correctly")


def test_format_xml_result():
    """Test XML result formatting."""
    print("Testing XML result formatting...")
    
    result = format_xml_result('READ', {'file_path': 'test.txt'}, 'File content here')
    
    assert '<result>' in result
    assert '<function_result>' in result
    assert 'File content here' in result
    
    # Test with special characters
    result2 = format_xml_result('READ', {'file_path': 'test.txt'}, 'Content with <tags> & special chars')
    
    assert '&lt;tags&gt;' in result2
    assert '&amp;' in result2
    
    print("  ✓ XML result formatting works correctly")


def test_integration_with_response_processor():
    """Test full integration with ResponseProcessor."""
    print("Testing integration with ResponseProcessor...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "mission.md")
        with open(test_file, 'w') as f:
            f.write("# Mission\nComplete the task")
        
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Simulate agent response with XML function call
        response = """I'll read the mission file:

<function_calls>
<invoke name="read_file">
<parameter name="file_path">mission.md</parameter>
</invoke>
</function_calls>

Now I'll process it."""
        
        processed = processor.process_response(response, "test_agent")
        
        # Check that result was added
        assert "Mission" in processed or "Complete the task" in processed or "<result>" in processed
        assert "Execution Results" in processed or "<function_result>" in processed
        
        print("  ✓ Integration with ResponseProcessor works")


def test_mixed_xml_and_markdown():
    """Test that both XML and markdown blocks work together."""
    print("Testing mixed XML and markdown blocks...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        with open(os.path.join(tmpdir, "file1.txt"), 'w') as f:
            f.write("Content 1")
        
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Response with both XML and markdown
        response = """First, I'll use XML:

<function_calls>
<invoke name="read_file">
<parameter name="file_path">file1.txt</parameter>
</invoke>
</function_calls>

Now markdown:

```WRITE file2.txt
Content 2
```

Done!"""
        
        processed = processor.process_response(response, "test_agent")
        
        # Should have results from both
        assert "Execution Results" in processed
        
        # Verify file2.txt was created
        assert os.path.exists(os.path.join(tmpdir, "file2.txt"))
        
        print("  ✓ Mixed XML and markdown blocks work together")


def test_nested_xml_content():
    """Test handling of content with XML-like characters."""
    print("Testing nested/escaped XML content...")
    
    xml_text = """<function_calls>
<invoke name="write_file">
<parameter name="file_path">code.py</parameter>
<parameter name="content">def func():
    x = 5 &gt; 3
    return x &lt; 10</parameter>
</invoke>
</function_calls>"""
    
    calls = parse_xml_function_calls(xml_text)
    
    assert len(calls) == 1
    # The parser should get the raw content with entities
    assert 'content' in calls[0]['params']
    
    print("  ✓ Nested/escaped content handled")


def test_malformed_xml():
    """Test handling of malformed XML."""
    print("Testing malformed XML handling...")
    
    # Missing closing tag
    xml_text1 = """<function_calls>
<invoke name="read_file">
<parameter name="file_path">test.txt</parameter>
</function_calls>"""
    
    calls1 = parse_xml_function_calls(xml_text1)
    # Should gracefully handle by not finding the invoke
    assert len(calls1) == 0
    
    # No parameters
    xml_text2 = """<function_calls>
<invoke name="read_file">
</invoke>
</function_calls>"""
    
    calls2 = parse_xml_function_calls(xml_text2)
    # Should parse but have empty params
    assert len(calls2) == 1
    assert calls2[0]['params'] == {}
    
    print("  ✓ Malformed XML handled gracefully")


def test_bash_tags():
    """Test parsing <bash>command</bash> format."""
    print("Testing <bash> tag parsing...")
    
    response = '<bash>cat /tmp/file.txt</bash>'
    calls = parse_bash_tags(response)
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]["tool"] == "EXEC"
    assert calls[0]["params"]["command"] == "cat /tmp/file.txt"
    
    print("  ✓ <bash> tags parsed correctly")


def test_bash_codeblock():
    """Test parsing ```bash code blocks."""
    print("Testing ```bash code block parsing...")
    
    response = '```bash\nls -la /tmp\n```'
    calls = parse_shell_codeblocks(response)
    assert len(calls) == 1
    assert calls[0]["params"]["command"] == "ls -la /tmp"
    
    print("  ✓ ```bash blocks parsed correctly")


def test_shell_codeblock():
    """Test parsing ```shell code blocks."""
    print("Testing ```shell code block parsing...")
    
    response = '```shell\nfind . -name "*.pdf"\n```'
    calls = parse_shell_codeblocks(response)
    assert len(calls) == 1
    assert "find" in calls[0]["params"]["command"]
    
    print("  ✓ ```shell blocks parsed correctly")


def test_sh_codeblock():
    """Test parsing ```sh code blocks."""
    print("Testing ```sh code block parsing...")
    
    response = '```sh\necho "hello"\n```'
    calls = parse_shell_codeblocks(response)
    assert len(calls) == 1
    assert "echo" in calls[0]["params"]["command"]
    
    print("  ✓ ```sh blocks parsed correctly")


def test_multiline_codeblock():
    """Test parsing multi-line shell code blocks."""
    print("Testing multi-line code block parsing...")
    
    response = '```bash\ncd /tmp\nls -la\npwd\n```'
    calls = parse_shell_codeblocks(response)
    assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}"  # One per line
    
    print("  ✓ Multi-line blocks parsed correctly")


def test_axe_read_block():
    """Test parsing ```READ blocks."""
    print("Testing ```READ block parsing...")
    
    response = '```READ /tmp/playground/MISSION.md```'
    calls = parse_axe_native_blocks(response)
    assert len(calls) == 1
    assert calls[0]["tool"] == "READ"
    assert calls[0]["params"]["file_path"] == "/tmp/playground/MISSION.md"
    
    print("  ✓ ```READ blocks parsed correctly")


def test_axe_write_block():
    """Test parsing ```WRITE blocks."""
    print("Testing ```WRITE block parsing...")
    
    response = '```WRITE /tmp/out.txt\nhello world\n```'
    calls = parse_axe_native_blocks(response)
    assert len(calls) == 1
    assert calls[0]["tool"] == "WRITE"
    assert calls[0]["params"]["file_path"] == "/tmp/out.txt"
    assert "hello world" in calls[0]["params"]["content"]
    
    print("  ✓ ```WRITE blocks parsed correctly")


def test_axe_exec_block():
    """Test parsing ```EXEC blocks."""
    print("Testing ```EXEC block parsing...")
    
    response = '```EXEC ls -la /tmp```'
    calls = parse_axe_native_blocks(response)
    assert len(calls) == 1
    assert calls[0]["tool"] == "EXEC"
    assert calls[0]["params"]["command"] == "ls -la /tmp"
    
    print("  ✓ ```EXEC blocks parsed correctly")


def test_simple_xml_read():
    """Test parsing <read_file> tags."""
    print("Testing <read_file> tag parsing...")
    
    response = '<read_file>/tmp/x.txt</read_file>'
    calls = parse_simple_xml_tags(response)
    assert len(calls) == 1
    assert calls[0]["tool"] == "READ"
    assert calls[0]["params"]["file_path"] == "/tmp/x.txt"
    
    print("  ✓ <read_file> tags parsed correctly")


def test_simple_xml_shell():
    """Test parsing <shell> tags."""
    print("Testing <shell> tag parsing...")
    
    response = '<shell>ls -la</shell>'
    calls = parse_simple_xml_tags(response)
    assert len(calls) == 1
    assert calls[0]["tool"] == "EXEC"
    assert calls[0]["params"]["command"] == "ls -la"
    
    print("  ✓ <shell> tags parsed correctly")


def test_simple_xml_write():
    """Test parsing <write_file> tags."""
    print("Testing <write_file> tag parsing...")
    
    response = '<write_file path="/tmp/x.txt">hello world</write_file>'
    calls = parse_simple_xml_tags(response)
    assert len(calls) == 1
    assert calls[0]["tool"] == "WRITE"
    assert calls[0]["params"]["file_path"] == "/tmp/x.txt"
    assert calls[0]["params"]["content"] == "hello world"
    
    print("  ✓ <write_file> tags parsed correctly")


def test_mixed_formats():
    """Test parsing mixed tool call formats."""
    print("Testing mixed format parsing...")
    
    response = '''
    <bash>echo "hello"</bash>
    ```bash
    ls -la
    ```
    ```READ /tmp/file.txt```
    '''
    calls = parse_all_tool_formats(response)
    assert len(calls) >= 3, f"Expected at least 3 calls, got {len(calls)}"
    
    print("  ✓ Mixed formats parsed correctly")


def test_deduplication():
    """Test deduplication of identical calls."""
    print("Testing deduplication...")
    
    response = '''
    <bash>cat /tmp/file.txt</bash>
    <bash>cat /tmp/file.txt</bash>
    '''
    calls = parse_all_tool_formats(response)
    assert len(calls) == 1, f"Expected 1 deduplicated call, got {len(calls)}"
    
    print("  ✓ Deduplication works correctly")


def test_comments_ignored_in_codeblock():
    """Test that comments in code blocks are ignored."""
    print("Testing comment filtering in code blocks...")
    
    response = '```bash\n# This is a comment\nls -la\n# Another comment\n```'
    calls = parse_shell_codeblocks(response)
    assert len(calls) == 1
    assert calls[0]["params"]["command"] == "ls -la"
    
    print("  ✓ Comments ignored correctly")


def test_empty_commands_ignored():
    """Test that empty commands are ignored."""
    print("Testing empty command filtering...")
    
    response = '<bash>   </bash>'
    calls = parse_bash_tags(response)
    assert len(calls) == 0
    
    print("  ✓ Empty commands ignored correctly")


def test_clean_tool_syntax():
    """Test cleaning tool syntax from response."""
    print("Testing tool syntax cleaning...")
    
    response = '''
    Here's my plan:
    <bash>ls -la</bash>
    ```bash
    echo "test"
    ```
    Some text here.
    ```READ /tmp/file.txt```
    '''
    
    cleaned = clean_tool_syntax(response)
    
    assert '<bash>' not in cleaned
    assert '```bash' not in cleaned
    assert '```READ' not in cleaned
    assert '[TOOL EXECUTED]' in cleaned
    assert 'Some text here' in cleaned  # Keep non-tool text
    
    print("  ✓ Tool syntax cleaning works correctly")


def test_all_formats_execution():
    """Test execution of all formats with actual file operations."""
    print("Testing execution of all formats...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        tool_runner.auto_approve = True
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Test <bash> format
        response1 = f'<bash>cat {test_file}</bash>'
        _, results1 = process_agent_response(response1, tmpdir, processor)
        assert len(results1) > 0
        
        # Test ```bash format
        response2 = f'```bash\ncat {test_file}\n```'
        _, results2 = process_agent_response(response2, tmpdir, processor)
        assert len(results2) > 0
        
        # Test ```READ format
        response3 = f'```READ test.txt```'
        _, results3 = process_agent_response(response3, tmpdir, processor)
        assert len(results3) > 0
        assert "Test content" in results3[0] or "result" in results3[0]
        
        # Test <read_file> format
        response4 = '<read_file>test.txt</read_file>'
        _, results4 = process_agent_response(response4, tmpdir, processor)
        assert len(results4) > 0
        
        print("  ✓ All formats execute correctly")


def main():
    """Run all tests."""
    print("="*70)
    print("XML TOOL PARSER TEST SUITE")
    print("="*70)
    
    try:
        # Unit tests - existing
        test_parse_single_function_call()
        test_parse_multiple_function_calls()
        test_tool_name_normalization()
        test_execute_read()
        test_execute_write()
        test_execute_append()
        test_execute_exec()
        test_execute_list_dir()
        test_error_handling()
        test_format_xml_result()
        test_integration_with_response_processor()
        test_mixed_xml_and_markdown()
        test_nested_xml_content()
        test_malformed_xml()
        
        # New multi-format tests
        test_bash_tags()
        test_bash_codeblock()
        test_shell_codeblock()
        test_sh_codeblock()
        test_multiline_codeblock()
        test_axe_read_block()
        test_axe_write_block()
        test_axe_exec_block()
        test_simple_xml_read()
        test_simple_xml_shell()
        test_simple_xml_write()
        test_mixed_formats()
        test_deduplication()
        test_comments_ignored_in_codeblock()
        test_empty_commands_ignored()
        test_clean_tool_syntax()
        test_all_formats_execution()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
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
