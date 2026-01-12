#!/usr/bin/env python3
"""
Test suite for new XML tag formats: <exec>, <read>, <write file="...">.

Tests the bug fixes for agents using XML formats that were previously not parsed.
"""
import os
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.xml_tool_parser import (
    parse_simple_xml_tags,
    parse_all_tool_formats,
    process_agent_response
)
from axe import Config, ResponseProcessor, ToolRunner


def test_exec_tag_parsing():
    """Test parsing <exec>command</exec> format."""
    print("Testing <exec> tag parsing...")
    
    response = """Let me check the files:
    
<exec>
cat /tmp/AXE/MISSION.md
</exec>

That should show us the mission."""
    
    calls = parse_simple_xml_tags(response)
    
    # Should find 1 EXEC call
    exec_calls = [c for c in calls if c['tool'] == 'EXEC']
    assert len(exec_calls) == 1, f"Expected 1 EXEC call, got {len(exec_calls)}"
    assert exec_calls[0]['params']['command'].strip() == 'cat /tmp/AXE/MISSION.md', \
        f"Command mismatch: {exec_calls[0]['params']['command']}"
    assert exec_calls[0]['raw_name'] == 'exec'
    
    print("  ✓ <exec> tag parsed correctly")


def test_read_tag_parsing():
    """Test parsing <read>path</read> format."""
    print("Testing <read> tag parsing...")
    
    response = """I'll read the file:
    
<read>/tmp/AXE/requirements.txt</read>

Let me analyze the contents."""
    
    calls = parse_simple_xml_tags(response)
    
    # Should find 1 READ call
    read_calls = [c for c in calls if c['tool'] == 'READ']
    assert len(read_calls) == 1, f"Expected 1 READ call, got {len(read_calls)}"
    assert read_calls[0]['params']['file_path'] == '/tmp/AXE/requirements.txt', \
        f"Path mismatch: {read_calls[0]['params']['file_path']}"
    assert read_calls[0]['raw_name'] == 'read'
    
    print("  ✓ <read> tag parsed correctly")


def test_write_file_attribute_parsing():
    """Test parsing <write file="...">content</write> format."""
    print("Testing <write file=\"...\"> tag parsing...")
    
    response = """I'll create a new file:
    
<write file="/tmp/AXE/utils/message_relay.py">
# Message relay utility
def relay_message(msg):
    return f"Relayed: {msg}"
</write>

File created successfully."""
    
    calls = parse_simple_xml_tags(response)
    
    # Should find 1 WRITE call
    write_calls = [c for c in calls if c['tool'] == 'WRITE']
    assert len(write_calls) == 1, f"Expected 1 WRITE call, got {len(write_calls)}"
    assert write_calls[0]['params']['file_path'] == '/tmp/AXE/utils/message_relay.py', \
        f"Path mismatch: {write_calls[0]['params']['file_path']}"
    assert '# Message relay utility' in write_calls[0]['params']['content'], \
        f"Content missing in: {write_calls[0]['params']['content']}"
    assert write_calls[0]['raw_name'] == 'write'
    
    print("  ✓ <write file=\"...\"> tag parsed correctly")


def test_all_new_formats_together():
    """Test all new XML formats in one response."""
    print("Testing all new XML formats together...")
    
    response = """Let me perform multiple operations:

<read>/tmp/test/config.yaml</read>

<exec>
ls -la /tmp/test
</exec>

<write file="/tmp/test/output.txt">
Test output
Line 2
</write>

All operations completed."""
    
    calls = parse_all_tool_formats(response)
    
    # Check we got all 3 calls
    assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}"
    
    # Verify each type
    read_calls = [c for c in calls if c['tool'] == 'READ']
    exec_calls = [c for c in calls if c['tool'] == 'EXEC']
    write_calls = [c for c in calls if c['tool'] == 'WRITE']
    
    assert len(read_calls) == 1, "Expected 1 READ call"
    assert len(exec_calls) == 1, "Expected 1 EXEC call"
    assert len(write_calls) == 1, "Expected 1 WRITE call"
    
    print("  ✓ All new XML formats work together")


def test_integration_with_response_processor():
    """Test that new formats work end-to-end with ResponseProcessor."""
    print("Testing integration with ResponseProcessor...")
    
    # Create a temporary workspace
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Write a test file
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('Original content\n')
        
        # Create a temporary config file
        config_file = os.path.join(temp_dir, 'test_config.yaml')
        config_data = {
            'directories': {
                'allowed': [temp_dir],
                'readonly': [],
                'forbidden': []
            },
            'tools': {
                'whitelist': ['cat', 'ls', 'echo']
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Create config and components
        config = Config(config_file)
        tool_runner = ToolRunner(config, temp_dir)
        response_processor = ResponseProcessor(config, temp_dir, tool_runner)
        
        # Test response with new XML formats
        response = f"""I'll check the file:

<read>{test_file}</read>

Now list the directory:

<exec>ls -la {temp_dir}</exec>"""
        
        # Process the response
        processed_response, xml_results = process_agent_response(
            response, temp_dir, response_processor
        )
        
        # Verify results were generated
        assert len(xml_results) == 2, f"Expected 2 results, got {len(xml_results)}"
        
        # Check that results contain expected content
        combined_results = ''.join(xml_results)
        assert 'Original content' in combined_results, "READ result missing"
        assert 'test.txt' in combined_results, "EXEC result missing"
        
        print("  ✓ Integration with ResponseProcessor works")
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_no_conflicts_with_existing_formats():
    """Test that new formats don't conflict with existing ones."""
    print("Testing no conflicts with existing formats...")
    
    response = """Multiple formats:

<read_file>file1.txt</read_file>
<read>file2.txt</read>

<shell>echo hello</shell>
<exec>echo world</exec>

<write_file path="file3.txt">content3</write_file>
<write file="file4.txt">content4</write>"""
    
    calls = parse_all_tool_formats(response)
    
    # Should get 6 calls total (2 read, 2 exec, 2 write)
    assert len(calls) == 6, f"Expected 6 calls, got {len(calls)}"
    
    read_calls = [c for c in calls if c['tool'] == 'READ']
    exec_calls = [c for c in calls if c['tool'] == 'EXEC']
    write_calls = [c for c in calls if c['tool'] == 'WRITE']
    
    assert len(read_calls) == 2, "Expected 2 READ calls"
    assert len(exec_calls) == 2, "Expected 2 EXEC calls"
    assert len(write_calls) == 2, "Expected 2 WRITE calls"
    
    # Check raw names are preserved
    read_names = {c['raw_name'] for c in read_calls}
    exec_names = {c['raw_name'] for c in exec_calls}
    write_names = {c['raw_name'] for c in write_calls}
    
    assert read_names == {'read_file', 'read'}, f"READ names: {read_names}"
    assert exec_names == {'shell', 'exec'}, f"EXEC names: {exec_names}"
    assert write_names == {'write_file', 'write'}, f"WRITE names: {write_names}"
    
    print("  ✓ No conflicts with existing formats")


if __name__ == '__main__':
    print("=" * 70)
    print("NEW XML FORMATS TEST SUITE")
    print("=" * 70)
    
    test_exec_tag_parsing()
    test_read_tag_parsing()
    test_write_file_attribute_parsing()
    test_all_new_formats_together()
    test_integration_with_response_processor()
    test_no_conflicts_with_existing_formats()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
