; dos_sample.asm – minimal 16-bit real-mode MS-DOS EXE stub.
;
; Purpose: fixture for AXE reverse-engineering tests.  Demonstrates classic
; DOS patterns: INT 21h service calls, segment register setup, and simple
; string output – the kinds of constructs an x86 RE agent should recognise
; and annotate correctly.
;
; Assembled with NASM:
;   nasm -f bin -o dos_sample.com dos_sample.asm
;
; Note: assembled as a .COM (flat binary) for simplicity; the same patterns
; appear in real MZ EXE files.  For proper MZ EXE tests use the BBS samples
; from EdgeOfAssembly/HaxBox.

    org 100h                    ; COM programs start at CS:0100

start:
    ; Set DS = CS (already true for COM, but explicit for clarity)
    push    cs
    pop     ds

    ; Print greeting via INT 21h / AH=09h (print $-terminated string)
    mov     ah, 09h
    lea     dx, [msg_hello]
    int     21h

    ; Read a single character (AH=01h) to pause before exit
    mov     ah, 01h
    int     21h

    ; Exit via INT 21h / AH=4Ch, return code 0
    mov     ah, 4Ch
    xor     al, al
    int     21h

; ---------------------------------------------------------------------------
; Data section
; ---------------------------------------------------------------------------
msg_hello   db  'Hello from 16-bit DOS!', 0Dh, 0Ah, '$'
