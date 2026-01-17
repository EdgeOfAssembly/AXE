Skill: dosbox_screenshot
Category: DOS-specific Reverse Engineering / Emulation

Purpose: Capture VGA screenshots during interactive session (host hotkey—automated video dump hard without external tools).

Workflow:
1. Start interactive: @llama use dosbox_emulation_setup --interactive --preset ega-286 AR/AR.EXE
2. Play/navigate to desired screen (title, mission brief, etc.)
3. Press host hotkey Ctrl + F5 → saves screenshot0001.png etc. in workspace
4. Repeat as needed, exit when done.
5. List: ls *.png

Note: For batch, run multiple sessions or manual timing.