Skill: dos_memory_arena_analyzer
Category: DOS-specific Reverse Engineering
Recommended agent: llama
Purpose: Analyze DOS memory layout — MCB chain, conventional/UMB/high memory, PSP, resident programs, free blocks, overlays

Typical inputs: Low memory hexdump, PSP segment, dosbox-x memory state
Outputs: Readable memory map + resident program inference
Note: Critical foundation skill for most real DOS-era reverse engineering tasks

Optional automation:
If no hexdump/PSP provided, first use dosbox_emulation_setup to generate low memory dump:
@llama use dosbox_emulation_setup target.exe --dump-low-memory
Then feed the resulting .bin to this skill for MCB chain walking, resident TSR inference, free block map, etc.