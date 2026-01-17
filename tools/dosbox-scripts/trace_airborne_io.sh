#!/bin/bash
# Headless INT21 trace
ln -sf /tools/dosbox-presets/headless-re.conf dosbox-re.conf
dosbox-x -conf dosbox-re.conf -fastlaunch -log-int21 -log-fileio -exit AR/AR.EXE > int21_trace.log 2>&1
echo "Trace complete → int21_trace.log"
grep -i "open\|3d\|file" int21_trace.log