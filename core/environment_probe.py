"""
Environment Probe - Auto-generates static environment info at session start.
Zero agent token cost - AXE runs this, not the agents.
Author: EdgeOfAssembly
License: GPLv3 / Commercial
"""
import os
import subprocess
from typing import Dict, Optional
class EnvironmentProbe:
    """Auto-generates .collab_env.md at session start. Zero agent token cost."""
    DEFAULT_PROBES = {
        # System info
        'kernel': 'uname -r',
        'arch': 'uname -m',
        'hostname': 'hostname',
        'full_uname': 'uname -a',
        'distro_name': "grep -E '^NAME=' /etc/os-release 2>/dev/null | cut -d'=' -f2 | tr -d '\"'",
        'distro_version': "grep -E '^VERSION=' /etc/os-release 2>/dev/null | cut -d'=' -f2 | tr -d '\"'",
        'shell': 'echo $SHELL',
        # Resources
        'cpu_cores': 'nproc',
        'cpu_model': "grep -m1 'model name' /proc/cpuinfo | cut -d':' -f2 | xargs",
        'memory_total': "free -h | awk '/Mem:/{print $2}'",
        'memory_available': "free -h | awk '/Mem:/{print $7}'",
        'disk_free': "df -h . | awk 'NR==2{print $4}'",
        'disk_total': "df -h . | awk 'NR==2{print $2}'",
        # Core toolchain
        'gcc': "gcc --version 2>/dev/null | head -1 || echo 'not available'",
        'clang': "clang --version 2>/dev/null | head -1 || echo 'not available'",
        'python3': "python3 --version 2>/dev/null || echo 'not available'",
        'python': "python --version 2>/dev/null || echo 'not available'",
        'pip': "pip3 --version 2>/dev/null | head -1 || echo 'not available'",
        'make': "make --version 2>/dev/null | head -1 || echo 'not available'",
        'cmake': "cmake --version 2>/dev/null | head -1 || echo 'not available'",
        'ninja': "ninja --version 2>/dev/null || echo 'not available'",
        'meson': "meson --version 2>/dev/null || echo 'not available'",
        # Version control
        'git': "git --version 2>/dev/null || echo 'not available'",
        # Debugging tools
        'gdb': "gdb --version 2>/dev/null | head -1 || echo 'not available'",
        'lldb': "lldb --version 2>/dev/null | head -1 || echo 'not available'",
        'valgrind': "valgrind --version 2>/dev/null || echo 'not available'",
        'strace': "strace --version 2>/dev/null | head -1 || echo 'not available'",
        # RE tools (important for AXE's reverse engineering focus)
        'objdump': "objdump --version 2>/dev/null | head -1 || echo 'not available'",
        'readelf': "readelf --version 2>/dev/null | head -1 || echo 'not available'",
        'nm': "nm --version 2>/dev/null | head -1 || echo 'not available'",
        'file': "file --version 2>/dev/null | head -1 || echo 'not available'",
        # Additional languages (optional)
        'rustc': "rustc --version 2>/dev/null || echo 'not available'",
        'cargo': "cargo --version 2>/dev/null || echo 'not available'",
        'go': "go version 2>/dev/null || echo 'not available'",
        'node': "node --version 2>/dev/null || echo 'not available'",
        # Kernel config location
        'kernel_config': """
if [ -f /proc/config.gz ]; then
    echo "/proc/config.gz (use zcat/zgrep)"
elif [ -f /proc/config ]; then
    echo "/proc/config (use cat/grep)"
elif [ -f /boot/config-$(uname -r) ]; then
    echo "/boot/config-$(uname -r) (use cat/grep)"
else
    echo "not found"
fi
""",
        # Man page availability
        'man_available': "man --version 2>/dev/null | head -1 || echo 'not available'",
    }
    def __init__(self, workspace_dir: str, config: dict = None):
        """
        Args:
            workspace_dir: Path to the workspace directory
            config: Optional config dict from axe.yaml preprocessing.environment_probe section
        """
        self.workspace_dir = workspace_dir
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.output_file = os.path.join(workspace_dir,
                                        self.config.get('output_file', '.collab_env.md'))
        self.timeout = self.config.get('probe_timeout', 5)
        # Merge default probes with custom probes from config
        self.probes = self.DEFAULT_PROBES.copy()
        custom_probes = self.config.get('custom_probes', {})
        self.probes.update(custom_probes)
        # Allow disabling specific probes
        disabled_probes = self.config.get('disabled_probes', [])
        for probe in disabled_probes:
            self.probes.pop(probe, None)
    def run(self) -> Optional[str]:
        """
        Execute all probes and write results to .collab_env.md
        Returns:
            Path to output file, or None if disabled
        """
        if not self.enabled:
            return None
        results = self._execute_probes()
        self._write_env_file(results)
        return self.output_file
    def _execute_probes(self) -> Dict[str, str]:
        """Execute all configured probes and collect results."""
        results = {}
        for name, cmd in self.probes.items():
            try:
                result = subprocess.run(
                    ['bash', '-c', cmd],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.workspace_dir
                )
                output = result.stdout.strip()
                # If stdout is empty, check stderr (some --version outputs go to stderr)
                if not output and result.stderr.strip():
                    output = result.stderr.strip().split('\n')[0]
                results[name] = output if output else "not available"
            except subprocess.TimeoutExpired:
                results[name] = "probe timed out"
            except Exception as e:
                results[name] = f"probe failed: {str(e)}"
        return results
    def _write_env_file(self, results: Dict[str, str]):
        """Write the environment summary to .collab_env.md"""
        # Helper to check if tool is available
        def is_available(key):
            val = results.get(key, 'not available')
            return val and 'not available' not in val.lower() and 'not found' not in val.lower()
        # Build toolchain table
        toolchain_rows = []
        tools = [
            ('GCC', 'gcc'),
            ('Clang', 'clang'),
            ('Python 3', 'python3'),
            ('pip', 'pip'),
            ('Make', 'make'),
            ('CMake', 'cmake'),
            ('Ninja', 'ninja'),
            ('Meson', 'meson'),
            ('Git', 'git'),
            ('GDB', 'gdb'),
            ('LLDB', 'lldb'),
            ('Valgrind', 'valgrind'),
            ('strace', 'strace'),
        ]
        for display_name, key in tools:
            status = "✓" if is_available(key) else "✗"
            version = results.get(key, 'not available')
            if is_available(key):
                toolchain_rows.append(f"| {display_name} | {status} | {version} |")
            else:
                toolchain_rows.append(f"| {display_name} | {status} | - |")
        # Build RE tools table
        re_tools_rows = []
        re_tools = [
            ('objdump', 'objdump'),
            ('readelf', 'readelf'),
            ('nm', 'nm'),
            ('file', 'file'),
        ]
        for display_name, key in re_tools:
            status = "✓" if is_available(key) else "✗"
            version = results.get(key, 'not available')
            if is_available(key):
                re_tools_rows.append(f"| {display_name} | {status} | {version} |")
            else:
                re_tools_rows.append(f"| {display_name} | {status} | - |")
        # Build additional languages table
        lang_rows = []
        langs = [
            ('Rust (rustc)', 'rustc'),
            ('Cargo', 'cargo'),
            ('Go', 'go'),
            ('Node.js', 'node'),
        ]
        for display_name, key in langs:
            if is_available(key):
                lang_rows.append(f"| {display_name} | ✓ | {results.get(key, '')} |")
        content = f"""# Environment Summary
*Auto-generated by AXE at session start. Do not re-probe this information.*
## System
| Property | Value |
|----------|-------|
| Kernel | {results.get('kernel', 'unknown')} |
| Architecture | {results.get('arch', 'unknown')} |
| Full uname | {results.get('full_uname', 'unknown')} |
| Distribution | {results.get('distro_name', 'unknown')} {results.get('distro_version', '')} |
| Shell | {results.get('shell', 'unknown')} |
## Resources
| Resource | Value |
|----------|-------|
| CPU Cores | {results.get('cpu_cores', 'unknown')} |
| CPU Model | {results.get('cpu_model', 'unknown')} |
| Memory | {results.get('memory_available', '?')} available / {results.get('memory_total', '?')} total |
| Disk | {results.get('disk_free', '?')} free / {results.get('disk_total', '?')} total |
## Build Toolchain
| Tool | Available | Version |
|------|-----------|---------|
{chr(10).join(toolchain_rows)}
## Reverse Engineering Tools
| Tool | Available | Version |
|------|-----------|---------|
{chr(10).join(re_tools_rows)}
"""
        # Add additional languages section only if any are available
        if lang_rows:
            content += f"""## Additional Languages
| Language | Available | Version |
|----------|-----------|---------|
{chr(10).join(lang_rows)}
"""
        content += f"""## Documentation Access
| Feature | Status |
|---------|--------|
| man pages | {'✓ Available' if is_available('man_available') else '✗ Not available'} |
| Kernel config | {results.get('kernel_config', 'not found')} |
## Quick Reference
### Documentation Commands
```bash
# View man pages without pager
man --pager=cat <command>
# Search man pages
apropos <keyword>
# Query kernel config (if available)
zgrep CONFIG_XYZ /proc/config.gz  # If using /proc/config.gz
grep CONFIG_XYZ /boot/config-$(uname -r)  # If using /boot/config
```
### Tool Version Check
```bash
# Check if a tool is available
which <tool>  # Shows path if available
# Get tool version
<tool> --version  # Most tools support this
```
### Resource Monitoring
```bash
# Check disk space
df -h .
# Check memory
free -h
# Check CPU info
lscpu
# Check running processes
ps aux
top
```
## Notes for Agents
**DO NOT** re-probe this information during your session. This file contains static system information that was captured at session start.
For **dynamic** information (e.g., current process status, network state, temporary files), you may use runtime commands.
For **project-specific** information (e.g., build configuration, project dependencies), read the project files directly.
"""
        # Write the file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)
def create_environment_probe(workspace_dir: str, config: dict = None) -> EnvironmentProbe:
    """
    Factory function to create an EnvironmentProbe.
    Args:
        workspace_dir: Path to workspace directory
        config: Optional config dict from axe.yaml preprocessing.environment_probe section
    Returns:
        EnvironmentProbe instance
    """
    return EnvironmentProbe(workspace_dir, config)