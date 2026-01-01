#!/usr/bin/env python3
"""
Manual test script for WRITE block functionality.
Run this to verify agents can create files using WRITE blocks.

Usage:
    export ANTHROPIC_API_KEY=your_key
    export OPENAI_API_KEY=your_key
    python3 manual_test_write.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axe import Config, AgentManager, ResponseProcessor, ToolRunner


def test_agent(agent_name: str):
    """Test an agent's WRITE block functionality."""
    print(f"\n{'='*70}")
    print(f"Testing {agent_name.upper()}")
    print(f"{'='*70}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Workspace: {tmpdir}\n")
        
        try:
            config = Config()
            agent_mgr = AgentManager(config)
            tool_runner = ToolRunner(config, tmpdir)
            tool_runner.auto_approve = True
            processor = ResponseProcessor(config, tmpdir, tool_runner)
            
            # Test 1: Simple file creation
            print("Test 1: Create a simple text file")
            prompt = """Please create a file called 'test.txt' with the content "Hello, World!" using a WRITE block."""
            
            print(f"  Sending request...")
            response = agent_mgr.call_agent(agent_name, prompt, "")
            
            if "API error" in response or "not available" in response:
                print(f"  ❌ FAILED: {response}")
                return False
            
            print(f"  Agent response ({len(response)} chars):")
            print(f"  {response[:200]}...")
            
            # Process for code blocks
            processed = processor.process_response(response, agent_name)
            
            # Check if file was created
            test_file = os.path.join(tmpdir, "test.txt")
            if os.path.exists(test_file):
                with open(test_file, 'r') as f:
                    content = f.read()
                print(f"  ✅ SUCCESS: File created with content: {repr(content)}")
            else:
                print(f"  ⚠️  File not created. Agent may not have used WRITE block.")
                print(f"  Processed response:")
                print(f"  {processed}")
                return False
            
            # Test 2: Python script creation
            print("\nTest 2: Create a Python script")
            prompt2 = """Create a Python script called 'hello.py' that prints "Hello from Python!" when run. Use a WRITE block."""
            
            print(f"  Sending request...")
            response2 = agent_mgr.call_agent(agent_name, prompt2, "")
            processor.process_response(response2, agent_name)
            
            hello_file = os.path.join(tmpdir, "hello.py")
            if os.path.exists(hello_file):
                with open(hello_file, 'r') as f:
                    content = f.read()
                print(f"  ✅ SUCCESS: Python script created")
                print(f"  Preview: {content[:100]}...")
            else:
                print(f"  ⚠️  Python script not created")
                return False
            
            print(f"\n✅ {agent_name.upper()} PASSED ALL TESTS!")
            return True
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run manual tests."""
    print("="*70)
    print("MANUAL WRITE BLOCK TEST")
    print("="*70)
    print("\nThis script tests WRITE block functionality with real LLM APIs.")
    print("Make sure you have set the required API keys as environment variables.\n")
    
    # Check API keys
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    
    if not (has_anthropic or has_openai):
        print("❌ No API keys found!")
        print("\nPlease set at least one of:")
        print("  export ANTHROPIC_API_KEY=your_key")
        print("  export OPENAI_API_KEY=your_key")
        return 1
    
    results = {}
    
    # Test available agents
    if has_anthropic:
        results['claude'] = test_agent('claude')
    
    if has_openai:
        results['gpt'] = test_agent('gpt')
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for agent, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {agent:10} {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! WRITE blocks are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
