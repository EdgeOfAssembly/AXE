# LLM-Ready Codebase Overview — 2026-01-13

**Project:** AXE

## Directory Structure

```text
.
├── claude
│   ├── ocr_out
│   ├── Agent Skills - Claude Docs.pdf
│   ├── Bash tool - Claude Docs.pdf
│   ├── Batch processing - Claude Docs.pdf
│   ├── Building with extended thinking - Claude Docs.pdf
│   ├── Chain complex prompts for stronger performance - Claude Docs.pdf
│   ├── Code execution tool - Claude Docs.pdf
│   ├── Computer use tool - Claude Docs.pdf
│   ├── Context editing - Claude Docs.pdf
│   ├── Extended thinking tips - Claude Docs.pdf
│   ├── Files API - Claude Docs.pdf
│   ├── Get started with Agent Skills in the API - Claude Docs.pdf
│   ├── Giving Claude a role with a system prompt - Claude Docs.pdf
│   ├── How to implement tool use - Claude Docs.pdf
│   ├── Let Claude think (chain of thought prompting) to increase performance - Claude Docs.pdf
│   ├── Long context prompting tips - Claude Docs.pdf
│   ├── Memory tool - Claude Docs.pdf
│   ├── Multilingual support - Claude Docs.pdf
│   ├── pdfocr.py
│   ├── PDF support - Claude Docs.pdf
│   ├── Pricing - Claude Docs.pdf
│   ├── Programmatic tool calling - Claude Docs.pdf
│   ├── Prompt caching - Claude Docs.pdf
│   ├── Prompt engineering overview - Claude Docs.pdf
│   ├── Skill authoring best practices - Claude Docs.pdf
│   ├── Text editor tool - Claude Docs.pdf
│   ├── Token counting - Claude Docs.pdf
│   ├── Tool search tool - Claude Docs.pdf
│   ├── Use XML tags to structure your prompts - Claude Docs.pdf
│   ├── Using Agent Skills with the API - Claude Docs.pdf
│   ├── Vision - Claude Docs.pdf
│   ├── Web fetch tool - Claude Docs.pdf
│   └── Web search tool - Claude Docs.pdf
├── core
│   ├── agent_manager.py
│   ├── config.py
│   ├── constants.py
│   ├── __init__.py
│   ├── multiprocess.py
│   ├── resource_monitor.py
│   ├── sandbox.py
│   ├── session_manager.py
│   └── tool_runner.py
├── database
│   ├── agent_db.py
│   ├── __init__.py
│   └── schema.py
├── docs
│   └── diagrams
│       ├── call_graph.dot
│       ├── class_diagram.dot
│       ├── module_dependencies.dot
│       └── README.md
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
├── managers
│   ├── break_system.py
│   ├── dynamic_spawner.py
│   ├── emergency_mailbox.py
│   ├── __init__.py
│   └── sleep_manager.py
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
├── tests
│   ├── test_absolute_path_fix.py
│   ├── test_analysis_tools.py
│   ├── test_axe_improvements.py
│   ├── test_collab_tool_syntax.py
│   ├── test_database_location.py
│   ├── test_detect_agent_token.py
│   ├── test_double_execution.py
│   ├── test_dynamic_max_tokens.py
│   ├── test_exec_heredoc.py
│   ├── test_heredoc_execution_fix.py
│   ├── test_heredoc_parsing.py
│   ├── test_inline_exec_blocks.py
│   ├── test_integration_bug_fix.py
│   ├── test_integration_database_fix.py
│   ├── test_mission_md_tokens.py
│   ├── test_models_yaml.py
│   ├── test_sandbox.py
│   ├── test_spawned_agents.py
│   ├── test_supervisor_protections.py
│   ├── test_task_completion_detection.py
│   ├── test_token_error_handling.py
│   ├── test_token_optimization.py
│   ├── test_tool_runner_edge_cases.py
│   ├── test_tool_runner.py
│   ├── test_workshop_cli_integration.py
│   ├── test_workshop_integration.py
│   ├── test_workshop_pr23_validation.py
│   ├── test_workshop.py
│   ├── test_write_blocks.py
│   ├── test_xml_new_formats.py
│   └── test_xml_tool_parser.py
├── tools
│   ├── build_analyzer.py
│   ├── __init__.py
│   └── llmprep.py
├── utils
│   ├── context_optimizer.py
│   ├── formatting.py
│   ├── __init__.py
│   ├── prompt_compressor.py
│   ├── rate_limiter.py
│   ├── token_stats.py
│   └── xml_tool_parser.py
├── workshop
│   ├── chisel.py
│   ├── hammer.py
│   ├── __init__.py
│   ├── plane.py
│   └── saw.py
├── ABSOLUTE_PATH_FIX_SUMMARY.md
├── API_PROVIDERS.md
├── ARCHITECTURE.md
├── axe.py
├── axe.yaml
├── BEFORE_AFTER_COMPARISON.md
├── BUG_FIX_SUMMARY.md
├── COLLAB_TOOL_SYNTAX_FIX_SUMMARY.md
├── DATABASE_LOCATION_FIX_SUMMARY.md
├── demo_absolute_path_fix.py
├── demo_dynamic_tokens.py
├── demo_heredoc_fix.py
├── demo_improvements.py
├── demo_task_completion_fix.py
├── DUPLICATE_EXECUTION_FIX_SUMMARY.md
├── DYNAMIC_TOKENS_SUMMARY.md
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
├── models.yaml
├── MULTI_FORMAT_PARSER_IMPLEMENTATION.md
├── MULTI_FORMAT_PARSER_QUICK_REFERENCE.md
├── PR23_EXECUTIVE_SUMMARY.md
├── PR23_VALIDATION_REPORT.md
├── QUICK_REFERENCE.md
├── README.md
├── REFACTORING_NOTES.md
├── requirements.txt
├── SANDBOX_IMPLEMENTATION_SUMMARY.md
├── SANDBOX.md
├── SECURITY_REPORT.md
├── SHELL_OPERATOR_SUPPORT_SUMMARY.md
├── TASK_COMPLETION_FIX_SUMMARY.md
├── workshop_benchmarks.md
├── workshop_dependency_validation.md
├── workshop_quick_reference.md
├── workshop_security_audit.md
├── workshop_test_results.md
├── WRITE_BLOCKS_GUIDE.md
├── XML_PARSER_IMPLEMENTATION.md
└── XML_PARSER_QUICK_REFERENCE.md

18 directories, 164 files
```

## Code Statistics

```text
github.com/AlDanial/cloc v 2.00  T=0.18 s (689.4 files/s, 202321.1 lines/s)
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
Python                          79           4611           5230          13532
Markdown                        43           2703              0           8984
YAML                             2            447             90           1442
Text                             3              2              0            232
-------------------------------------------------------------------------------
SUM:                           127           7763           5320          24190
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
