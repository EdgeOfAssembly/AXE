Skill: trace_execution_path
Category: Legacy Code Archaeology
Recommended agents: llama (main), claude (review)
Purpose: Follow control flow from given entry point (direct calls, jumps, far jumps, indirect branches, interrupt chains)

Typical inputs: Entry address/label, disassembly, debugger trace
Outputs: Linear + branching path description (text + optional ASCII diagram)
AXE focus: Real-mode DOS, far pointers, overlay switching, int 21h/2Fh dispatch