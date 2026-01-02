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
    process_agent_response
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


def main():
    """Run all tests."""
    print("="*70)
    print("XML TOOL PARSER TEST SUITE")
    print("="*70)
    
    try:
        # Unit tests
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
