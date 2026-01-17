# DOS EXE Unpackers

Collection of simple tools for unpacking common DOS executable packers (LZEXE, EXEPACK, PKLITE). These are useful for reverse engineering old MS-DOS games and tools before disassembly/analysis.

These are integrated as source code so the repo stays self-contained.

### Build Instructions
You need gcc (standard on most Linux distros).

```bash
cd tools/dos_unpackers
make          # builds unlzexe, unexepack, depklite
```

Binaries will appear in this directory. Add it to your PATH or call them with relative paths from AXE agents/scripts.

### Usage Examples
- ./unlzexe packed.exe → creates unpacked version (usually with -unlzexe suffix)
- ./unexepack packed.exe → creates "unpacked" by default
- ./depklite packed.exe → creates packed.exe.dep (extracted data)

### Attributions & Credits
These tools are ports/adaptations of classic unpackers. Big thanks to the original authors and maintainers:

- **unlzexe**: Based on work by Fabrice Bellard and Mitugu Kurizono. Linux port by mywave82[](https://github.com/mywave82/unlzexe).
- **unexepack**: By w4kfu[](https://github.com/w4kfu/unEXEPACK). Handles Microsoft EXEPACK.
- **depklite**: By hackerb9[](https://github.com/hackerb9/depklite). MIT licensed. Extracts PKLITE-compressed data—great for RE.

Huge respect to these folks and the retro RE community for keeping old DOS stuff accessible!

