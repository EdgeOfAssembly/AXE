#!/usr/bin/env python3
"""
Test suite for bug fixes from multi-agent collaboration session.

Tests Bug 1, 2, 3, 5, 6, and 7 fixes.
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.xml_tool_parser import (
    parse_simple_xml_tags,
    parse_all_tool_formats,
    detect_malformed_tool_syntax,
    process_agent_response
)
from axe import Config, ResponseProcessor, ToolRunner


def test_bug1_exec_tag():
    """Bug 1: Test <exec>command</exec> format parsing."""
    print("Testing Bug 1: <exec> tag...")
    
    response = '<exec>cat /tmp/MISSION.md</exec>'
    calls = parse_simple_xml_tags(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'EXEC', f"Expected EXEC, got {calls[0]['tool']}"
    assert calls[0]['params']['command'] == 'cat /tmp/MISSION.md'
    assert calls[0]['raw_name'] == 'exec'
    
    print("  ✓ <exec> tag parsed correctly")


def test_bug1_executor_tag():
    """Bug 1: Test <executor>command</executor> format parsing."""
    print("Testing Bug 1: <executor> tag...")
    
    response = '<executor>ls -la /tmp/AXE/</executor>'
    calls = parse_simple_xml_tags(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'EXEC', f"Expected EXEC, got {calls[0]['tool']}"
    assert calls[0]['params']['command'] == 'ls -la /tmp/AXE/'
    assert calls[0]['raw_name'] == 'executor'
    
    print("  ✓ <executor> tag parsed correctly")


def test_bug1_read_tag():
    """Bug 1: Test <read>path</read> format parsing."""
    print("Testing Bug 1: <read> tag...")
    
    response = '<read>/tmp/AXE/requirements.txt</read>'
    calls = parse_simple_xml_tags(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'READ', f"Expected READ, got {calls[0]['tool']}"
    assert calls[0]['params']['file_path'] == '/tmp/AXE/requirements.txt'
    assert calls[0]['raw_name'] == 'read'
    
    print("  ✓ <read> tag parsed correctly")


def test_bug1_write_file_tag():
    """Bug 1: Test <write file="...">content</write> format parsing."""
    print("Testing Bug 1: <write file=\"...\"> tag...")
    
    response = '''<write file="/tmp/AXE/utils/message_relay.py">
import sqlite3
import time
</write>'''
    calls = parse_simple_xml_tags(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'WRITE', f"Expected WRITE, got {calls[0]['tool']}"
    assert calls[0]['params']['file_path'] == '/tmp/AXE/utils/message_relay.py'
    assert 'import sqlite3' in calls[0]['params']['content']
    assert calls[0]['raw_name'] == 'write'
    
    print("  ✓ <write file=\"...\"> tag parsed correctly")


def test_bug1_all_formats_together():
    """Bug 1: Test that all new formats work together."""
    print("Testing Bug 1: All new formats together...")
    
    response = '''
    <exec>cat /tmp/file1.txt</exec>
    <executor>ls -la</executor>
    <read>/tmp/file2.txt</read>
    <write file="/tmp/file3.txt">content here</write>
    '''
    
    calls = parse_all_tool_formats(response)
    
    # Should parse all 4 new formats
    assert len(calls) >= 4, f"Expected at least 4 calls, got {len(calls)}"
    
    # Verify we have each type
    tools = [call['tool'] for call in calls]
    assert 'EXEC' in tools, "Missing EXEC call"
    assert 'READ' in tools, "Missing READ call"
    assert 'WRITE' in tools, "Missing WRITE call"
    
    print("  ✓ All new formats parsed correctly together")


def test_bug5_write_verification():
    """Bug 5 & 6: Test write operation with verification and feedback."""
    print("Testing Bug 5 & 6: Write verification and feedback...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Test write with verification
        content = "Test content for verification\n" * 10
        result = processor._handle_write("test_verify.txt", content)
        
        # Should include file size in feedback
        assert "bytes" in result, f"Result should include byte count: {result}"
        assert "✓" in result or "success" in result.lower(), f"Should indicate success: {result}"
        
        # Verify file exists and has correct size
        filepath = os.path.join(tmpdir, "test_verify.txt")
        assert os.path.exists(filepath), "File should exist after write"
        
        actual_size = os.path.getsize(filepath)
        expected_size = len(content.encode('utf-8'))
        assert actual_size == expected_size, f"File size mismatch: expected {expected_size}, got {actual_size}"
        
        print("  ✓ Write verification and feedback working correctly")


def test_bug7_malformed_non_ascii():
    """Bug 7: Test detection of malformed tags with non-ASCII attributes."""
    print("Testing Bug 7: Malformed non-ASCII attributes...")
    
    # Example from the bug report
    response = '<exec 天天中奖彩票="json">{"cmd":"bash","args":["ls"]}</exec>'
    warnings = detect_malformed_tool_syntax(response)
    
    assert len(warnings) > 0, "Should detect malformed syntax"
    assert any("non-ASCII" in w for w in warnings), f"Should warn about non-ASCII: {warnings}"
    
    print("  ✓ Non-ASCII attribute detection working")


def test_bug7_malformed_unclosed():
    """Bug 7: Test detection of unclosed tags."""
    print("Testing Bug 7: Unclosed tags...")
    
    response = '<exec>cat /tmp/file.txt'
    warnings = detect_malformed_tool_syntax(response)
    
    assert len(warnings) > 0, "Should detect unclosed tags"
    assert any("Unclosed" in w for w in warnings), f"Should warn about unclosed tags: {warnings}"
    
    print("  ✓ Unclosed tag detection working")


def test_bug7_malformed_json_in_tag():
    """Bug 7: Test detection of JSON in tag attributes."""
    print("Testing Bug 7: JSON in tag attributes...")
    
    response = '<exec {"cmd":"bash"}>'
    warnings = detect_malformed_tool_syntax(response)
    
    assert len(warnings) > 0, "Should detect JSON in attributes"
    assert any("JSON" in w or "code" in w for w in warnings), f"Should warn about JSON: {warnings}"
    
    print("  ✓ JSON in attributes detection working")


def test_bug7_malformed_commentary():
    """Bug 7: Test detection of non-standard commentary tags."""
    print("Testing Bug 7: Non-standard tags...")
    
    response = '<commentary to=exec code="python">test</commentary>'
    warnings = detect_malformed_tool_syntax(response)
    
    assert len(warnings) > 0, "Should detect non-standard tags"
    assert any("commentary" in w.lower() for w in warnings), f"Should warn about commentary tag: {warnings}"
    
    print("  ✓ Non-standard tag detection working")


def test_bug7_warnings_in_response():
    """Bug 7: Test that warnings are included in process_agent_response output."""
    print("Testing Bug 7: Warnings in response...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        
        # Response with malformed syntax
        response = '<exec 天天中奖彩票="json">ls</exec>'
        
        _, results = process_agent_response(response, tmpdir, processor)
        
        # Should have warnings in results
        assert len(results) > 0, "Should have results (at least warnings)"
        result_text = '\n'.join(results)
        assert "⚠️" in result_text or "warning" in result_text.lower(), f"Should include warnings: {result_text}"
        
        print("  ✓ Warnings included in response processing")


def test_bug4_no_double_execution():
    """Bug 4: Verify that parse_all_tool_formats doesn't parse AXE native blocks."""
    print("Testing Bug 4: No double execution...")
    
    # AXE native formats should NOT be parsed by parse_all_tool_formats
    # They're handled by ResponseProcessor.process_response() only
    response = '''
    ```READ /tmp/file.txt
    ```
    ```EXEC
    ls -la
    ```
    ```WRITE /tmp/out.txt
    content
    ```
    '''
    
    calls = parse_all_tool_formats(response)
    
    # Should be 0 because AXE native blocks are excluded from parse_all_tool_formats
    assert len(calls) == 0, f"AXE native blocks should not be parsed here (got {len(calls)} calls)"
    
    print("  ✓ No double execution - AXE native blocks excluded from parse_all_tool_formats")


def test_exec_with_heredoc_in_tag():
    """Bug 5: Test <exec> tag with heredoc content."""
    print("Testing Bug 5: Heredoc in <exec> tag...")
    
    response = '''<exec>
cat > /tmp/test.py << 'EOF'
def hello():
    print("Hello World")
EOF
</exec>'''
    
    calls = parse_simple_xml_tags(response)
    
    assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    assert calls[0]['tool'] == 'EXEC'
    command = calls[0]['params']['command']
    assert '<<' in command, "Should contain heredoc marker"
    assert 'EOF' in command, "Should contain EOF delimiter"
    assert 'def hello' in command, "Should contain heredoc content"
    
    print("  ✓ Heredoc in <exec> tag handled correctly")


def main():
    """Run all bug fix tests."""
    print("="*70)
    print("BUG FIX TEST SUITE")
    print("="*70)
    
    try:
        # Bug 1 tests: New XML tag formats
        test_bug1_exec_tag()
        test_bug1_executor_tag()
        test_bug1_read_tag()
        test_bug1_write_file_tag()
        test_bug1_all_formats_together()
        
        # Bug 4 test: No double execution
        test_bug4_no_double_execution()
        
        # Bug 5 & 6 tests: Write verification and feedback
        test_bug5_write_verification()
        test_exec_with_heredoc_in_tag()
        
        # Bug 7 tests: Malformed syntax detection
        test_bug7_malformed_non_ascii()
        test_bug7_malformed_unclosed()
        test_bug7_malformed_json_in_tag()
        test_bug7_malformed_commentary()
        test_bug7_warnings_in_response()
        
        print("\n" + "="*70)
        print("✅ ALL BUG FIX TESTS PASSED!")
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
