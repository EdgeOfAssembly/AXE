Skill: dos_exe_unpack
Category: Legacy Code Archaeology / DOS Preprocessing
Recommended agents: llama (primary, good at low-level), grok (coordination), claude (review)

Purpose: Detect and unpack common DOS executable packers (LZEXE, EXEPACK, PKLITE) to get a clean binary for further reverse engineering. This is often the critical first step for 1980s–1990s MS-DOS games/tools.

Typical inputs: Path to DOS .exe/.com file (relative or absolute)

Outputs: 
- Path to unpacked binary (or original if no packer detected)
- Short report: detected packer (or "none"), unpacker used, success/failure notes
- Markdown summary with next recommended steps

AXE-specific notes:
- Unpacker tools are in ../../tools/dos_unpackers/ (relative from repo root)
- Binaries: unlzexe, unexepack, depklite
- If a binary is missing, first run: cd ../../tools/dos_unpackers && make
- Always verify unpack success (e.g., check file size increase, MZ header, strings)

Step-by-step workflow (follow exactly):

1. Build check: 
   - Run: ls ../../tools/dos_unpackers/unlzexe ../../tools/dos_unpackers/unexepack ../../tools/dos_unpackers/depklite
   - If any missing → run: cd ../../tools/dos_unpackers && make && cd ../../..
   - Confirm all three binaries now exist.

2. Packer detection (run these commands):
   - strings <input_file> | grep -i "LZ91\|lzexe" → if match, packer = LZEXE
   - strings <input_file> | grep -i "Packed file is corrupt" → if match, packer = EXEPACK  
   - strings <input_file> | grep -i "PKLITE" → if match, packer = PKLITE
   - Prioritize in order above (some files might have overlapping strings).

3. If no packer detected:
   - Report "No common packer detected" and return original file path.

4. Unpacking:
   - LZEXE: ../../tools/dos_unpackers/unlzexe <input_file>
     - Unpacked file usually gets -unlzexe suffix or specify output.
   - EXEPACK: ../../tools/dos_unpackers/unexepack <input_file>
     - Default output: "unpacked" (rename to something sensible like original_unpacked.exe)
   - PKLITE: ../../tools/dos_unpackers/depklite <input_file>
     - Output: <input_file>.dep (good for RE even if not perfect EXE)

5. Verify:
   - Check new file has valid MZ header (hexdump -C first 32 bytes, look for "MZ")
   - Size should be larger than original
   - Quick strings check for cleaner output

6. Final output:
   - Markdown report with:
     - Original file
     - Detected packer
     - Unpacked path
     - Any warnings/errors
     - Suggestion: "@llama use find_entry_points on <unpacked_path>"

Usage example in chain:
@llama use dos_exe_unpack game.exe
→ then feed unpacked output to find_entry_points, trace_execution_path, etc.

This skill dramatically improves disassembly quality on packed DOS binaries—many old games become way more readable after this step.