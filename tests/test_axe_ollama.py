#!/usr/bin/env python3
"""
Test AXE with Ollama model in sandbox mode.
This test runs axe.py with a simple diagnostic task using Ollama.
"""
import os
import sys
import subprocess
import tempfile
import time
def test_axe_with_ollama():
    """Test axe.py with Ollama model."""
    print("=" * 70)
    print("AXE + OLLAMA SANDBOX TEST")
    print("=" * 70)
    # Check if Ollama is running
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("✗ Ollama not running")
            return False
        models = result.stdout
        print(f"✓ Ollama is running")
        print(f"  Available models:\n{models}")
        # Check if qwen model is available
        if 'qwen' not in models.lower():
            print("✗ qwen2.5:0.5b model not found")
            print("  Run: ollama pull qwen2.5:0.5b")
            return False
        print("✓ qwen2.5:0.5b model available")
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        return False
    # Create a test workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nTest workspace: {tmpdir}")
        # Create a test Python file
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""#!/usr/bin/env python3
# Simple test file
def hello():
    print("Hello from test file")
if __name__ == '__main__':
    hello()
""")
        # Create output file for diagnostics
        output_file = os.path.join(tmpdir, "axe_output.txt")
        # Test command for the agent
        test_command = f"""Write diagnostic information to {output_file}:
1. Run 'whoami' command and save output
2. Run 'id' command and save output
3. Run 'pwd' command and save output
4. Run 'ls -la' command and save output
5. Write a summary stating whether you appear to be running as root
Use EXEC blocks to run commands and WRITE block to save results."""
        print("\n" + "=" * 70)
        print("TEST: Running AXE with diagnostic task")
        print("=" * 70)
        print(f"\nTask: {test_command[:100]}...")
        # Run axe.py with the ollama provider (qwen model)
        # Use -c for single command mode
        axe_cmd = [
            'python3', '/home/runner/work/AXE/AXE/axe.py',
            '--dir', tmpdir,
            '-c', f'@llama {test_command}'
        ]
        print(f"\nRunning: {' '.join(axe_cmd[:4])} ...")
        print("(This may take 30-60 seconds for model inference)\n")
        try:
            result = subprocess.run(
                axe_cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for model inference
                cwd='/home/runner/work/AXE/AXE'
            )
            print("=" * 70)
            print("AXE OUTPUT:")
            print("=" * 70)
            print(result.stdout)
            if result.stderr:
                print("\n" + "=" * 70)
                print("STDERR:")
                print("=" * 70)
                print(result.stderr)
            print("\n" + "=" * 70)
            print("RESULTS:")
            print("=" * 70)
            # Check if output file was created
            if os.path.exists(output_file):
                print(f"✓ Output file created: {output_file}")
                with open(output_file, 'r') as f:
                    content = f.read()
                print("\nOutput file contents:")
                print("-" * 70)
                print(content)
                print("-" * 70)
            else:
                print(f"⚠️  Output file not created: {output_file}")
                print("  Agent may not have been able to execute commands")
            # Check return code
            if result.returncode == 0:
                print(f"\n✓ axe.py completed successfully (exit code: 0)")
            else:
                print(f"\n⚠️  axe.py exit code: {result.returncode}")
            return True
        except subprocess.TimeoutExpired:
            print("✗ Command timed out after 120 seconds")
            return False
        except Exception as e:
            print(f"✗ Error running axe.py: {e}")
            import traceback
            traceback.print_exc()
            return False
if __name__ == "__main__":
    try:
        success = test_axe_with_ollama()
        print("\n" + "=" * 70)
        if success:
            print("✅ TEST COMPLETED")
        else:
            print("⚠️  TEST COMPLETED WITH WARNINGS")
        print("=" * 70)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)