Skill: dos_packer_detector
Category: DOS-specific Reverse Engineering
Recommended agents: llama (primary, low-level analysis), grok (coordination/scripting)

Purpose: Detect common DOS executable packers/compressors (LZEXE, PKLITE, EXEPACK, DIET, etc.) on a target .EXE/.COM file. Uses signature checks and safe trial runs with the unpackers from /tools/dos_unpackers/. Reports packer type (or "plain/unpacked MZ executable") and suggests the appropriate unpack command. Essential prep step before static disassembly or memory analysis, as packed exes hide code/strings.

Typical inputs:
- Path to DOS executable (e.g., AR/AR.EXE, relative to workspace)
- Optional flags: --unpack (auto-unpack if detected, outputs unpacked.exe), --verbose (show raw tool output)

Outputs:
- Markdown report: detected packer (or none), confidence, key evidence (signatures/output)
- If --unpack: path to unpacked file (e.g., AR_unpacked.exe)
- Ready next steps (e.g., "@llama disassemble unpacked.exe" or "No packer → feed directly to ida_pro_analysis_patterns")

AXE-specific notes:
- Requires unpackers built in /tools/dos_unpackers/ (runs `make` automatically if binaries missing)
- Works on copy of file to avoid modifying original
- Sandbox-safe (all ops in workspace)
- Focuses on classic 80s/90s packers (LZEXE v0.9x, PKLITE 1.x/2.x, Microsoft EXEPACK); modern ones like UPX not expected in old DOS games

Step-by-step workflow (follow precisely):

1. Build unpackers if needed:
   if [ ! -f /tools/dos_unpackers/unlzexe ] || [ ! -f /tools/dos_unpackers/depklite ] || [ ! -f /tools/dos_unpackers/unexepack ]; then
       make -C /tools/dos_unpackers/
       echo "Built DOS unpackers"
   fi

2. Validate target:
   - File exists and is MZ executable: head -c 2 "$target" | grep -q "MZ" || error "Not a valid DOS MZ executable"

3. Make safe working copy:
   cp "$target" temp_packed.exe

4. Detection (try tools in order of commonality, capture output):
   packer="none"
   evidence=""

   # Try unlzexe first (very common)
   /tools/dos_unpackers/unlzexe -t temp_packed.exe > detect_log.txt 2>&1
   if grep -qi "packed.*lzexe" detect_log.txt; then
       packer="LZEXE"
       evidence=$(grep -i "lzexe" detect_log.txt)

   # Then PKLITE
   elif /tools/dos_unpackers/depklite temp_packed.exe > detect_log.txt 2>&1 && grep -q "PKLITE" detect_log.txt; then
       packer="PKLITE"
       evidence=$(grep -i "pklite" detect_log.txt)

   # Then EXEPACK
   elif /tools/dos_unpackers/unexepack temp_packed.exe > detect_log.txt 2>&1 && grep -q "EXEPACK" detect_log.txt; then
       packer="Microsoft EXEPACK"
       evidence=$(grep -i "exepack" detect_log.txt)

   # Optional: add more (DIET, etc.) if tools expand
   fi

   # Fallback signature quick-check if all trials fail
   if [ "$packer" = "none" ]; then
       if strings temp_packed.exe | grep -qi "pklite"; then
           packer="PKLITE (signature only)"
       elif hexdump -C temp_packed.exe | grep -qi "lz09\|lz91"; then
           packer="LZEXE (signature only)"
       fi
   fi

   rm temp_packed.exe

5. Optional auto-unpack:
   if [ "--unpack" provided ] && [ "$packer" != "none" ]; then
       cp "$target" temp_packed.exe
       case $packer in
           "LZEXE"*) /tools/dos_unpackers/unlzexe temp_packed.exe ;;
           "PKLITE"*) /tools/dos_unpackers/depklite temp_packed.exe ;;
           "Microsoft EXEPACK"*) /tools/dos_unpackers/unexepack temp_packed.exe ;;
       esac
       mv temp_packed.exe "${target%.*}_unpacked.exe"
       unpacked_path="${target%.*}_unpacked.exe"
   fi

6. Final report (Markdown):
   # DOS Packer Detection Report

   **Target:** $target  
   **Detected packer:** $packer  

   **Evidence:**
   $evidence (or full detect_log.txt if --verbose)

**Artifacts:**
- detect_log.txt (raw tool output)
- $unpacked_path (if --unpack used)

**Next steps:**
- If packed and unpacked: "@llama use x86_assembly_expert on unpacked.exe" or feed to IDA
- If none: "Proceed with original → strings, disassembly, or dosbox dynamic analysis"
- If uncertain: "Manual check with hex editor for other packers"

Example chains:
@llama use dos_packer_detector AR/AR.EXE
→ Likely "none" for Airborne Ranger

@llama use dos_packer_detector somegame.exe --unpack
→ Auto-unpacks if LZEXE/PKLITE/EXEPACK, ready for deeper RE

@llama use dos_packer_detector oldshareware.exe --verbose
→ Full diagnostic output for tricky cases


