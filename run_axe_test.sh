#!/bin/bash
# Simplified AXE Multi-Agent Test Script
# Tests PR #18 and #20 fixes with a mock wadextract-like project

set -e

# Check for required API keys (should be set in environment)
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$HUGGINGFACE_API_KEY" ]; then
    echo "ERROR: No API keys found. Please set at least one of:"
    echo "  ANTHROPIC_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY"
    exit 1
fi

echo "=== AXE Multi-Agent Test Setup ==="
echo "Date: $(date)"
echo ""

# Setup workspace
WORKSPACE="/tmp/wadextract_test"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"

# Create a mock wadextract project
echo "Creating mock wadextract project..."

# Create wadextract.c
cat > "$WORKSPACE/wadextract.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Simple WAD extractor mock for testing
typedef enum {
    SECTION_NONE = 0,
    SECTION_SPRITES,
    SECTION_PATCHES,
    SECTION_FLATS
} SectionType;

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: wadextract [OPTIONS] WADFILE\n");
        printf("Options:\n");
        printf("  -h          Show this help\n");
        printf("  -l          List contents\n");
        printf("  -x          Extract files\n");
        printf("  -r TYPE     Resource type (sprite, graphic, flat)\n");
        printf("  -O DIR      Output directory\n");
        return 0;
    }
    
    if (strcmp(argv[1], "-h") == 0) {
        printf("WAD Extractor v1.0\n");
        printf("Extracts assets from Doom/Heretic/Hexen/Strife WAD files\n");
        return 0;
    }
    
    // Mock extraction logic
    printf("WAD file: %s\n", argv[argc-1]);
    printf("Extraction completed!\n");
    
    return 0;
}
EOF

# Create Makefile
cat > "$WORKSPACE/Makefile" << 'EOF'
CC=gcc
CFLAGS=-Wall -O2

wadextract: wadextract.c
	$(CC) $(CFLAGS) -o wadextract wadextract.c

clean:
	rm -f wadextract

.PHONY: clean
EOF

# Create usage.txt
cat > "$WORKSPACE/usage.txt" << 'EOF'
WAD Extractor Usage Guide

SYNOPSIS
    wadextract [OPTIONS] WADFILE

DESCRIPTION
    Extracts assets (sprites, graphics, flats) from Doom-engine WAD files.

OPTIONS
    -h              Show help
    -l              List all lumps in WAD file
    -x              Extract mode
    -r TYPE         Filter by resource type: sprite, graphic, flat
    -O DIR          Output directory for extracted files

EXAMPLES
    # List contents
    ./wadextract DOOM.WAD -l
    
    # Extract all sprites
    ./wadextract DOOM.WAD -x -r sprite -O sprites/
    
    # Extract all graphics  
    ./wadextract DOOM.WAD -x -r graphic -O graphics/

SUPPORTED GAMES
    - Doom (1993)
    - Doom II (1994)
    - Heretic (1994)
    - Hexen (1995)
    - Strife (1996)
EOF

# Create common.h
cat > "$WORKSPACE/common.h" << 'EOF'
#ifndef COMMON_H
#define COMMON_H

#define WAD_MAGIC_IWAD 0x44415749
#define WAD_MAGIC_PWAD 0x44415750

typedef struct {
    unsigned int magic;
    unsigned int num_lumps;
    unsigned int dir_offset;
} wad_header_t;

#endif
EOF

# Create png.h
cat > "$WORKSPACE/png.h" << 'EOF'
#ifndef PNG_H
#define PNG_H

int write_png(const char *filename, unsigned char *data, int width, int height);

#endif
EOF

echo "Mock project created in $WORKSPACE"
ls -la "$WORKSPACE"

# Run AXE in collaborative mode
echo ""
echo "=== Starting AXE Collaborative Mode ==="
echo "Agents: claude,gpt"
echo "Time limit: 5 minutes (for quick test)"
echo ""

cd /home/runner/work/AXE/AXE

# Run with short time limit for testing
./axe.py --collab claude,gpt \
         --workspace "$WORKSPACE" \
         --time 5 \
         --task "Complete these tasks for the wadextract tool:

1. READ all source files to understand the codebase (wadextract.c, Makefile, usage.txt, common.h, png.h)

2. COMPILE the tool using 'make' and verify it builds successfully

3. RUN the tool:
   - Run: ./wadextract -h (show help)
   - Run: ./wadextract test.wad (test basic functionality)

4. CREATE a README.md file that includes:
   - Project description (Doom/Heretic/Hexen/Strife WAD asset extractor)
   - Build instructions from the Makefile
   - Usage examples from usage.txt
   - Supported games and features

5. CREATE a TEST_REPORT.md file that includes:
   - Did compilation succeed? 
   - Did the program run successfully?
   - Were README.md and TEST_REPORT.md files created?
   - List all files in the workspace with 'ls -la'
   - Any issues or bugs found?

IMPORTANT: Use <exec>command</exec>, <read>file</read>, and <write file=\"path\">content</write> tags to perform your tasks."

echo ""
echo "=== AXE Test Completed ==="
echo ""
echo "Results are in: $WORKSPACE"
echo ""
echo "Checking for created files..."
ls -la "$WORKSPACE"
echo ""

if [ -f "$WORKSPACE/README.md" ]; then
    echo "✅ README.md was created"
else
    echo "❌ README.md was NOT created"
fi

if [ -f "$WORKSPACE/TEST_REPORT.md" ]; then
    echo "✅ TEST_REPORT.md was created"
else
    echo "❌ TEST_REPORT.md was NOT created"
fi

if [ -f "$WORKSPACE/wadextract" ]; then
    echo "✅ wadextract binary was compiled"
else
    echo "❌ wadextract binary was NOT compiled"
fi

echo ""
echo "Check the collaboration log at: $WORKSPACE/.collab_log.md"
