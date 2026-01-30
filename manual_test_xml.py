#!/usr/bin/env python3
"""
Manual test to verify XML function call parsing works end-to-end.
Simulates agent responses with XML function calls.
"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axe import Config, ResponseProcessor, ToolRunner
def test_xml_read_call():
    """Test XML READ call."""
    print("="*70)
    print("TEST 1: XML READ CALL")
    print("="*70)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "mission.md")
        with open(test_file, 'w') as f:
            f.write("# Mission Document\n\nYour mission is to complete the task successfully.")
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        # Simulate agent response with XML function call (native Claude format)
        agent_response = """I'll help you read the mission file.
<function_calls>
<invoke name="read_file">
<parameter name="file_path">mission.md</parameter>
</invoke>
</function_calls>
Let me check what's in the mission file."""
        print("\nAgent response:")
        print("-" * 70)
        print(agent_response)
        print("-" * 70)
        # Process the response
        processed = processor.process_response(agent_response, "claude")
        print("\nProcessed response:")
        print("-" * 70)
        print(processed)
        print("-" * 70)
        # Verify results
        if "<result>" in processed and "Mission Document" in processed:
            print("\n✅ SUCCESS: XML READ call executed and returned results")
            return True
        else:
            print("\n❌ FAILED: XML READ call did not execute properly")
            return False
def test_xml_write_call():
    """Test XML WRITE call."""
    print("\n" + "="*70)
    print("TEST 2: XML WRITE CALL")
    print("="*70)
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        # Simulate agent response with XML function call
        agent_response = """I'll create a new file for you.
<function_calls>
<invoke name="write_file">
<parameter name="file_path">output.txt</parameter>
<parameter name="content">Hello from XML function calls!
This is line 2.
This is line 3.</parameter>
</invoke>
</function_calls>
File should be created now."""
        print("\nAgent response:")
        print("-" * 70)
        print(agent_response)
        print("-" * 70)
        # Process the response
        processed = processor.process_response(agent_response, "gpt")
        print("\nProcessed response:")
        print("-" * 70)
        print(processed)
        print("-" * 70)
        # Verify file was created
        output_file = os.path.join(tmpdir, "output.txt")
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                content = f.read()
            print("\nFile created with content:")
            print("-" * 70)
            print(content)
            print("-" * 70)
            if "Hello from XML function calls!" in content:
                print("\n✅ SUCCESS: XML WRITE call executed and created file")
                return True
            else:
                print("\n❌ FAILED: File created but content incorrect")
                return False
        else:
            print("\n❌ FAILED: XML WRITE call did not create file")
            return False
def test_xml_multiple_calls():
    """Test multiple XML calls in sequence."""
    print("\n" + "="*70)
    print("TEST 3: MULTIPLE XML CALLS")
    print("="*70)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create initial file
        with open(os.path.join(tmpdir, "input.txt"), 'w') as f:
            f.write("Original data")
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        # Simulate agent response with multiple XML calls
        agent_response = """I'll perform multiple operations:
First, read the input:
<function_calls>
<invoke name="read_file">
<parameter name="file_path">input.txt</parameter>
</invoke>
</function_calls>
Then create output:
<function_calls>
<invoke name="write_file">
<parameter name="file_path">output.txt</parameter>
<parameter name="content">Processed: Original data</parameter>
</invoke>
</function_calls>
Done with both operations!"""
        print("\nAgent response:")
        print("-" * 70)
        print(agent_response)
        print("-" * 70)
        # Process the response
        processed = processor.process_response(agent_response, "llama")
        print("\nProcessed response:")
        print("-" * 70)
        print(processed)
        print("-" * 70)
        # Verify both operations succeeded
        output_exists = os.path.exists(os.path.join(tmpdir, "output.txt"))
        has_read_result = "Original data" in processed
        has_results = "<result>" in processed or "Execution Results" in processed
        if output_exists and has_read_result and has_results:
            print("\n✅ SUCCESS: Multiple XML calls executed correctly")
            return True
        else:
            print("\n❌ FAILED: Multiple XML calls did not execute properly")
            return False
def test_mixed_xml_and_markdown():
    """Test that XML and markdown formats work together."""
    print("\n" + "="*70)
    print("TEST 4: MIXED XML AND MARKDOWN")
    print("="*70)
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        tool_runner = ToolRunner(config, tmpdir)
        processor = ResponseProcessor(config, tmpdir, tool_runner)
        # Simulate agent response mixing both formats
        agent_response = """I'll use both formats:
First, XML format:
<function_calls>
<invoke name="write_file">
<parameter name="file_path">xml_file.txt</parameter>
<parameter name="content">Created via XML</parameter>
</invoke>
</function_calls>
Now markdown format:
```WRITE markdown_file.txt
Created via markdown
```
Both should work!"""
        print("\nAgent response:")
        print("-" * 70)
        print(agent_response)
        print("-" * 70)
        # Process the response
        processed = processor.process_response(agent_response, "grok")
        print("\nProcessed response:")
        print("-" * 70)
        print(processed)
        print("-" * 70)
        # Verify both files were created
        xml_file = os.path.join(tmpdir, "xml_file.txt")
        md_file = os.path.join(tmpdir, "markdown_file.txt")
        xml_exists = os.path.exists(xml_file)
        md_exists = os.path.exists(md_file)
        if xml_exists and md_exists:
            print("\n✅ SUCCESS: Both XML and markdown formats work together")
            return True
        else:
            print(f"\n❌ FAILED: XML file: {xml_exists}, Markdown file: {md_exists}")
            return False
def main():
    """Run all manual tests."""
    print("\n" + "="*70)
    print("XML FUNCTION CALL PARSER - MANUAL VERIFICATION")
    print("="*70 + "\n")
    results = []
    results.append(test_xml_read_call())
    results.append(test_xml_write_call())
    results.append(test_xml_multiple_calls())
    results.append(test_mixed_xml_and_markdown())
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Passed: {sum(results)}/{len(results)} tests")
    if all(results):
        print("\n✅ ALL MANUAL TESTS PASSED!")
        print("\nThe XML function call parser is working correctly.")
        print("LLM agents can now use their native XML format and it will be")
        print("properly parsed and executed by AXE.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1
if __name__ == '__main__':
    sys.exit(main())