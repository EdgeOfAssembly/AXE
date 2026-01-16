Skill: firmware_header_identify
Category: Firmware Structure Analysis
Recommended agents: grok, llama
Purpose: Detect and parse common firmware container/header formats before deep analysis

Common patterns to check (binwalk + manual):
- TRX (Broadcom/TP-Link)
- HDR0 / HSQS (many realtek/chipset vendors)
- uImage / u-boot legacy image
- OpenWrt / DD-WRT / Asuswrt signatures
- LZMA/Zlib/GZIP at known offsets
- Vendor magic bytes (D-Link, Netgear, Linksys, etc.)

Typical inputs: firmware binary + binwalk -B output
Outputs: Probable container type + header fields summary (version, size, CRC, load address…) + next recommended steps