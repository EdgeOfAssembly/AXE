# LLM-Ready Codebase Overview — 2026-01-01

**Project:** AXE

## Directory Structure

```text
.
├── core
│   ├── __init__.py
│   └── multiprocess.py
├── database
│   ├── agent_db.py
│   ├── __init__.py
│   └── schema.py
├── llm_prep
│   ├── dot_graphs_doxygen
│   ├── dot_graphs_pyreverse
│   │   └── classes.dot
│   ├── codebase_overview.md
│   ├── codebase_stats.txt
│   ├── codebase_structure.txt
│   ├── codebase_structure_updated.txt
│   ├── llm_system_prompt.md
│   ├── project_guidance.md
│   └── tags
├── models
│   ├── __init__.py
│   └── metadata.py
├── progression
│   ├── __init__.py
│   ├── levels.py
│   └── xp_system.py
├── safety
│   ├── __init__.py
│   └── rules.py
├── team_test
├── utils
│   ├── formatting.py
│   ├── __init__.py
│   └── token_tracker.py
├── API_PROVIDERS.md
├── axe_agents.db
├── axe_agents.db-shm
├── axe_agents.db-wal
├── axe.py
├── axe.yaml
├── demo_improvements.py
├── IMPLEMENTATION_COMPLETE.md
├── IMPROVEMENTS_FINAL.md
├── IMPROVEMENTS_README.md
├── LICENSE
├── MODELS_FINAL.md
├── QUICK_REFERENCE.md
├── README.md
├── REFACTORING_NOTES.md
├── requirements.txt
└── test_axe_improvements.py

11 directories, 40 files
```

## Code Statistics

```text
github.com/AlDanial/cloc v 2.00  T=0.05 s (673.3 files/s, 191654.1 lines/s)
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
Python                          18            999           1262           3338
Markdown                        13            893              0           2662
YAML                             1             99             40            571
Text                             3              2              0             96
-------------------------------------------------------------------------------
SUM:                            35           1993           1302           6667
-------------------------------------------------------------------------------
```

## Python Class Diagrams (pyreverse)

- `classes.dot`

## Symbol Index

- `llm_prep/tags` - ctags file for symbol navigation

## LLM Context Files

- `llm_system_prompt.md` - System prompt for LLM sessions
- `project_guidance.md` - Best practices and guidelines

## How to Use

1. Copy this file as initial context for your LLM
2. Paste relevant DOT graphs for architecture questions
3. Reference specific files when asking about code
