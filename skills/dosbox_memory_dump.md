Skill: dosbox_memory_dump
Category: DOS-specific Reverse Engineering / Emulation
Recommended agent: llama

Purpose: Clean conventional/low memory dump via DOSBox-X for MCB/PSP/TSR analysis. Uses interactive mode for manual debugger dump (automated not feasible).

Inputs: Optional target.exe (for post-load dump), --full-1mb flag

Workflow:
1. @llama use dosbox_emulation_setup --interactive --dump-low-memory (add --full-1mb if needed; add target.exe + --brief-run for post-load)
2. When session starts: press debugger hotkey → type the suggested MEMDUMPBIN command → file appears in workspace
3. Exit DOSBox when done
4. Verify/parse the .bin (size check, hexdump -C head/tail, or direct feed to dos_memory_arena_analyzer)