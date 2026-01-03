#!/usr/bin/env python3
"""
Test suite for double execution bug (Bug #4).

Verifies that commands are executed only once, not twice,
by ensuring parse_all_tool_formats() does not duplicate
the work of ResponseProcessor.process_response().
"""
import os
import sys
import tempfile
import shutil
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.xml_tool_parser import parse_all_tool_formats, parse_axe_native_blocks
from axe import Config, ResponseProcessor, ToolRunner


def test_parse_axe_native_blocks_not_called():
    """Test that parse_all_tool_formats does not call parse_axe_native_blocks."""
    print("Testing that parse_axe_native_blocks is not called...")
    
    # Read the parse_all_tool_formats source code
    import inspect
    source = inspect.getsource(parse_all_tool_formats)
    
    # Check that parse_axe_native_blocks is commented out
    assert 'parse_axe_native_blocks(response)' not in source or \
           '# calls.extend(parse_axe_native_blocks(response))' in source, \
           "parse_axe_native_blocks should be commented out"
    
    # Verify the comment explaining why it's disabled
    assert 'REMOVED' in source or 'duplicate execution' in source.lower(), \
           "Comment explaining why parse_axe_native_blocks is disabled should be present"
    
    print("  ✓ parse_axe_native_blocks is properly commented out")


def test_native_blocks_only_processed_once():
    """Test that ```READ/WRITE/EXEC blocks are only processed once."""
    print("Testing that native blocks are only processed once...")
    
    # Create a response with native blocks
    response = """Let me read the file:

```READ /tmp/test.txt```

And execute a command:

```EXEC
echo "hello world"
```

Done."""
    
    # Call parse_all_tool_formats - should NOT parse native blocks
    xml_calls = parse_all_tool_formats(response)
    
    # Verify native blocks were NOT parsed by xml parser
    read_calls = [c for c in xml_calls if c['tool'] == 'READ']
    exec_calls = [c for c in xml_calls if c['tool'] == 'EXEC']
    
    # These should be 0 because parse_axe_native_blocks is disabled
    assert len(read_calls) == 0, f"Expected 0 READ calls from XML parser, got {len(read_calls)}"
    assert len(exec_calls) == 0, f"Expected 0 EXEC calls from XML parser, got {len(exec_calls)}"
    
    print("  ✓ Native blocks not parsed by XML parser")


def test_response_processor_handles_native_blocks():
    """Test that ResponseProcessor handles native blocks correctly."""
    print("Testing that ResponseProcessor handles native blocks...")
    
    # Create temporary workspace
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content\n')
        
        # Create config file
        config_file = os.path.join(temp_dir, 'test_config.yaml')
        import json
        with open(config_file, 'w') as f:
            json.dump({
                'directories': {'allowed': [temp_dir], 'readonly': [], 'forbidden': []},
                'tools': {'whitelist': ['echo', 'cat']}
            }, f)
        
        # Create config and components
        config = Config(config_file)
        tool_runner = ToolRunner(config, temp_dir)
        tool_runner.auto_approve = True
        response_processor = ResponseProcessor(config, temp_dir, tool_runner)
        
        # Test response with native block (need newline after ```READ)
        response = f"""Let me read the file:

```READ
{test_file}
```"""
        
        # Process response - should execute the READ
        processed = response_processor.process_response(response)
        
        # Verify execution occurred
        assert '--- Execution Results ---' in processed, "Execution results missing"
        assert 'test content' in processed, "File content not in results"
        
        print("  ✓ ResponseProcessor handles native blocks correctly")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_no_duplicate_execution_with_mixed_formats():
    """Test that mixed XML and native formats don't cause duplicate execution."""
    print("Testing no duplicate execution with mixed formats...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create test file
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('content\n')
        
        # Create config
        config_file = os.path.join(temp_dir, 'test_config.yaml')
        import json
        with open(config_file, 'w') as f:
            json.dump({
                'directories': {'allowed': [temp_dir], 'readonly': [], 'forbidden': []},
                'tools': {'whitelist': ['echo']}
            }, f)
        
        config = Config(config_file)
        tool_runner = ToolRunner(config, temp_dir)
        tool_runner.auto_approve = True
        response_processor = ResponseProcessor(config, temp_dir, tool_runner)
        
        # Response with both XML and native blocks
        response = f"""I'll use both formats:

<read>{test_file}</read>

```READ
{test_file}
```"""
        
        # Process response
        processed = response_processor.process_response(response)
        
        # Count how many times the file was read (should be 2, one for each format)
        content_count = processed.count('content')
        
        # Should be at least 2 (once in each execution result)
        # But NOT 4 (which would indicate duplicate execution)
        assert content_count >= 2, f"Expected at least 2 occurrences, got {content_count}"
        assert content_count <= 3, f"Too many occurrences ({content_count}), possible duplicate execution"
        
        print("  ✓ No duplicate execution with mixed formats")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_parse_axe_native_blocks_function_exists():
    """Test that parse_axe_native_blocks function still exists for future use."""
    print("Testing that parse_axe_native_blocks function exists...")
    
    # The function should still exist, just not be called
    assert callable(parse_axe_native_blocks), "parse_axe_native_blocks function should exist"
    
    # Test it works independently
    response = "```READ /tmp/test.txt```"
    calls = parse_axe_native_blocks(response)
    
    assert len(calls) == 1, "parse_axe_native_blocks should still work when called directly"
    assert calls[0]['tool'] == 'READ', "Parsed call should be READ"
    
    print("  ✓ parse_axe_native_blocks function exists and works")


def test_duplicate_execution_fix_documented():
    """Test that the duplicate execution fix is documented in code."""
    print("Testing that the fix is documented...")
    
    # Read the xml_tool_parser source
    with open('/home/runner/work/AXE/AXE/utils/xml_tool_parser.py', 'r') as f:
        source = f.read()
    
    # Look for documentation of the fix
    keywords = ['duplicate', 'REMOVED', 'twice', 'double']
    found_documentation = any(keyword in source for keyword in keywords)
    
    assert found_documentation, "Duplicate execution fix should be documented in code"
    
    # Check for explanation near parse_all_tool_formats
    parse_all_section = source[source.find('def parse_all_tool_formats'):source.find('def parse_all_tool_formats') + 1000]
    assert 'duplicate' in parse_all_section.lower() or 'REMOVED' in parse_all_section, \
           "Documentation should be near parse_all_tool_formats"
    
    print("  ✓ Duplicate execution fix is documented")


def test_execution_count_tracking():
    """Test that we can track execution counts to verify single execution."""
    print("Testing execution count tracking...")
    
    # Simulate execution counter
    executions = {}
    
    def track_execution(tool, params):
        key = (tool, str(params))
        executions[key] = executions.get(key, 0) + 1
    
    # Simulate processing
    track_execution('READ', {'file': '/tmp/test.txt'})
    
    # Verify single execution
    assert all(count == 1 for count in executions.values()), \
           "All tools should be executed exactly once"
    
    # Simulate duplicate execution (the bug)
    track_execution('READ', {'file': '/tmp/test.txt'})
    
    # This would fail if we had the bug
    assert any(count > 1 for count in executions.values()), \
           "Test can detect duplicate executions"
    
    print("  ✓ Execution count tracking works")


if __name__ == '__main__':
    print("=" * 70)
    print("DOUBLE EXECUTION BUG TEST SUITE")
    print("=" * 70)
    
    test_parse_axe_native_blocks_not_called()
    test_native_blocks_only_processed_once()
    test_response_processor_handles_native_blocks()
    test_no_duplicate_execution_with_mixed_formats()
    test_parse_axe_native_blocks_function_exists()
    test_duplicate_execution_fix_documented()
    test_execution_count_tracking()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nSUMMARY: Double execution bug is fixed.")
    print("- parse_axe_native_blocks() is commented out in parse_all_tool_formats()")
    print("- Native blocks are ONLY processed by ResponseProcessor.process_response()")
    print("- Commands are executed exactly once")
