#!/usr/bin/env python3
"""
Test suite for token-saving optimizations.
Tests context optimization, prompt compression, and other token-saving features.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.context_optimizer import ContextOptimizer, Message, estimate_token_savings
from utils.prompt_compressor import PromptCompressor, calculate_compression_ratio


def test_context_optimization():
    """Test context optimization features."""
    print("Testing context optimization...")
    
    optimizer = ContextOptimizer()
    
    # Create sample messages
    messages = [
        Message(role='system', content='You are a helpful assistant.' * 10, tokens=100),
        Message(role='user', content='What is Python?' * 5, tokens=50),
        Message(role='assistant', content='Python is a programming language.' * 20, tokens=200),
        Message(role='user', content='Tell me more about it.' * 5, tokens=50),
        Message(role='assistant', content='Python was created by Guido van Rossum.' * 30, tokens=300),
        Message(role='user', content='Show me example code.' * 5, tokens=50),
        Message(role='assistant', content='```python\nprint("Hello, World!")\n```' * 10, tokens=150),
    ]
    
    # Test optimization
    optimized = optimizer.optimize_conversation(messages, max_tokens=400, keep_recent=3)
    
    original_tokens = sum(m.tokens for m in messages)
    optimized_tokens = sum(m.tokens or optimizer.token_counter(m.content) for m in optimized)
    
    print(f"  Original tokens: {original_tokens}")
    print(f"  Optimized tokens: {optimized_tokens}")
    print(f"  Savings: {original_tokens - optimized_tokens} tokens ({(1 - optimized_tokens/original_tokens)*100:.1f}%)")
    print(f"  Original messages: {len(messages)}")
    print(f"  Optimized messages: {len(optimized)}")
    
    assert optimized_tokens <= 400, "Optimization failed to meet token budget"
    assert len(optimized) <= len(messages), "Optimization increased message count"
    print("  ✓ Context optimization passed\n")


def test_prompt_compression():
    """Test prompt compression."""
    print("Testing prompt compression...")
    
    compressor = PromptCompressor()
    
    # Sample verbose prompt
    verbose_prompt = """
    You are an expert software engineer. You are a helpful assistant.
    Please provide clear and concise code. Make sure to follow best practices.
    You should always include error handling. It is important to write tests.
    
    For example:
    - Write unit tests for all functions
    - Use type hints in Python
    - Follow PEP 8 style guide
    - Document your code properly
    - Handle edge cases carefully
    - Write defensive code
    
    Important: Always validate user input. Never trust external data.
    Note: Security is paramount in all code you write.
    
    Please remember to:
    - Check for null pointers
    - Validate array bounds
    - Sanitize SQL queries
    - Escape HTML output
    """
    
    # Test compression levels
    for level in ['minimal', 'balanced', 'aggressive']:
        compressed = compressor.compress(verbose_prompt, level=level)
        stats = calculate_compression_ratio(verbose_prompt, compressed)
        
        print(f"  {level.capitalize()} compression:")
        print(f"    Original: {stats['original_length']} chars")
        print(f"    Compressed: {stats['compressed_length']} chars")
        print(f"    Saved: {stats['percent_saved']:.1f}%")
    
    print("  ✓ Prompt compression passed\n")


def test_code_block_truncation():
    """Test code block truncation."""
    print("Testing code block truncation...")
    
    optimizer = ContextOptimizer()
    
    # Create long code block
    long_code = "```python\n"
    for i in range(100):
        long_code += f"line_{i} = {i}\n"
    long_code += "```"
    
    truncated = optimizer._truncate_code_blocks(long_code, max_lines=20)
    
    original_lines = long_code.count('\n')
    truncated_lines = truncated.count('\n')
    
    print(f"  Original lines: {original_lines}")
    print(f"  Truncated lines: {truncated_lines}")
    print(f"  Reduction: {original_lines - truncated_lines} lines")
    
    assert truncated_lines < original_lines, "Truncation failed"
    assert '... (' in truncated, "Truncation marker not found"
    print("  ✓ Code block truncation passed\n")


def test_clean_message_content():
    """Test message content cleaning."""
    print("Testing message content cleaning...")
    
    optimizer = ContextOptimizer()
    
    # Message with READ blocks
    message = """
    Let me read the file:
    
    [READ example.py]
    def hello():
        print("Hello, World!")
    
    
    Now I'll analyze it...
    """
    
    cleaned = optimizer._clean_message_content(message)
    
    print(f"  Original length: {len(message)}")
    print(f"  Cleaned length: {len(cleaned)}")
    print(f"  Reduction: {len(message) - len(cleaned)} chars")
    
    assert '[READ' not in cleaned, "READ block not removed"
    assert len(cleaned) < len(message), "Cleaning didn't reduce size"
    print("  ✓ Message cleaning passed\n")


def test_deduplication():
    """Test content deduplication."""
    print("Testing content deduplication...")
    
    optimizer = ContextOptimizer()
    
    # Create messages with duplicates
    messages = [
        Message(role='user', content='What is Python?', tokens=10),
        Message(role='assistant', content='Python is a language.', tokens=20),
        Message(role='user', content='What is Python?', tokens=10),  # Duplicate
        Message(role='assistant', content='Python is great!', tokens=20),
        Message(role='user', content='What is Python?', tokens=10),  # Duplicate
    ]
    
    deduplicated = optimizer.deduplicate_context(messages)
    
    print(f"  Original messages: {len(messages)}")
    print(f"  Deduplicated messages: {len(deduplicated)}")
    print(f"  Removed: {len(messages) - len(deduplicated)} duplicates")
    
    assert len(deduplicated) < len(messages), "Deduplication didn't remove any messages"
    print("  ✓ Deduplication passed\n")


def test_minimal_prompt_creation():
    """Test minimal prompt creation."""
    print("Testing minimal prompt creation...")
    
    compressor = PromptCompressor()
    
    roles = ['coder', 'reviewer', 'analyzer', 'security', 'optimizer']
    
    for role in roles:
        prompt = compressor.create_minimal_prompt(role)
        print(f"  {role}: {len(prompt)} chars - '{prompt}'")
        assert len(prompt) < 100, f"Minimal prompt for {role} too long"
    
    print("  ✓ Minimal prompt creation passed\n")


def test_token_savings_calculation():
    """Test token savings calculation."""
    print("Testing token savings calculation...")
    
    original = 10000
    optimized = 4000
    
    savings = estimate_token_savings(original, optimized)
    
    print(f"  Original: {savings['original']} tokens")
    print(f"  Optimized: {savings['optimized']} tokens")
    print(f"  Savings: {savings['savings']} tokens ({savings['percent']:.1f}%)")
    
    assert savings['savings'] == 6000, "Incorrect savings calculation"
    assert savings['percent'] == 60.0, "Incorrect percentage calculation"
    print("  ✓ Token savings calculation passed\n")


def test_workshop_instruction_compression():
    """Test workshop instruction compression."""
    print("Testing workshop instruction compression...")
    
    compressor = PromptCompressor()
    
    prompt = """
    Workshop tools available: /workshop chisel for symbolic execution,
    /workshop saw for taint analysis, /workshop plane for source/sink enumeration,
    /workshop hammer for live instrumentation, /workshop anvil for binary patching,
    /workshop drill for fuzzing, /workshop wrench for debugging.
    """
    
    compressed = compressor.compress_workshop_instructions(prompt)
    
    print(f"  Original: {len(prompt)} chars")
    print(f"  Compressed: {len(compressed)} chars")
    print(f"  Savings: {len(prompt) - len(compressed)} chars ({(1 - len(compressed)/len(prompt))*100:.1f}%)")
    
    assert len(compressed) < len(prompt), "Workshop compression didn't reduce size"
    print("  ✓ Workshop instruction compression passed\n")


def run_all_tests():
    """Run all token optimization tests."""
    print("=" * 60)
    print("TOKEN-SAVING OPTIMIZATIONS TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_context_optimization,
        test_prompt_compression,
        test_code_block_truncation,
        test_clean_message_content,
        test_deduplication,
        test_minimal_prompt_creation,
        test_token_savings_calculation,
        test_workshop_instruction_compression,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
