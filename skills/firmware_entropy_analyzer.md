Skill: firmware_entropy_analyzer
Category: Firmware Analysis / Encryption Detection
Recommended agents: grok, llama
Purpose: Use entropy analysis to detect compressed, encrypted or plaintext sections

Key approach:
- binwalk -E <file> → generate entropy plot
- High entropy regions → likely encrypted or compressed code/data
- Low entropy regions → usually strings, headers, config, compressed sections

Typical inputs: firmware file
Outputs: Entropy graph interpretation + regions classification (plaintext / compressed / encrypted / random) + suggestions where to look for keys or unpackers