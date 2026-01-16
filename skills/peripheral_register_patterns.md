Skill: peripheral_register_patterns
Category: Bare-metal / Embedded Understanding
Recommended agents: llama (strongest for asm)
Purpose: Help locate and label hardware register accesses in disassembled firmware code

Common patterns to look for:
- Load/store to fixed high addresses (0x4000_0000+, 0xE000_0000+ on ARM Cortex-M)
- Bitfield operations: BIC, ORR, AND with constants
- Polling loops (LDR → TST → BNE)
- Write-read sequences for status registers
- Clock/power/GPIO init blocks (very common early in boot)

Typical inputs: Disassembly snippet / function / Ghidra/IDA export
Outputs: List of suspected peripheral base addresses + guessed names (UART, SPI, I2C, GPIO, TIM, ADC, WDT…)
Value: Transforms "magic numbers" into understandable driver code