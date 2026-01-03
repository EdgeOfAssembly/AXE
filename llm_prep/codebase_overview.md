# LLM-Ready Codebase Overview — 2026-01-04

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
│   ├── token_tracker.py
│   └── xml_tool_parser.py
├── workshop
│   ├── chisel.py
│   ├── hammer.py
│   ├── __init__.py
│   ├── plane.py
│   └── saw.py
├── ABSOLUTE_PATH_FIX_SUMMARY.md
├── API_PROVIDERS.md
├── axe.py
├── axe.yaml
├── BEFORE_AFTER_COMPARISON.md
├── BUG_FIX_SUMMARY.md
├── COLLAB_TOOL_SYNTAX_FIX_SUMMARY.md
├── DATABASE_LOCATION_FIX_SUMMARY.md
├── demo_absolute_path_fix.py
├── demo_heredoc_fix.py
├── demo_improvements.py
├── demo_task_completion_fix.py
├── DUPLICATE_EXECUTION_FIX_SUMMARY.md
├── FIXES_SUMMARY.md
├── HEREDOC_EXECUTION_FIX.md
├── HEREDOC_EXECUTION_FIX_SUMMARY.md
├── IMPLEMENTATION_COMPLETE.md
├── IMPLEMENTATION_SUMMARY.md
├── IMPROVEMENTS_FINAL.md
├── IMPROVEMENTS_README.md
├── LICENSE
├── manual_test_write.py
├── manual_test_xml.py
├── MISSION.md
├── MODELS_FINAL.md
├── MULTI_FORMAT_PARSER_IMPLEMENTATION.md
├── MULTI_FORMAT_PARSER_QUICK_REFERENCE.md
├── PR23_EXECUTIVE_SUMMARY.md
├── PR23_VALIDATION_REPORT.md
├── QUICK_REFERENCE.md
├── README.md
├── REFACTORING_NOTES.md
├── requirements.txt
├── SHELL_OPERATOR_SUPPORT_SUMMARY.md
├── TASK_COMPLETION_FIX_SUMMARY.md
├── test_absolute_path_fix.py
├── test_axe_improvements.py
├── test_collab_tool_syntax.py
├── test_database_location.py
├── test_detect_agent_token.py
├── test_double_execution.py
├── test_exec_heredoc.py
├── test_heredoc_execution_fix.py
├── test_heredoc_parsing.py
├── test_inline_exec_blocks.py
├── test_integration_bug_fix.py
├── test_integration_database_fix.py
├── test_mission_md_tokens.py
├── test_spawned_agents.py
├── test_supervisor_protections.py
├── test_task_completion_detection.py
├── test_token_error_handling.py
├── test_tool_runner_edge_cases.py
├── test_tool_runner.py
├── test_workshop_cli_integration.py
├── test_workshop_integration.py
├── test_workshop_pr23_validation.py
├── test_workshop.py
├── test_write_blocks.py
├── test_xml_new_formats.py
├── test_xml_tool_parser.py
├── workshop_benchmarks.md
├── workshop_dependency_validation.md
├── workshop_quick_reference.md
├── workshop_security_audit.md
├── workshop_test_results.md
├── WRITE_BLOCKS_GUIDE.md
├── XML_PARSER_IMPLEMENTATION.md
└── XML_PARSER_QUICK_REFERENCE.md

12 directories, 98 files
```

## Code Statistics

```text
github.com/AlDanial/cloc v 2.00  T=0.16 s (625.8 files/s, 218647.0 lines/s)
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
Markdown                        39           4060              0          12128
Python                          54           3374           3967           9449
YAML                             1            104             46            604
Text                             3              2              0            158
-------------------------------------------------------------------------------
SUM:                            97           7540           4013          22339
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
