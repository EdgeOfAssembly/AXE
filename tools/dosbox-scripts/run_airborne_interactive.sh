#!/bin/bash
# Quick interactive run with EGA preset
ln -sf /tools/dosbox-presets/ega-286.conf dosbox-re.conf
echo "EGA 286 preset linked"
dosbox-x -conf dosbox-re.conf -fastlaunch AR/AR.EXE > log.txt 2>&1