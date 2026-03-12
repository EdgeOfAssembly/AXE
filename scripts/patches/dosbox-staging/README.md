# scripts/patches/dosbox-staging/

Patch files applied by `scripts/setup_env.sh` to
`EdgeOfAssembly/dosbox-staging` after cloning, before building.

Applied in numbered order via `git apply --whitespace=fix <patch>`.

| File | What it fixes |
|------|---------------|
| `0001-guard-opengl-link.patch` | `src/gui/CMakeLists.txt` — OpenGL::GL was unconditionally linked even when `OPT_OPENGL=OFF`. Wraps it in a generator expression. |
| `0002-fix-zlib-ng-cmakedefine01.patch` | `src/libs/zmbv/zmbv.h` — `#if defined(C_SYSTEM_ZLIB_NG)` always true because `#cmakedefine01` emits `#define X 0`. Changed to `#if C_SYSTEM_ZLIB_NG`. |
| `0003-guard-fluidsynth-midi.patch` | `src/midi/CMakeLists.txt` — `fluidsynth.cpp` compiled and `FluidSynth::libfluidsynth` linked even when `OPT_FLUIDSYNTH=OFF`. Guards both. |
| `0004-add-c-fluidsynth-cmakedefine.patch` | `CMakeLists.txt` + `src/dosbox_config.h.in.cmake` — adds `C_FLUIDSYNTH` cmake variable and config-header define so source guards work. |
| `0005-guard-fluidsynth-source.patch` | `src/dosbox.cpp` + `src/midi/midi.cpp` — wraps all `FSYNTH_*` symbol references in `#if C_FLUIDSYNTH`. |
| `0006-debugtrace-conf-trace-off-dedup-on.patch` | `dosbox-staging.conf` — disables `trace_instructions` (keeps text log small); enables all `deduplicate_*` options; enables binary opcode dump. |

## Re-applying manually

```bash
cd tools/dosbox-staging
for p in ../../scripts/patches/dosbox-staging/*.patch; do
    git apply --whitespace=fix "$p" && echo "Applied: $p" || echo "SKIP (already applied?): $p"
done
```
