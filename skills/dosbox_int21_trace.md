Skill: dosbox_int21_trace
Category: DOS-specific Reverse Engineering / Emulation
Recommended agent: llama

Purpose: Trace INT 21h / file I/O during program run to map resource loading (e.g., which .DTX for what).

Inputs: target.exe (e.g., AR.EXE), --brief-run or --full-play

Workflow:
1. @llama use dosbox_emulation_setup --headless --preset headless --log-int21 --log-fileio target.exe --run-and-exit
   (Or --brief-run: add pause/echo for early exit)

2. Run → produces log.txt with lines like:
   INT21: AH=3Fh BX=filehandle ... (reads)
   INT21: AH=3Dh ... Open file: MAPDES.DTX

3. Post-process:
   grep log.txt -i "open\|read\|3d\|3f" > fileio_trace.txt
   Or feed full log to analysis skill.

4. Report: Key files accessed in order, any errors.

Example for Airborne Ranger:
@llama use dosbox_int21_trace AR/AR.EXE
→ Reveals startup loads TTLCHR.DTX, MSCHR.DTX etc. for title/menu.