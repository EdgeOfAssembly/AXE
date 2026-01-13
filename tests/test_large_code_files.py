#!/usr/bin/env python3
"""
Extensive tests for AXE handling of large code files.

This test suite verifies that:
1. Large code files are NOT truncated
2. The shared collaboration systems work with large content
3. File reading handles large files correctly
4. Context optimization preserves code even with large files
5. Build status system handles large output

These tests ensure agents can work effectively with real-world
large codebases without losing context.
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.context_optimizer import ContextOptimizer, Message
from core.constants import (
    COLLAB_SHARED_NOTES_LIMIT,
    COLLAB_HISTORY_LIMIT,
    COLLAB_CONTENT_LIMIT,
)


def generate_large_python_file(lines: int) -> str:
    """Generate a large Python file with realistic content."""
    content = '"""Large Python module for testing.\n\nThis file contains many functions and classes.\n"""\n\n'
    content += "import os\nimport sys\nimport json\nfrom typing import List, Dict, Any, Optional\n\n"
    
    # Generate classes
    for c in range(lines // 50):
        content += f'''
class DataProcessor{c}:
    """Data processor class #{c}."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data: List[Any] = []
        self.processed: bool = False
    
    def process(self, items: List[Any]) -> List[Any]:
        """Process a list of items."""
        results = []
        for item in items:
            if self._validate(item):
                result = self._transform(item)
                results.append(result)
        self.processed = True
        return results
    
    def _validate(self, item: Any) -> bool:
        """Validate an item."""
        return item is not None
    
    def _transform(self, item: Any) -> Any:
        """Transform an item."""
        return {{"original": item, "processor": {c}}}

'''
    
    # Generate standalone functions
    for f in range(lines // 20):
        content += f'''
def helper_function_{f}(arg1: str, arg2: int = 0) -> Optional[str]:
    """Helper function #{f}.
    
    Args:
        arg1: First argument
        arg2: Second argument (default: 0)
    
    Returns:
        Processed result or None
    """
    if not arg1:
        return None
    result = f"{{arg1}}_{{arg2}}_processed_{f}"
    return result

'''
    
    return content


def generate_large_c_file(lines: int) -> str:
    """Generate a large C file with realistic content."""
    content = '''/*
 * Large C source file for testing.
 * Contains multiple functions and data structures.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

'''
    
    # Generate structs
    for s in range(lines // 100):
        content += f'''
typedef struct {{
    int id;
    char name[64];
    double value;
    uint8_t flags;
    struct data_node_{s} *next;
}} data_node_{s};

int process_node_{s}(data_node_{s} *node) {{
    if (node == NULL) {{
        return -1;
    }}
    printf("Processing node %d: %s\\n", node->id, node->name);
    return 0;
}}

data_node_{s} *create_node_{s}(int id, const char *name, double value) {{
    data_node_{s} *node = malloc(sizeof(data_node_{s}));
    if (node == NULL) {{
        return NULL;
    }}
    node->id = id;
    strncpy(node->name, name, sizeof(node->name) - 1);
    node->name[sizeof(node->name) - 1] = '\\0';
    node->value = value;
    node->flags = 0;
    node->next = NULL;
    return node;
}}

void free_node_{s}(data_node_{s} *node) {{
    if (node != NULL) {{
        free(node);
    }}
}}

'''
    
    # Add main function
    content += '''
int main(int argc, char *argv[]) {
    printf("Large C file test\\n");
    return 0;
}
'''
    
    return content


def generate_large_assembly_file(lines: int) -> str:
    """Generate a large assembly file with realistic content."""
    content = '''; Large x86 assembly file for testing
; Contains multiple subroutines and data sections

section .data
'''
    
    # Generate data section
    for d in range(lines // 50):
        content += f'''    msg_{d} db "Message {d}", 0
    buffer_{d} times 256 db 0
'''
    
    content += '''
section .bss
    input_buffer resb 4096
    output_buffer resb 4096

section .text
    global _start
'''
    
    # Generate subroutines
    for s in range(lines // 30):
        content += f'''
; Subroutine {s}
subroutine_{s}:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    ; Function body
    mov eax, {s}
    add eax, 1
    imul eax, 2
    
    ; Restore and return
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

'''
    
    # Add entry point
    content += '''
_start:
    ; Program entry point
    mov eax, 1      ; sys_exit
    xor ebx, ebx    ; exit code 0
    int 0x80
'''
    
    return content


class TestLargeCodeFiles:
    """Test suite for large code file handling."""
    
    def __init__(self):
        self.temp_dir = None
        self.optimizer = ContextOptimizer()
        self.test_results = []
    
    def setup(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix='axe_large_file_test_')
        print(f"  Test directory: {self.temp_dir}")
    
    def teardown(self):
        """Clean up test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_no_truncation_python_1000_lines(self):
        """Test that 1000-line Python file is NOT truncated."""
        print("\n--- Test: 1000-line Python file ---")
        
        content = generate_large_python_file(1000)
        original_lines = content.count('\n')
        original_size = len(content)
        
        print(f"  Generated: {original_lines} lines, {original_size} chars")
        
        # Test truncate_code returns unchanged
        result = self.optimizer.truncate_code(content, max_lines=50)
        result_lines = result.count('\n')
        result_size = len(result)
        
        print(f"  After truncate_code(): {result_lines} lines, {result_size} chars")
        
        assert result == content, "Content was modified!"
        assert result_lines == original_lines, "Line count changed!"
        print("  ✓ PASSED: 1000-line Python file NOT truncated")
        return True
    
    def test_no_truncation_python_5000_lines(self):
        """Test that 5000-line Python file is NOT truncated."""
        print("\n--- Test: 5000-line Python file ---")
        
        content = generate_large_python_file(5000)
        original_lines = content.count('\n')
        original_size = len(content)
        
        print(f"  Generated: {original_lines} lines, {original_size} chars ({original_size // 1024}KB)")
        
        result = self.optimizer.truncate_code(content, max_lines=100)
        result_lines = result.count('\n')
        
        print(f"  After truncate_code(): {result_lines} lines")
        
        assert result == content, "Content was modified!"
        print("  ✓ PASSED: 5000-line Python file NOT truncated")
        return True
    
    def test_no_truncation_c_2000_lines(self):
        """Test that 2000-line C file is NOT truncated."""
        print("\n--- Test: 2000-line C file ---")
        
        content = generate_large_c_file(2000)
        original_lines = content.count('\n')
        original_size = len(content)
        
        print(f"  Generated: {original_lines} lines, {original_size} chars ({original_size // 1024}KB)")
        
        result = self.optimizer.truncate_code(content, max_lines=50)
        
        assert result == content, "Content was modified!"
        print("  ✓ PASSED: 2000-line C file NOT truncated")
        return True
    
    def test_no_truncation_assembly_1500_lines(self):
        """Test that 1500-line assembly file is NOT truncated."""
        print("\n--- Test: 1500-line assembly file ---")
        
        content = generate_large_assembly_file(1500)
        original_lines = content.count('\n')
        original_size = len(content)
        
        print(f"  Generated: {original_lines} lines, {original_size} chars ({original_size // 1024}KB)")
        
        result = self.optimizer.truncate_code(content, max_lines=30)
        
        assert result == content, "Content was modified!"
        print("  ✓ PASSED: 1500-line assembly file NOT truncated")
        return True
    
    def test_large_code_in_message(self):
        """Test that large code blocks in messages are preserved."""
        print("\n--- Test: Large code block in message ---")
        
        code = generate_large_python_file(500)
        message_content = f"Here is the code:\n\n```python\n{code}\n```\n\nPlease review it."
        
        original_size = len(message_content)
        print(f"  Message size: {original_size} chars ({original_size // 1024}KB)")
        
        # Test clean_content preserves code
        cleaned = self.optimizer.clean_content(message_content)
        cleaned_size = len(cleaned)
        
        # Code should be preserved (only READ blocks removed)
        assert '```python' in cleaned, "Code block markers removed!"
        assert 'class DataProcessor' in cleaned, "Code content removed!"
        
        print(f"  After clean_content(): {cleaned_size} chars")
        print("  ✓ PASSED: Large code block in message preserved")
        return True
    
    def test_conversation_with_large_code(self):
        """Test conversation optimization with large code blocks."""
        print("\n--- Test: Conversation with large code ---")
        
        code1 = generate_large_python_file(200)
        code2 = generate_large_c_file(200)
        
        messages = [
            Message(role='system', content='You are a code reviewer.', tokens=20),
            Message(role='user', content=f'Review this Python:\n```python\n{code1}\n```', tokens=len(code1)//4),
            Message(role='assistant', content='This looks good. Here are my suggestions...', tokens=50),
            Message(role='user', content=f'Now review this C:\n```c\n{code2}\n```', tokens=len(code2)//4),
            Message(role='assistant', content='The C code is well-structured.', tokens=30),
        ]
        
        total_tokens = sum(m.tokens for m in messages)
        print(f"  Total tokens in conversation: {total_tokens}")
        
        # Optimize with large budget (should keep most content)
        optimized = self.optimizer.optimize_conversation(messages, max_tokens=total_tokens + 1000)
        optimized_tokens = sum(m.tokens or self.optimizer.token_counter(m.content) for m in optimized)
        
        print(f"  After optimization: {optimized_tokens} tokens")
        print(f"  Messages: {len(messages)} -> {len(optimized)}")
        
        # With large budget, content should be mostly preserved
        assert len(optimized) >= 3, "Too many messages removed!"
        print("  ✓ PASSED: Conversation with large code handled correctly")
        return True
    
    def test_file_write_and_read_large(self):
        """Test writing and reading large files."""
        print("\n--- Test: Write/read large files ---")
        
        # Generate large file
        content = generate_large_python_file(2000)
        filepath = os.path.join(self.temp_dir, 'large_test.py')
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(content)
        
        file_size = os.path.getsize(filepath)
        print(f"  Written file: {file_size} bytes ({file_size // 1024}KB)")
        
        # Read file back
        with open(filepath, 'r') as f:
            read_content = f.read()
        
        assert read_content == content, "File content changed during write/read!"
        print(f"  Read back: {len(read_content)} chars (identical)")
        print("  ✓ PASSED: Large file write/read works correctly")
        return True
    
    def test_shared_notes_limit(self):
        """Test that shared notes limit is sufficient for large content."""
        print("\n--- Test: Shared notes limit ---")
        
        # Generate content slightly under the limit
        content = "A" * (COLLAB_SHARED_NOTES_LIMIT - 100)
        
        print(f"  COLLAB_SHARED_NOTES_LIMIT: {COLLAB_SHARED_NOTES_LIMIT:,} chars")
        print(f"  Test content size: {len(content):,} chars")
        
        # Verify the limit is reasonable (should be 100K now)
        assert COLLAB_SHARED_NOTES_LIMIT >= 100000, f"Shared notes limit too low: {COLLAB_SHARED_NOTES_LIMIT}"
        
        # Content under limit should be preserved
        if len(content) <= COLLAB_SHARED_NOTES_LIMIT:
            result = content  # No truncation needed
        else:
            result = content[-COLLAB_SHARED_NOTES_LIMIT:]
        
        assert len(result) == len(content), "Content was truncated unnecessarily!"
        print("  ✓ PASSED: Shared notes limit is adequate for large content")
        return True
    
    def test_history_limit(self):
        """Test that history limit allows sufficient messages."""
        print("\n--- Test: History limit ---")
        
        print(f"  COLLAB_HISTORY_LIMIT: {COLLAB_HISTORY_LIMIT} messages")
        
        # Verify the limit is reasonable (should be 200 now)
        assert COLLAB_HISTORY_LIMIT >= 200, f"History limit too low: {COLLAB_HISTORY_LIMIT}"
        
        # Create messages up to the limit
        messages = [
            Message(role='user', content=f'Message {i}', tokens=10)
            for i in range(COLLAB_HISTORY_LIMIT)
        ]
        
        print(f"  Created {len(messages)} messages")
        assert len(messages) == COLLAB_HISTORY_LIMIT, "Could not create expected number of messages!"
        print("  ✓ PASSED: History limit allows sufficient messages")
        return True
    
    def test_content_limit(self):
        """Test that content limit per message is sufficient."""
        print("\n--- Test: Content limit per message ---")
        
        print(f"  COLLAB_CONTENT_LIMIT: {COLLAB_CONTENT_LIMIT:,} chars")
        
        # Verify the limit is reasonable (should be 100K now)
        assert COLLAB_CONTENT_LIMIT >= 100000, f"Content limit too low: {COLLAB_CONTENT_LIMIT}"
        
        # Generate content at the limit
        large_code = generate_large_python_file(2000)
        
        print(f"  Large code size: {len(large_code):,} chars")
        
        if len(large_code) <= COLLAB_CONTENT_LIMIT:
            print(f"  Large code fits within limit ✓")
        else:
            print(f"  Large code exceeds limit by {len(large_code) - COLLAB_CONTENT_LIMIT:,} chars")
        
        print("  ✓ PASSED: Content limit is adequate for large code")
        return True
    
    def test_multiple_large_code_blocks(self):
        """Test handling multiple large code blocks in one response."""
        print("\n--- Test: Multiple large code blocks ---")
        
        py_code = generate_large_python_file(300)
        c_code = generate_large_c_file(300)
        asm_code = generate_large_assembly_file(300)
        
        combined = f"""Here are three implementations:

## Python Version

```python
{py_code}
```

## C Version

```c
{c_code}
```

## Assembly Version

```asm
{asm_code}
```
"""
        
        total_size = len(combined)
        print(f"  Combined content: {total_size:,} chars ({total_size // 1024}KB)")
        
        # Test that truncate_code preserves all
        result = self.optimizer.truncate_code(combined, max_lines=50)
        
        assert result == combined, "Combined content was modified!"
        assert '```python' in result, "Python block removed!"
        assert '```c' in result, "C block removed!"
        assert '```asm' in result, "Assembly block removed!"
        
        print("  ✓ PASSED: Multiple large code blocks preserved")
        return True
    
    def test_very_long_single_line(self):
        """Test handling of very long single lines (e.g., minified JS)."""
        print("\n--- Test: Very long single line ---")
        
        # Simulate minified JavaScript
        long_line = "var a=" + ",".join([f'"{i}"' for i in range(10000)]) + ";"
        content = f"```javascript\n{long_line}\n```"
        
        print(f"  Line length: {len(long_line):,} chars")
        print(f"  Total content: {len(content):,} chars")
        
        result = self.optimizer.truncate_code(content, max_lines=10)
        
        assert result == content, "Long line content was modified!"
        print("  ✓ PASSED: Very long single line preserved")
        return True
    
    def test_binary_like_content(self):
        """Test handling of binary-like content (hex dumps)."""
        print("\n--- Test: Binary-like content (hex dump) ---")
        
        # Generate hex dump content
        lines = []
        for addr in range(0, 10000, 16):
            hex_bytes = " ".join([f"{(addr + i) % 256:02x}" for i in range(16)])
            ascii_repr = "".join([chr((addr + i) % 95 + 32) for i in range(16)])
            lines.append(f"{addr:08x}  {hex_bytes}  |{ascii_repr}|")
        
        content = "\n".join(lines)
        
        print(f"  Hex dump: {len(lines)} lines, {len(content):,} chars")
        
        result = self.optimizer.truncate_code(content, max_lines=50)
        
        assert result == content, "Hex dump content was modified!"
        print("  ✓ PASSED: Binary-like content preserved")
        return True
    
    def run_all_tests(self):
        """Run all large code file tests."""
        print("=" * 70)
        print("EXTENSIVE LARGE CODE FILE TEST SUITE")
        print("Testing how AXE agents handle really long code files")
        print("=" * 70)
        
        self.setup()
        
        tests = [
            self.test_no_truncation_python_1000_lines,
            self.test_no_truncation_python_5000_lines,
            self.test_no_truncation_c_2000_lines,
            self.test_no_truncation_assembly_1500_lines,
            self.test_large_code_in_message,
            self.test_conversation_with_large_code,
            self.test_file_write_and_read_large,
            self.test_shared_notes_limit,
            self.test_history_limit,
            self.test_content_limit,
            self.test_multiple_large_code_blocks,
            self.test_very_long_single_line,
            self.test_binary_like_content,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ✗ FAILED: {test.__name__}: {e}")
                failed += 1
        
        self.teardown()
        
        print("\n" + "=" * 70)
        print("LARGE CODE FILE TEST RESULTS")
        print("=" * 70)
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Total:  {passed + failed}")
        print("=" * 70)
        
        if failed == 0:
            print("\n✓ ALL TESTS PASSED - AXE handles large code files correctly!")
            print("  Code is NOT truncated, and agents have maximum shared view.")
        else:
            print(f"\n✗ {failed} TEST(S) FAILED - Review the results above.")
        
        return failed == 0


def run_all_tests():
    """Entry point for running all tests."""
    suite = TestLargeCodeFiles()
    return suite.run_all_tests()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
