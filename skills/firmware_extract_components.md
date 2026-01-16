Skill: firmware_extract_components
Category: Firmware Extraction
Recommended agents: llama (execution), claude (verification)
Purpose: Automatically extract embedded filesystems, compressed sections, kernels and other components using binwalk

Key commands:
- binwalk -e <file>                → extract everything to _<filename>.extracted/
- binwalk --dd='.*' <file>         → extract all detected file types
- binwalk -r -e <file>             → recursive extraction

Post-extraction steps to consider:
- Check for squashfs-root, jffs2, ubifs, cramfs, etc.
- Try mounting extracted filesystems (squashfs-tools, jefferson, etc.)
- Look for interesting files: /etc/passwd, web UI files, scripts, certificates

Typical inputs: firmware file path
Outputs: Path to extraction directory + summary of extracted items + quick interesting findings report
Note: Very often the first big win in firmware reversing