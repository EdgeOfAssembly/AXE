Skill: firmware_binwalk_scan
Category: Firmware Analysis / Extraction
Recommended agents: llama, grok
Purpose: Perform initial signature scan and structure analysis of firmware images using binwalk

Key commands to use:
- binwalk -B <file>          → basic scan with signatures
- binwalk -E <file>          → generate entropy graph (save as .gnuplot or .png)
- binwalk -M -v <file>       → recursive/matryoshka scan (very useful for nested images)

Typical inputs: firmware binary path (.bin, .img, .trx, router update file…)
Outputs: 
- Summary of detected signatures, offsets and types
- List of probable embedded components (compressed data, filesystems, headers…)
- Entropy assessment (high entropy = likely encrypted/compressed code)

Usage tip: Always start almost every firmware task with this skill