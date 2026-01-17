Skill: dosbox_emulation_setup
Category: DOS-specific Reverse Engineering / Emulation
Recommended agents: llama (primary, low-level expert), grok (scripting/coordination)

Purpose: Self-contained DOSBox-X session for reverse engineering. Generates optimized config or symlinks to era presets, mounts workspace as C:, runs target binary (or prompt), supports automated headless fast runs OR interactive video mode for manual debugging/memory dumps/screenshots. Captures logs, enables clean exits, produces artifacts for chaining (log.txt, *.bin from manual dumps, *.png screenshots).

Typical inputs:
- Path to DOS .exe/.com (relative to workspace, optional)
- Flags: 
  --interactive (or --dump-low-memory / --dump-full-conventional to auto-enable interactive)
  --run-and-exit, --brief-run, --cycles <n>
  --preset <name> (cga-8086, ega-286, vga-386, svga-pentium, headless) → symlinks to preset
  --log-int21, --log-fileio → enable DOSBox-X internal logging

Outputs:
- Paths to artifacts (dosbox-re.conf symlink or generated, log.txt / int21.log, manual *.bin dumps, *.png screenshots)
- Markdown report: config/commands used, run summary, key observations
- Ready next steps (e.g., "@llama use dos_memory_arena_analyzer on lowmem.bin")

AXE-specific notes:
- Workspace = current dir (sandboxed via bwrap).
- Presets live in /tools/dosbox-presets/ (use symlinks for speed/reuse).
- DOSBox-X in PATH.
- Automated = headless by default (fast, no video/sound).
- Interactive = video window + sound + debugger access.

Step-by-step workflow (follow precisely):

1. Determine mode:
   - interactive_mode = true if --interactive or any --dump* flag or no --headless explicit
   - automated_mode = else (headless)

2. Config handling:
   - If --preset <name> provided:
        ln -sf /tools/dosbox-presets/${name}.conf dosbox-re.conf
        echo "Symlinked preset: ${name}"
   - Else if automated_mode:
        ln -sf /tools/dosbox-presets/headless-re.conf dosbox-re.conf
        echo "Defaulted to headless preset"
   - Else (interactive, no preset):
        Generate fresh dosbox-re.conf with full modern settings:
        [dosbox]
        machine=svga_s3
        memsize=64
        vmemsize=8
        cycles=max

        [cpu]
        core=dynamic
        cputype=pentium

        [dos]
        xms=true
        ems=true
        umb=true

        [sdl]
        output=surface
        fullscreen=false

        [mixer]
        nosound=false
        rate=49716

        [sblaster]
        sbtype=sb16
        oplmode=auto

        [render]
        aspect=true

        [speaker]
        pcspeaker=true

        [autoexec] (see below)

3. [autoexec] section (always added/overwritten):
   mount c .
   c:
   cls
   echo DOSBox-X RE session ready.

   If interactive_mode:
   echo === INTERACTIVE MODE ===
   echo Press debugger hotkey (common: Ctrl+Alt+F9, Alt+Pause, or check mapper.txt) for console.
   echo Memory dump commands:
   echo   MEMDUMPBIN 0 A0000 lowmem.bin     (~640KB conventional)
   echo   MEMDUMPBIN 0 100000 fullmem.bin   (full 1MB)
   echo SCREENSHOT: Host hotkey Ctrl+F5 → saves screenshotXXXX.png in workspace
   echo After actions: type C to continue, or exit DOSBox when done.

   If custom --cycles <n>:
      Add to autoexec: CYCLES <n>

4. Build command:
   base: dosbox-x -conf dosbox-re.conf -fastlaunch

   If --log-int21: append -log-int21
   If --log-fileio: append -log-fileio

   If target.exe provided: append -c "target.exe"

   If --brief-run: append -c "target.exe" -c "echo Brief run complete - open debugger now for post-load dump/state"

   If automated_mode: append -exit

   Redirect: > log.txt 2>&1
   (If heavy logging: > int21_trace.log 2>&1)

5. Execute the full command.

6. Post-run:
   - Grep log.txt for errors/startup info.
   - List new artifacts (ls *.bin *.png log.txt).
   - If interactive: remind manual actions needed for dumps/screenshots.

7. Final report (Markdown):
   - Mode used (automated/headless or interactive)
   - Preset used (or "generated fresh")
   - Full command and key config sections
   - Artifacts list
   - Observations from log.txt
   - Next steps:
     Automated → "Check log.txt; if INT21 logged → grep for file opens"
     Interactive → "Manual dumps/screenshots ready → @llama use dos_memory_arena_analyzer on lowmem.bin"

Example chains:
@llama use dosbox_emulation_setup --preset ega-286 --interactive AR/AR.EXE
→ Era-accurate interactive run with screenshots/debugger

@llama use dosbox_emulation_setup --preset headless --log-int21 --run-and-exit AR/AR.EXE
→ Fast headless INT21 trace for file I/O

@llama use dosbox_emulation_setup --dump-low-memory
→ Interactive clean memory dump (no preset, full video)