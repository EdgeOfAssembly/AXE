Skill: boot_flow_reconstruction
Category: Firmware Architecture
Recommended agents: llama + claude (review)
Purpose: Rebuild the boot sequence and initialization flow of embedded firmware

Typical stages to map:
- Reset vector / vector table
- Early assembly init (stack, .bss zeroing, relocation)
- Clock/power/peripheral basic init
- Secondary bootloader / stage 2
- Kernel loading / jump to C code
- RTOS startup (FreeRTOS, Zephyr, ThreadX patterns)

Typical inputs: Reset handler address + disassembly + binwalk results
Outputs: Markdown boot timeline + simple ASCII flow diagram + key functions/addresses