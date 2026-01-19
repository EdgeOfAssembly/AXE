# LLM-Ready Codebase Overview — 2026-01-19

**Project:** AXE

## Directory Structure

```text
.
├── claude
│   ├── ocr_out
│   │   ├── Agent Skills - Claude Docs.txt
│   │   ├── Bash tool - Claude Docs.txt
│   │   ├── Batch processing - Claude Docs.txt
│   │   ├── Building with extended thinking - Claude Docs.txt
│   │   ├── Chain complex prompts for stronger performance - Claude Docs.txt
│   │   ├── Code execution tool - Claude Docs.txt
│   │   ├── Computer use tool - Claude Docs.txt
│   │   ├── Context editing - Claude Docs.txt
│   │   ├── Extended thinking tips - Claude Docs.txt
│   │   ├── Files API - Claude Docs.txt
│   │   ├── Get started with Agent Skills in the API - Claude Docs.txt
│   │   ├── Giving Claude a role with a system prompt - Claude Docs.txt
│   │   ├── How to implement tool use - Claude Docs.txt
│   │   ├── Let Claude think (chain of thought prompting) to increase performance - Claude Docs.txt
│   │   ├── Long context prompting tips - Claude Docs.txt
│   │   ├── Memory tool - Claude Docs.txt
│   │   ├── Multilingual support - Claude Docs.txt
│   │   ├── PDF support - Claude Docs.txt
│   │   ├── Pricing - Claude Docs.txt
│   │   ├── Programmatic tool calling - Claude Docs.txt
│   │   ├── Prompt caching - Claude Docs.txt
│   │   ├── Prompt engineering overview - Claude Docs.txt
│   │   ├── Skill authoring best practices - Claude Docs.txt
│   │   ├── Text editor tool - Claude Docs.txt
│   │   ├── Token counting - Claude Docs.txt
│   │   ├── Tool search tool - Claude Docs.txt
│   │   ├── Use XML tags to structure your prompts - Claude Docs.txt
│   │   ├── Using Agent Skills with the API - Claude Docs.txt
│   │   ├── Vision - Claude Docs.txt
│   │   ├── Web fetch tool - Claude Docs.txt
│   │   └── Web search tool - Claude Docs.txt
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
│   ├── acp_validator.py
│   ├── agent_manager.py
│   ├── anthropic_features.py
│   ├── config.py
│   ├── constants.py
│   ├── environment_probe.py
│   ├── github_agent.py
│   ├── __init__.py
│   ├── multiprocess.py
│   ├── resource_monitor.py
│   ├── sandbox.py
│   ├── session_manager.py
│   ├── session_preprocessor.py
│   ├── skills_manager.py
│   └── tool_runner.py
├── data
│   ├── create_abbreviations_db.py
│   └── it_abbreviations.db
├── database
│   ├── agent_db.py
│   ├── __init__.py
│   └── schema.py
├── docs
│   ├── diagrams
│   │   ├── call_graph.dot
│   │   ├── class_diagram.dot
│   │   ├── module_dependencies.dot
│   │   └── README.md
│   ├── ANTHROPIC_FEATURES.md
│   └── GITHUB_AGENT_INTEGRATION.md
├── examples
│   └── anthropic_features_demo.py
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
│   ├── shared_build_status.py
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
├── scripts
│   └── benchmark_acp.py
├── skills
│   ├── boot_flow_reconstruction.md
│   ├── build.md
│   ├── claude_build.md
│   ├── c_modernization_expert.md
│   ├── cpp_modernization_expert.md
│   ├── cpp_refactoring_expert.md
│   ├── deep_dive_function.md
│   ├── dosbox_emulation_setup.md
│   ├── dosbox_int21_trace.md
│   ├── dosbox_memory_dump.md
│   ├── dosbox_screenshot.md
│   ├── dos_exe_unpack.md
│   ├── dos_memory_arena_analyzer.md
│   ├── dos_packer_detector.md
│   ├── find_entry_points.md
│   ├── firmware_binwalk_scan.md
│   ├── firmware_entropy_analyzer.md
│   ├── firmware_extract_components.md
│   ├── firmware_header_identify.md
│   ├── ida_pro_analysis_patterns.md
│   ├── indirect_flow_hunter.md
│   ├── manifest.json
│   ├── map_data_flows.md
│   ├── peripheral_register_patterns.md
│   ├── python_agent_expert.md
│   ├── recover_high_level_model.md
│   ├── reverse_engineering_expert.md
│   ├── trace_execution_path.md
│   └── x86_assembly_expert.md
├── tests
│   ├── MISSION.md
│   ├── test_absolute_path_fix.py
│   ├── test_acp_benchmark.py
│   ├── test_analysis_tools.py
│   ├── test_anthropic_features.py
│   ├── test_anthropic_integration.py
│   ├── test_axe_improvements.py
│   ├── test_collab_tool_syntax.py
│   ├── test_database_location.py
│   ├── test_detect_agent_token.py
│   ├── test_double_execution.py
│   ├── test_dynamic_max_tokens.py
│   ├── test_efficiency_analysis.py
│   ├── test_environment_probe.py
│   ├── test_exec_heredoc.py
│   ├── test_github_agent.py
│   ├── test_heredoc_execution_fix.py
│   ├── test_heredoc_parsing.py
│   ├── test_inline_exec_blocks.py
│   ├── test_integration_bug_fix.py
│   ├── test_integration_database_fix.py
│   ├── test_large_code_files.py
│   ├── test_minifier.py
│   ├── test_mission_md_tokens.py
│   ├── test_models_yaml.py
│   ├── test_sandbox.py
│   ├── test_session_preprocessor.py
│   ├── test_shared_build_status.py
│   ├── test_silent_builds.py
│   ├── test_skills_manager.py
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
│   ├── dosbox-presets
│   │   ├── cga-8086.conf
│   │   ├── ega-286.conf
│   │   ├── headless-re.conf
│   │   ├── re-base.conf
│   │   ├── svga-pentium.conf
│   │   └── vga-386.conf
│   ├── dosbox-scripts
│   │   ├── run_airborne_interactive.sh
│   │   └── trace_airborne_io.sh
│   ├── dos_unpackers
│   │   ├── depklite.c
│   │   ├── depklite.h
│   │   ├── Makefile
│   │   ├── README.md
│   │   ├── unlzexe.c
│   │   └── unpack.c
│   ├── build_analyzer.py
│   ├── __init__.py
│   ├── llmprep.py
│   ├── minifier.py
│   └── mkpyenv
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
├── AGENTS.md
├── ANTHROPIC_IMPLEMENTATION_SUMMARY.md
├── API_PROVIDERS.md
├── ARCHITECTURE.md
├── axe_agents.db
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
├── demo_minifier.py
├── demo_skills_system.py
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
├── MINIFIER_IMPLEMENTATION_SUMMARY.md
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
├── SILENT_BUILDS_IMPLEMENTATION.md
├── SKILLS_SYSTEM_IMPLEMENTATION_SUMMARY.md
├── TASK_COMPLETION_FIX_SUMMARY.md
├── workshop_benchmarks.md
├── workshop_dependency_validation.md
├── workshop_quick_reference.md
├── workshop_security_audit.md
├── workshop_test_results.md
├── WRITE_BLOCKS_GUIDE.md
├── XML_PARSER_IMPLEMENTATION.md
└── XML_PARSER_QUICK_REFERENCE.md

25 directories, 274 files
```

## Code Statistics

```text
github.com/AlDanial/cloc v 2.00  T=0.30 s (777.1 files/s, 258129.5 lines/s)
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
Text                            34            391              0          23633
Python                         104           6531           7479          18723
Markdown                        81           3513              0          11770
YAML                             3            684            120           1754
C                                3            169            186           1330
JSON                             1              0              0             61
C/C++ Header                     1              7              4             19
make                             1              6              0             12
Bourne Shell                     2              0              2              9
-------------------------------------------------------------------------------
SUM:                           230          11301           7791          57311
-------------------------------------------------------------------------------
```

## Doxygen Documentation (C/C++)

- Browse: `llm_prep/doxygen_output/html/index.html`
- DOT graphs for LLM context:
  - `classaxe_1_1ChatSession__coll__graph.dot` (16 KB)
  - `classaxe_1_1ChatSession_a049b421bf07ed70e7e7f3aa6b33a6dda_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a0ab519e1dc9929cad872bce563497494_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a292849d40a6711c7b6d7452667c55458_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a29a1bebc11983c09ab80e80476390355_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a49ed0956e4c1d34d14ff8eabe273389a_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a5193da01e07e92935883879a4b787cba_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a5a74e53da64988a363d8ebb226f8305a_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a5ae75ad1fa38a10487d6b6e5e4db8710_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a5e97c8f1a8d0df56f1c861ac553378ff_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a6888eced2d3409274af2f4ebe408deaf_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a68cb42802ab49b009bbfc87e9d7e8f78_cgraph.dot` (8 KB)
  - `classaxe_1_1ChatSession_a68cb42802ab49b009bbfc87e9d7e8f78_icgraph.dot` (0 KB)
  - `classaxe_1_1ChatSession_a75658491705b9ea427ddcd85a0795212_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a84bbc5a4a51e722511c2fb80672ec6c2_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a92ba45e5dec2d5bbe7430d2d1302729a_cgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a92ba45e5dec2d5bbe7430d2d1302729a_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_a9d70e5bb01dfd6c8bcef6a86448e5698_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_aaa359a2981c69ef0b93b8b48e259e007_cgraph.dot` (8 KB)
  - `classaxe_1_1ChatSession_aaa359a2981c69ef0b93b8b48e259e007_icgraph.dot` (0 KB)
  - `classaxe_1_1ChatSession_aac98b18a00b50925abec74f75573cffa_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_ab97f8be62dd60678d92c6f18b3e13d50_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_ac4738e0d479152844444fe8c647e3934_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_ad1395c2247996d061ec1a9cc47621bdf_cgraph.dot` (3 KB)
  - `classaxe_1_1ChatSession_ad1395c2247996d061ec1a9cc47621bdf_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_ad6c7e2f347e93cde6d7cf162d49b23ef_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_aeb6da562695cee9b0d73d41956d5e013_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_aec06b2aeb52d5c5cbac6bd9ef969e09d_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_aecfb5d28c9d242bb1d3bbe5d972f5fe5_cgraph.dot` (0 KB)
  - `classaxe_1_1ChatSession_aecfb5d28c9d242bb1d3bbe5d972f5fe5_icgraph.dot` (1 KB)
  - `classaxe_1_1ChatSession_aeff43e85c446ddd0b886d1203875452f_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession__coll__graph.dot` (4 KB)
  - `classaxe_1_1CollaborativeSession_a041ba9ec847ef00ec022b44ad2c5fd88_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_a05dff6155ae4caa7d185d656765b2245_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_a2c0fb59b4465a4f8514630602fa942f8_cgraph.dot` (8 KB)
  - `classaxe_1_1CollaborativeSession_a2c0fb59b4465a4f8514630602fa942f8_icgraph.dot` (0 KB)
  - `classaxe_1_1CollaborativeSession_a38db2f20ab1aba56ecbe35c99c7ccfd2_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_a3e34c26c0de8010ad5878ed3886ee1c9_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_a501edaa48b72d90cc3af128953133578_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_a64377593b620e4449351bb066f04456d_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_a909e359216e70f696e6a51f60a24be7d_cgraph.dot` (0 KB)
  - `classaxe_1_1CollaborativeSession_a909e359216e70f696e6a51f60a24be7d_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ab23535e0d366c892f663caf9b9929bed_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ab9a5670ebe43be16b93f2fc7cad0108e_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ab9b4446c5f6869de5d98eb51d3ab44ef_cgraph.dot` (0 KB)
  - `classaxe_1_1CollaborativeSession_ab9b4446c5f6869de5d98eb51d3ab44ef_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ac268af6bc8cdd91f1868a817b5c5de1b_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ad553b84eeef4e00b661e60f07e20ea1f_icgraph.dot` (2 KB)
  - `classaxe_1_1CollaborativeSession_ad62f87765c49218f37f833f403a9d5e2_cgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ad62f87765c49218f37f833f403a9d5e2_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_adfdeaf4031f6e214d05e21a96d24755a_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_ae5b0476285af0c83e3e1910c1a60e5f6_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_af1293714188297ae8b5cbb4bbba7af67_cgraph.dot` (0 KB)
  - `classaxe_1_1CollaborativeSession_af1293714188297ae8b5cbb4bbba7af67_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_af4ab55de0d7b895c6002cd691b36a9be_cgraph.dot` (8 KB)
  - `classaxe_1_1CollaborativeSession_af7d2acc6e00abc418359198dfe4b019a_icgraph.dot` (1 KB)
  - `classaxe_1_1CollaborativeSession_afb29c1f9e386b7501a35b18e4d4a57cd_cgraph.dot` (2 KB)
  - `classaxe_1_1CollaborativeSession_afb29c1f9e386b7501a35b18e4d4a57cd_icgraph.dot` (1 KB)
  - `classaxe_1_1ProjectContext__coll__graph.dot` (1 KB)
  - `classaxe_1_1ProjectContext_a7f490ff391a06f9a5a91a8804d7c4233_cgraph.dot` (0 KB)
  - `classaxe_1_1ProjectContext_af40ec46de4b7f707ed7f845b7569d9c3_icgraph.dot` (0 KB)
  - `classaxe_1_1ResponseProcessor__coll__graph.dot` (2 KB)
  - `classaxe_1_1ResponseProcessor_a2160dda3d5ede0cf1488d89d8d54f4ba_cgraph.dot` (1 KB)
  - `classaxe_1_1ResponseProcessor_a2160dda3d5ede0cf1488d89d8d54f4ba_icgraph.dot` (0 KB)
  - `classaxe_1_1ResponseProcessor_a3c4cd5b5979bb788ced72a4fd5506c7a_icgraph.dot` (0 KB)
  - `classaxe_1_1ResponseProcessor_aaeacf7e56873f97fea7ea129228f6f6b_cgraph.dot` (1 KB)
  - `classaxe_1_1ResponseProcessor_aaeacf7e56873f97fea7ea129228f6f6b_icgraph.dot` (0 KB)
  - `classaxe_1_1ResponseProcessor_ac1a806aa420d789d964a94a1a5d04219_icgraph.dot` (1 KB)
  - `classaxe_1_1ResponseProcessor_acc32cd3a592012b0f063495b1daa6057_icgraph.dot` (1 KB)
  - `classaxe_1_1ResponseProcessor_aec0d8b41863aebd4e6700db31bd9a88a_cgraph.dot` (2 KB)
  - `classaxe_1_1SharedWorkspace__coll__graph.dot` (3 KB)
  - `classaxe_1_1SharedWorkspace_a3c9dac32f363c049807b783eb4e698ae_icgraph.dot` (1 KB)
  - `classaxe_1_1SharedWorkspace_a70f689883ed3ece23e4304410c51ee54_cgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_a70f689883ed3ece23e4304410c51ee54_icgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_a9010c0a1932f79c76127a0bb238edf7e_cgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_a958844453419f8d9064d52a166875152_cgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_a958844453419f8d9064d52a166875152_icgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_aa80b49ba9c0eb5e692d3898310dfb55e_cgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_aa80b49ba9c0eb5e692d3898310dfb55e_icgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_ab5e70300394328ef57e127c7dd59cace_cgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_ab5e70300394328ef57e127c7dd59cace_icgraph.dot` (0 KB)
  - `classaxe_1_1SharedWorkspace_acef354c98f13dad05822d5f0f0a1d8d5_cgraph.dot` (1 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator__coll__graph.dot` (2 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_a02a900319014a43dfa5082012f2dcba8_cgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_a327d2e974d6665eaf207bb47b2e81c83_icgraph.dot` (2 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_a4cba6fd9f33d0fc17e50901afaf9c848_cgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_a4cba6fd9f33d0fc17e50901afaf9c848_icgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_a948b52fa82a4a216404331d08f9d964e_cgraph.dot` (1 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_aa00c64b4245c4cc8fd7cbd5dedd343b2_cgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_aa00c64b4245c4cc8fd7cbd5dedd343b2_icgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_ad3086273f5a53c8cd4bd89705cd5ef8b_cgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_ad3086273f5a53c8cd4bd89705cd5ef8b_icgraph.dot` (0 KB)
  - `classcore_1_1acp__validator_1_1ACPValidator_af93405c93975a939c3df79141d9b956f_cgraph.dot` (0 KB)
  - `classcore_1_1agent__manager_1_1AgentManager__coll__graph.dot` (2 KB)
  - `classcore_1_1agent__manager_1_1AgentManager_a07fed5fbe9d58078779a04b917ab5f23_cgraph.dot` (1 KB)
  - `classcore_1_1agent__manager_1_1AgentManager_a9723ad2b71e0f7645dfa3903728e8b0c_icgraph.dot` (0 KB)
  - `classcore_1_1agent__manager_1_1AgentManager_aff75497cb51ce30997d46f1d2a5ac5e6_icgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1AnthropicFeatures__coll__graph.dot` (3 KB)
  - `classcore_1_1anthropic__features_1_1AnthropicFeatures_a264f65c13464b92c1ee4945375adb5f9_icgraph.dot` (1 KB)
  - `classcore_1_1anthropic__features_1_1AnthropicFeatures_ac5875c33c281908713873f9268e32fca_cgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1AnthropicFeatures_adcacfe29b8e7accb0eaffb3fb1bb39c7_cgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1AnthropicFeatures_ae4cd2fc680f6eee97b78bf22a249bb50_icgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1AnthropicFeatures_af7670c5e74191a95b3eae8d550839e1a_cgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager__coll__graph.dot` (2 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager_a152fe4d5284b0154eb3ed2127660f000_cgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager_a382ed85a0a1e80116c9e9b66e8f32aa7_cgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager_a99c82d41328c99549d39fc0553df97ff_cgraph.dot` (1 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager_ab869a3faaad1f8aeb4943f5d1d72134d_icgraph.dot` (1 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager_ac508bbb6766908b219a3f3a599eb5869_cgraph.dot` (0 KB)
  - `classcore_1_1anthropic__features_1_1FilesAPIManager_af92bb5475aa459712466b6ad8f7bd409_icgraph.dot` (0 KB)
  - `classcore_1_1config_1_1Config__coll__graph.dot` (1 KB)
  - `classcore_1_1config_1_1Config_a2086d06e50e944500379d84900901e11_icgraph.dot` (0 KB)
  - `classcore_1_1config_1_1Config_a3bdd1ab4ba109d2e3ff70c08ac51b978_cgraph.dot` (0 KB)
  - `classcore_1_1config_1_1Config_ada9632580f9c8bcc926c131b38ddacae_cgraph.dot` (0 KB)
  - `classcore_1_1config_1_1Config_afd6146204f0606fd5189011ca7122d9e_cgraph.dot` (0 KB)
  - `classcore_1_1config_1_1Config_afd6146204f0606fd5189011ca7122d9e_icgraph.dot` (0 KB)
  - `classcore_1_1environment__probe_1_1EnvironmentProbe__coll__graph.dot` (0 KB)
  - `classcore_1_1github__agent_1_1GitHubAgent__coll__graph.dot` (2 KB)
  - `classcore_1_1github__agent_1_1GitHubAgent_a304a9df6d3a2226cc3c8d7cc29894a9c_cgraph.dot` (1 KB)
  - `classcore_1_1github__agent_1_1GitHubAgent_a483a160b7d34753fdaceef1d31976897_icgraph.dot` (0 KB)
  - `classcore_1_1github__agent_1_1GitHubAgent_af3f737af59b8e897b33d680eb5e20e94_icgraph.dot` (0 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess__coll__graph.dot` (2 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess_a31934e365b16de26a030e3a9db2c4868_cgraph.dot` (1 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess_a31934e365b16de26a030e3a9db2c4868_icgraph.dot` (0 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess_a87339d23c63fe1980e98b5de79e24fe2_icgraph.dot` (1 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess_a8a73bda9ba7372bbaecbf6f31c55db71_icgraph.dot` (1 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess_ac3d3e058151e11aa9e6380c218590ce4_cgraph.dot` (1 KB)
  - `classcore_1_1multiprocess_1_1AgentWorkerProcess_acd76bd1ba490767b6cd053d02b609f64_icgraph.dot` (0 KB)
  - `classcore_1_1multiprocess_1_1MultiAgentCoordinator__coll__graph.dot` (2 KB)
  - `classcore_1_1multiprocess_1_1MultiAgentCoordinator_a3c35e80866e317fc554302ff3689b392_cgraph.dot` (0 KB)
  - `classcore_1_1multiprocess_1_1MultiAgentCoordinator_a3c35e80866e317fc554302ff3689b392_icgraph.dot` (0 KB)
  - `classcore_1_1multiprocess_1_1SharedContext__coll__graph.dot` (3 KB)
  - `classcore_1_1multiprocess_1_1SharedContext_a32521b9e5fb36f1979d7f5ae45d1cba5_icgraph.dot` (0 KB)
  - `classcore_1_1multiprocess_1_1SharedContext_add0712b1d658b30d1ecedc78fe234c99_cgraph.dot` (0 KB)
  - `classcore_1_1sandbox_1_1SandboxManager__coll__graph.dot` (2 KB)
  - `classcore_1_1sandbox_1_1SandboxManager_ac935b8aa94fa41939daa96a1866d21aa_icgraph.dot` (0 KB)
  - `classcore_1_1sandbox_1_1SandboxManager_ae0139e54ec4099aafd66e88ad6a2306f_icgraph.dot` (0 KB)
  - `classcore_1_1sandbox_1_1SandboxManager_ae2afdf199a31e056780d21e8442d9ddf_cgraph.dot` (1 KB)
  - `classcore_1_1session__manager_1_1SessionManager__coll__graph.dot` (1 KB)
  - `classcore_1_1session__preprocessor_1_1SessionPreprocessor__coll__graph.dot` (2 KB)
  - `classcore_1_1session__preprocessor_1_1SessionPreprocessor_a239c7c4102d4a17aa3ee623771e704a9_icgraph.dot` (0 KB)
  - `classcore_1_1session__preprocessor_1_1SessionPreprocessor_a2f65f5c2c1c8efe4d8277ddc8bccc558_icgraph.dot` (0 KB)
  - `classcore_1_1session__preprocessor_1_1SessionPreprocessor_a63cf0df8e90c608845ec1823a23ef796_icgraph.dot` (0 KB)
  - `classcore_1_1session__preprocessor_1_1SessionPreprocessor_a8e9a5917743dda14acd6185af58b796f_cgraph.dot` (1 KB)
  - `classcore_1_1skills__manager_1_1Skill__coll__graph.dot` (1 KB)
  - `classcore_1_1skills__manager_1_1SkillsManager__coll__graph.dot` (2 KB)
  - `classcore_1_1skills__manager_1_1SkillsManager_a0d184599c4e6802b6d021de80b8983ab_cgraph.dot` (0 KB)
  - `classcore_1_1skills__manager_1_1SkillsManager_a4c33b6563d567f91413f3c33b4569b5a_cgraph.dot` (0 KB)
  - `classcore_1_1skills__manager_1_1SkillsManager_abd6d4fd1eafbfd1475a67a3c811c8f26_icgraph.dot` (1 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner__coll__graph.dot` (3 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_a0481e2c62df293053b7576cff131107a_icgraph.dot` (0 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_a22a12ae017a003031a1b7e35f8656d30_icgraph.dot` (2 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_a7bb2cd101f8135bdd39f5ac59f936d32_cgraph.dot` (0 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_a7bb2cd101f8135bdd39f5ac59f936d32_icgraph.dot` (1 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_a7ef82b7c749ef204c6518f5ff4b1fc27_cgraph.dot` (2 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_a7ef82b7c749ef204c6518f5ff4b1fc27_icgraph.dot` (0 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_abd254d33291077274c09bef339b4c6c2_cgraph.dot` (1 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_abd254d33291077274c09bef339b4c6c2_icgraph.dot` (0 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_ad1d19d5231b3bbd01a8a7ced79073df3_cgraph.dot` (0 KB)
  - `classcore_1_1tool__runner_1_1ToolRunner_ad1d19d5231b3bbd01a8a7ced79073df3_icgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase__coll__graph.dot` (2 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_a04e74cfd2fe79df2ab9ce0a04778db13_cgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_a34da64c744cf5b858e2460d7eebe8d17_cgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_a377cce8e2e2ccc1cf9c91725386e5ad9_cgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_a5534b937edeca1d92af937f9245af004_icgraph.dot` (1 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_aa5870bd6431bcb5ad3cfdf1b5103c680_cgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_ab6aae89ca7180fe6e711089995cab545_icgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_aba43e5b95b90d8d1da74e1fa15770a17_icgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_ad1ba71d7b32d11d4cf8ef9fc64bae0d6_icgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_aee8cb122b57cc84d3bffe15e87ad96d8_cgraph.dot` (0 KB)
  - `classdatabase_1_1agent__db_1_1AgentDatabase_af72cf0d11b9913276d2261151da29430_cgraph.dot` (0 KB)
  - `classmanagers_1_1break__system_1_1BreakSystem__coll__graph.dot` (2 KB)
  - `classmanagers_1_1break__system_1_1BreakSystem_a54c3253b4082d7632563b9f6b73c1612_icgraph.dot` (0 KB)
  - `classmanagers_1_1break__system_1_1BreakSystem_a9305861dd0d1c7043fd9d536bc8a2cae_cgraph.dot` (0 KB)
  - `classmanagers_1_1dynamic__spawner_1_1DynamicSpawner__coll__graph.dot` (1 KB)
  - `classmanagers_1_1dynamic__spawner_1_1DynamicSpawner_a711e5dcf634b5abbd73ff3c2d71505f8_cgraph.dot` (0 KB)
  - `classmanagers_1_1dynamic__spawner_1_1DynamicSpawner_ace1486716f92dba70dfcf94d4a56ca71_icgraph.dot` (0 KB)
  - `classmanagers_1_1emergency__mailbox_1_1EmergencyMailbox__coll__graph.dot` (2 KB)
  - `classmanagers_1_1emergency__mailbox_1_1EmergencyMailbox_a134e2a33e103c17ab2173674ab113145_icgraph.dot` (0 KB)
  - `classmanagers_1_1emergency__mailbox_1_1EmergencyMailbox_a76c0e1e766d743d598da43887eace654_cgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1BuildError__coll__graph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1BuildStatus__coll__graph.dot` (1 KB)
  - `classmanagers_1_1shared__build__status_1_1BuildStatus__inherit__graph.dot` (1 KB)
  - `classmanagers_1_1shared__build__status_1_1DiffPatch__coll__graph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager__coll__graph.dot` (4 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a0497404448f8f821f09718ba8f71e194_icgraph.dot` (1 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a07256b0a1294090e17b3c447c7190b16_cgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a4616f493f92c2921eed73335504ad7b7_cgraph.dot` (2 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a55cff883bff3cce6259d8f56c0efbc95_cgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a64ddd06916b6c28a14142ac7a93e76bc_icgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a6610da3e6d58f3ac1fc5aa6cdd7d7ff1_cgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a6ec648f1f2e9b1d4b1ecebe88a30767b_cgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a6ec648f1f2e9b1d4b1ecebe88a30767b_icgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a757bbb7d30a5f3f49ff5c841d39e44b8_icgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_a7f6c6ee3e48111e5f78e9c56158fc779_cgraph.dot` (0 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_aa4c88d726a2fd0dd4f773f67f645ad8c_icgraph.dot` (1 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_aa69c8bc08d2e3811cc2fa370bece8359_icgraph.dot` (2 KB)
  - `classmanagers_1_1shared__build__status_1_1SharedBuildStatusManager_af01a4c34826896477c52cbbf4d2b8900_cgraph.dot` (1 KB)
  - `classmanagers_1_1sleep__manager_1_1SleepManager__coll__graph.dot` (1 KB)
  - `classtest__analysis__tools_1_1TestAXECommandIntegration__coll__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestAXECommandIntegration__inherit__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestBuildAnalyzerIntegration__coll__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestBuildAnalyzerIntegration__inherit__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestExecBlockSupport__coll__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestExecBlockSupport__inherit__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestLlmprepIntegration__coll__graph.dot` (2 KB)
  - `classtest__analysis__tools_1_1TestLlmprepIntegration__inherit__graph.dot` (2 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles__coll__graph.dot` (3 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a2878710990c0504ff36a7058f8a9f336_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a2878710990c0504ff36a7058f8a9f336_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a34c6175609d9c890fe54016d509f13e5_cgraph.dot` (1 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a34c6175609d9c890fe54016d509f13e5_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a3ab8a626ba5ac8d394a06a8321571073_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a47c0ad1d5146e3d3f29931aff1b06839_cgraph.dot` (8 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a5d900df953af1bca17f1eb6cd7b736b6_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a5d900df953af1bca17f1eb6cd7b736b6_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a603b8830f3949f2b6ea22ea4353f478d_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a61522bf09e47f7acd234779f3a59f9c0_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a61522bf09e47f7acd234779f3a59f9c0_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a669f34932e33a12743eb049c78056df2_cgraph.dot` (1 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a669f34932e33a12743eb049c78056df2_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a6ba6ee3c9c9bd1af73a375406510d767_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a816329051672d07644fa44a9ebdc1cdc_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a8c3d9221017c89e7a6ac28a1b066fad0_icgraph.dot` (1 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a9a277c2f4c93c3060dcb0eae9a5f474c_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_a9a277c2f4c93c3060dcb0eae9a5f474c_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_aa0464c1a1435b70f23f882f6a3cfa531_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_aa0464c1a1435b70f23f882f6a3cfa531_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_ab4226a598a941590d38d499eda3257be_icgraph.dot` (1 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_ae64a95b90dba266d7c611e4942cff10c_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_ae64a95b90dba266d7c611e4942cff10c_icgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_aeab69ee357a6da22bd122d4c8623ae5d_cgraph.dot` (0 KB)
  - `classtest__large__code__files_1_1TestLargeCodeFiles_aeab69ee357a6da22bd122d4c8623ae5d_icgraph.dot` (0 KB)
  - `classtest__minifier_1_1TestAsmMinification__coll__graph.dot` (1 KB)
  - `classtest__minifier_1_1TestAsmMinification__inherit__graph.dot` (1 KB)
  - `classtest__minifier_1_1TestCCppMinification__coll__graph.dot` (1 KB)
  - `classtest__minifier_1_1TestCCppMinification__inherit__graph.dot` (1 KB)
  - `classtest__minifier_1_1TestConvenienceFunctions__coll__graph.dot` (1 KB)
  - `classtest__minifier_1_1TestConvenienceFunctions__inherit__graph.dot` (1 KB)
  - `classtest__minifier_1_1TestEdgeCases__coll__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestEdgeCases__inherit__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestFileCollection__coll__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestFileCollection__inherit__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestLanguageDetection__coll__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestLanguageDetection__inherit__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestMinifierClass__coll__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestMinifierClass__inherit__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestPythonMinification__coll__graph.dot` (2 KB)
  - `classtest__minifier_1_1TestPythonMinification__inherit__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestEnvironmentProbePreprocessing__coll__graph.dot` (1 KB)
  - `classtest__session__preprocessor_1_1TestEnvironmentProbePreprocessing__inherit__graph.dot` (1 KB)
  - `classtest__session__preprocessor_1_1TestFactoryFunction__coll__graph.dot` (1 KB)
  - `classtest__session__preprocessor_1_1TestFactoryFunction__inherit__graph.dot` (1 KB)
  - `classtest__session__preprocessor_1_1TestFullWorkflow__coll__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestFullWorkflow__inherit__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestLlmprepPreprocessing__coll__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestLlmprepPreprocessing__inherit__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestMinifierPreprocessing__coll__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestMinifierPreprocessing__inherit__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestSessionPreprocessorInit__coll__graph.dot` (2 KB)
  - `classtest__session__preprocessor_1_1TestSessionPreprocessorInit__inherit__graph.dot` (2 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus__coll__graph.dot` (2 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a19c9c3f1ea1483d365e41cf25d82f752_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a1f920f1cb9204538eb8efce6f2529782_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a2b0ff34e4124bff50de2c31f4440036f_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a65483fd9b4288243e561b7fec43a5e6b_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a6fec447e1f436649fb7605d94eee1bb9_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a724e7f1f81669ffae5ab9ea9a0a15041_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_a8a9d0ab4bf6c6d962334aef304d2415b_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_aa2350a9328c47c13c0c8193a33de38e7_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_aa8514c9c2357090dcc630e897c29b7fe_cgraph.dot` (7 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_aae4064bb3f9606afdfa474d97de1db68_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_abf2455493cf8316b397d5f540389d732_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_ac0ba10c1093e4b815cd3aaea0c000173_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_ac3366fefbcaf0d590d51317c9db54596_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_ac5901fc4cd18edf85a56f7244ff4114f_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_ad6aff1bb9372d110dc585cfdc1544a18_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_ad978f9fecb7ddce345485006d13fc46f_icgraph.dot` (0 KB)
  - `classtest__shared__build__status_1_1TestSharedBuildStatus_add012f64260a686ab82a9187d990ef0e_icgraph.dot` (0 KB)
  - `classtest__workshop_1_1TestWorkshop__coll__graph.dot` (2 KB)
  - `classtest__workshop_1_1TestWorkshop__inherit__graph.dot` (2 KB)
  - `classtest__workshop__cli__integration_1_1TestWorkshopCLIIntegration__coll__graph.dot` (3 KB)
  - `classtest__workshop__cli__integration_1_1TestWorkshopCLIIntegration__inherit__graph.dot` (3 KB)
  - `classtest__workshop__integration_1_1TestWorkshopIntegration__coll__graph.dot` (2 KB)
  - `classtest__workshop__integration_1_1TestWorkshopIntegration__inherit__graph.dot` (2 KB)
  - `classtest__workshop__pr23__validation_1_1TestWorkshopPR23Validation__coll__graph.dot` (3 KB)
  - `classtest__workshop__pr23__validation_1_1TestWorkshopPR23Validation__inherit__graph.dot` (3 KB)
  - `classtools_1_1minifier_1_1Minifier__coll__graph.dot` (1 KB)
  - `classtools_1_1minifier_1_1Minifier_a316d3dbf2526c91794276c888391c8a7_cgraph.dot` (3 KB)
  - `classtools_1_1minifier_1_1Minifier_aef10b8bbbe845f198d5f739278cf596d_cgraph.dot` (2 KB)
  - `classtools_1_1minifier_1_1Minifier_aef10b8bbbe845f198d5f739278cf596d_icgraph.dot` (0 KB)
  - `classtools_1_1minifier_1_1Minifier_af4e76beb46588676e9f30dedfc7bba67_cgraph.dot` (2 KB)
  - `classtools_1_1minifier_1_1Minifier_af4e76beb46588676e9f30dedfc7bba67_icgraph.dot` (1 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer__coll__graph.dot` (2 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a201ebbd84b52fdab128451f3d4bcaa52_cgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a3383ac2d67bd3f1195407188178b94ac_icgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a3575d60d796e301c85a19bf49657bd04_icgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a3bee9ecda151e64652078984987409eb_icgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a3f4a938f1eea8500fc24ef790908569c_cgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a3f4a938f1eea8500fc24ef790908569c_icgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a479da7823a17036223762dda9a8b93aa_cgraph.dot` (1 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a5a8bcae7cfde8579b1228f781d8098fb_icgraph.dot` (1 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_a8f03bd5d6f4a60a5d04cab20047e623b_cgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_acb7b06b82aa405ceb52ef15cfdcaeac5_icgraph.dot` (0 KB)
  - `classutils_1_1context__optimizer_1_1ContextOptimizer_affd6588756f9f8e69a0da458e57b43ff_cgraph.dot` (1 KB)
  - `classutils_1_1context__optimizer_1_1Message__coll__graph.dot` (0 KB)
  - `classutils_1_1formatting_1_1Colors__coll__graph.dot` (1 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor__coll__graph.dot` (2 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a33e854a082c8a8ef6c18cd8bd78469c0_cgraph.dot` (0 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a33e854a082c8a8ef6c18cd8bd78469c0_icgraph.dot` (0 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a3c619d552358929453ff38705d6b7b37_cgraph.dot` (2 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a3dcdabd9e980fc632396b2047db32f23_cgraph.dot` (0 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a3dcdabd9e980fc632396b2047db32f23_icgraph.dot` (0 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a412cd77b24d44c2b4c3fae9eb3f0824c_icgraph.dot` (1 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_a7febd48ac42a8fbedf779015b5b5d4ce_icgraph.dot` (0 KB)
  - `classutils_1_1prompt__compressor_1_1PromptCompressor_abdad9849e060f6d137222f99e6fcb4f3_icgraph.dot` (1 KB)
  - `classutils_1_1rate__limiter_1_1RateLimiter__coll__graph.dot` (1 KB)
  - `classutils_1_1rate__limiter_1_1RateLimiter_aa8feb9cb1f0ad7257995d840c59d5c85_cgraph.dot` (0 KB)
  - `classutils_1_1rate__limiter_1_1RateLimiter_ad4f56b6cf0d52c1de326eafeb0b75590_icgraph.dot` (0 KB)
  - `classutils_1_1token__stats_1_1TokenStats__coll__graph.dot` (1 KB)
  - `classutils_1_1token__stats_1_1TokenStats_a6276a11210640470b7397871f93084bf_cgraph.dot` (1 KB)
  - `classutils_1_1token__stats_1_1TokenStats_a9ce688e0ff3d85f0a5cc2371301d90e0_cgraph.dot` (1 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer__coll__graph.dot` (2 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a08898a342ce3b5f527cc5ec8e235ffdb_cgraph.dot` (2 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a08898a342ce3b5f527cc5ec8e235ffdb_icgraph.dot` (0 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a27aee86cdc5318fc86c52a95b4148b50_cgraph.dot` (2 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a2bb4b175d37b7c5f3abe66368371ac8f_icgraph.dot` (1 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a4f5c6efc6a0dd95fb7b71fb1fd7d6a4c_icgraph.dot` (1 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a5d8e0664b65831068788dde5dba89e0f_icgraph.dot` (1 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_a6c1d01c7d9e55006508411fd8b092dc1_icgraph.dot` (1 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_abb8d63f59e4a6e219caaddfa8cf5ad33_icgraph.dot` (1 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_af0743f86826a48c14eea6d2ffdf961c9_cgraph.dot` (0 KB)
  - `classworkshop_1_1chisel_1_1ChiselAnalyzer_af0743f86826a48c14eea6d2ffdf961c9_icgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor__coll__graph.dot` (3 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a152c957853243eb31b32fb9156dfe118_cgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a152c957853243eb31b32fb9156dfe118_icgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a1d2d3680010ad50738f75699694eddae_icgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a337d0e7e376218896d4f6c916bb5a28b_cgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a337d0e7e376218896d4f6c916bb5a28b_icgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a362f26d8c133ee5fbefc358915b2e633_cgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a362f26d8c133ee5fbefc358915b2e633_icgraph.dot` (0 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a883da6cc68ccb313c4c9d619778ca9ed_cgraph.dot` (0 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a9159cd3e79ed6dcd93ae27ee9cde2589_cgraph.dot` (2 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_a9159cd3e79ed6dcd93ae27ee9cde2589_icgraph.dot` (0 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_aa795218d5d2fc4fda11367deab2f0b6f_icgraph.dot` (0 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_acb37c7042f0b40915e6b0e19610b994c_cgraph.dot` (3 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_acbb48087ecc8ff4ed7dfc5895661c6de_cgraph.dot` (1 KB)
  - `classworkshop_1_1hammer_1_1HammerInstrumentor_ad6c32528352dedebb0141e06981664b7_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1EnumeratedSink__coll__graph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1EnumeratedSource__coll__graph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1PlaneEnumerator__coll__graph.dot` (2 KB)
  - `classworkshop_1_1plane_1_1PlaneEnumerator_a5b59f8b59266e8e020af58011ba17320_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1PlaneEnumerator_aa342e2ae26e98c4864723c19a37fa56e_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1PlaneEnumerator_ab5db32ffa4e1b525e1199f0d9e3489ba_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1PlaneEnumerator_ac3fcd149453031fc5c03323e9fedfde8_cgraph.dot` (1 KB)
  - `classworkshop_1_1plane_1_1PlaneEnumerator_af741eec88de2e681fe359100445c8d92_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor__coll__graph.dot` (2 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor__inherit__graph.dot` (2 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor_a269bdc8ac096e820b482aa7534dec102_cgraph.dot` (1 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor_aa551e6624dfcc01865d63ce5db8f319a_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor_ac1dc92f8690ddc76a55f1a71115b48bc_cgraph.dot` (1 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor_adbc3eb382434b3d70c9c77ada24e9a57_icgraph.dot` (0 KB)
  - `classworkshop_1_1plane_1_1SourceSinkVisitor_adcf903fec9b1fd3c10c05227bfb854c4_icgraph.dot` (1 KB)
  - `classworkshop_1_1saw_1_1SawTracker__coll__graph.dot` (3 KB)
  - `classworkshop_1_1saw_1_1SawTracker_a7b854041a44b07a96d3002a1913df1fb_icgraph.dot` (1 KB)
  - `classworkshop_1_1saw_1_1SawTracker_a7ff782d2c81dd58f0af9bbca73d2caf9_cgraph.dot` (1 KB)
  - `classworkshop_1_1saw_1_1SawTracker_a879cdc1cb42bceaff7f1ce6f2578c2bb_cgraph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1SawTracker_a879cdc1cb42bceaff7f1ce6f2578c2bb_icgraph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer__coll__graph.dot` (3 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer__inherit__graph.dot` (3 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer_a018909a0b2cb4d0175cbb8f7566c45bb_cgraph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer_a018909a0b2cb4d0175cbb8f7566c45bb_icgraph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer_a3cd13e2d2cd36cfd16c8781eb8fe44f3_icgraph.dot` (1 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer_a5c28b8c11ae8d515895a15bf742320d4_cgraph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer_a82e632e124fa2892f991ffa8cccd9805_cgraph.dot` (1 KB)
  - `classworkshop_1_1saw_1_1TaintAnalyzer_a9342169b911115a76ab6b5f9c422401f_icgraph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintFlow__coll__graph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintSink__coll__graph.dot` (0 KB)
  - `classworkshop_1_1saw_1_1TaintSource__coll__graph.dot` (0 KB)
  - `depklite_8c__incl.dot` (2 KB)
  - `depklite_8c_a0ba3adf2d91169675b5f216a301d9da4_cgraph.dot` (0 KB)
  - `depklite_8c_a1a918d28cd72b0a8e04d0b697f8e0742_cgraph.dot` (1 KB)
  - `depklite_8c_a1a918d28cd72b0a8e04d0b697f8e0742_icgraph.dot` (0 KB)
  - `depklite_8c_a3c08aac8e60f001e2c48fc3daf43bfb5_icgraph.dot` (1 KB)
  - `depklite_8c_a6c8292606a6eb2aa9759b31df768e40d_cgraph.dot` (0 KB)
  - `depklite_8c_a6c8292606a6eb2aa9759b31df768e40d_icgraph.dot` (0 KB)
  - `depklite_8c_a746cee407a9dac3b866f8da6600581c5_icgraph.dot` (0 KB)
  - `depklite_8c_a84e1ca261f7810f3e6573b6775637387_icgraph.dot` (1 KB)
  - `depklite_8c_ab46784744f0c75c40a5591adc24f2dea_icgraph.dot` (0 KB)
  - `depklite_8c_abc34a005998258ced922ca2e5df70ad0_cgraph.dot` (2 KB)
  - `depklite_8c_aefe53ad5b9e8e179f9df773d0f15063e_cgraph.dot` (0 KB)
  - `depklite_8c_aefe53ad5b9e8e179f9df773d0f15063e_icgraph.dot` (1 KB)
  - `depklite_8h__dep__incl.dot` (0 KB)
  - `depklite_8h__incl.dot` (1 KB)
  - `depklite_8h_a6c8292606a6eb2aa9759b31df768e40d_cgraph.dot` (0 KB)
  - `depklite_8h_a6c8292606a6eb2aa9759b31df768e40d_icgraph.dot` (0 KB)
  - `depklite_8h_abc34a005998258ced922ca2e5df70ad0_cgraph.dot` (2 KB)
  - `dir_185e1be576cc3aab87068787be53911a_dep.dot` (0 KB)
  - `dir_f8bf3b3db987cef055901402344d3f8d_dep.dot` (0 KB)
  - `graph_legend.dot` (1 KB)
  - `inherit_graph_0.dot` (0 KB)
  - `inherit_graph_1.dot` (0 KB)
  - `inherit_graph_10.dot` (0 KB)
  - `inherit_graph_11.dot` (0 KB)
  - `inherit_graph_12.dot` (0 KB)
  - `inherit_graph_13.dot` (0 KB)
  - `inherit_graph_14.dot` (0 KB)
  - `inherit_graph_15.dot` (0 KB)
  - `inherit_graph_16.dot` (0 KB)
  - `inherit_graph_17.dot` (0 KB)
  - `inherit_graph_18.dot` (0 KB)
  - `inherit_graph_19.dot` (0 KB)
  - `inherit_graph_2.dot` (0 KB)
  - `inherit_graph_20.dot` (0 KB)
  - `inherit_graph_21.dot` (0 KB)
  - `inherit_graph_22.dot` (0 KB)
  - `inherit_graph_23.dot` (0 KB)
  - `inherit_graph_24.dot` (0 KB)
  - `inherit_graph_25.dot` (0 KB)
  - `inherit_graph_26.dot` (0 KB)
  - `inherit_graph_27.dot` (0 KB)
  - `inherit_graph_28.dot` (0 KB)
  - `inherit_graph_29.dot` (0 KB)
  - `inherit_graph_3.dot` (0 KB)
  - `inherit_graph_30.dot` (0 KB)
  - `inherit_graph_31.dot` (0 KB)
  - `inherit_graph_32.dot` (0 KB)
  - `inherit_graph_33.dot` (0 KB)
  - `inherit_graph_34.dot` (0 KB)
  - `inherit_graph_35.dot` (0 KB)
  - `inherit_graph_36.dot` (0 KB)
  - `inherit_graph_37.dot` (0 KB)
  - `inherit_graph_38.dot` (0 KB)
  - `inherit_graph_39.dot` (0 KB)
  - `inherit_graph_4.dot` (0 KB)
  - `inherit_graph_40.dot` (0 KB)
  - `inherit_graph_41.dot` (7 KB)
  - `inherit_graph_42.dot` (0 KB)
  - `inherit_graph_43.dot` (0 KB)
  - `inherit_graph_44.dot` (0 KB)
  - `inherit_graph_45.dot` (0 KB)
  - `inherit_graph_46.dot` (0 KB)
  - `inherit_graph_47.dot` (0 KB)
  - `inherit_graph_48.dot` (0 KB)
  - `inherit_graph_49.dot` (0 KB)
  - `inherit_graph_5.dot` (0 KB)
  - `inherit_graph_50.dot` (0 KB)
  - `inherit_graph_51.dot` (0 KB)
  - `inherit_graph_52.dot` (0 KB)
  - `inherit_graph_53.dot` (0 KB)
  - `inherit_graph_54.dot` (0 KB)
  - `inherit_graph_55.dot` (0 KB)
  - `inherit_graph_56.dot` (0 KB)
  - `inherit_graph_6.dot` (0 KB)
  - `inherit_graph_7.dot` (0 KB)
  - `inherit_graph_8.dot` (0 KB)
  - `inherit_graph_9.dot` (0 KB)
  - `namespaceanthropic__features__demo_a92085a1d8fb488ebc175f97bfdf9f610_icgraph.dot` (0 KB)
  - `namespaceanthropic__features__demo_ab2e39b6a9072090bfe008755bdfaf535_icgraph.dot` (0 KB)
  - `namespaceanthropic__features__demo_ac05c4f79a07d8920ba4b8ec4b462a6d0_cgraph.dot` (1 KB)
  - `namespaceanthropic__features__demo_ac05c4f79a07d8920ba4b8ec4b462a6d0_icgraph.dot` (0 KB)
  - `namespaceaxe_a24106f38d1e2278a094b572012ed4760_cgraph.dot` (0 KB)
  - `namespaceaxe_a24106f38d1e2278a094b572012ed4760_icgraph.dot` (1 KB)
  - `namespaceaxe_a5387f652eb28eecb3bec22654aa3e40d_icgraph.dot` (2 KB)
  - `namespaceaxe_a557557e18d17b8fa824f16fd344efdcf_cgraph.dot` (0 KB)
  - `namespaceaxe_a557557e18d17b8fa824f16fd344efdcf_icgraph.dot` (1 KB)
  - `namespaceaxe_a6219e4e9c2c63cebb97122848b591a70_cgraph.dot` (1 KB)
  - `namespaceaxe_a6219e4e9c2c63cebb97122848b591a70_icgraph.dot` (1 KB)
  - `namespaceaxe_abb23f0d8329e501eb234daeb5a11ac9a_icgraph.dot` (0 KB)
  - `namespaceaxe_ac2811818e423281b1abace5155de35d2_cgraph.dot` (1 KB)
  - `namespaceaxe_ac2811818e423281b1abace5155de35d2_icgraph.dot` (0 KB)
  - `namespaceaxe_ae18887cd1aba7d83578d18397fe0cd63_icgraph.dot` (0 KB)
  - `namespaceaxe_aed941049819dac642905b812e754e2fa_icgraph.dot` (1 KB)
  - `namespacebenchmark__acp_a0d2edd8caa4f70efabefa35938f79e35_icgraph.dot` (1 KB)
  - `namespacebenchmark__acp_a5234978d085f61ca35dab78600d38129_icgraph.dot` (1 KB)
  - `namespacebenchmark__acp_a619f91db5b5151d760a75022ceeeaf36_icgraph.dot` (1 KB)
  - `namespacebenchmark__acp_aa43f698f5f9ae95cf20fa9d98224edbc_cgraph.dot` (0 KB)
  - `namespacebenchmark__acp_aa43f698f5f9ae95cf20fa9d98224edbc_icgraph.dot` (1 KB)
  - `namespacebenchmark__acp_ab2ae429afc267d7dbde7698eec1e5087_cgraph.dot` (2 KB)
  - `namespacebenchmark__acp_ab2ae429afc267d7dbde7698eec1e5087_icgraph.dot` (0 KB)
  - `namespacebenchmark__acp_addc5f8554094cc37a9d0932816b175d5_cgraph.dot` (2 KB)
  - `namespacebenchmark__acp_addc5f8554094cc37a9d0932816b175d5_icgraph.dot` (0 KB)
  - `namespacebenchmark__acp_aeda14e93f5d44e64563223f33d6aa911_cgraph.dot` (1 KB)
  - `namespacebenchmark__acp_aeda14e93f5d44e64563223f33d6aa911_icgraph.dot` (1 KB)
  - `namespacecore_1_1resource__monitor_ab88061275eb03ab63686d67b77c193f7_cgraph.dot` (0 KB)
  - `namespacecore_1_1resource__monitor_afeaa75ca4becf846a4f09445dd4b05f5_icgraph.dot` (0 KB)
  - `namespacedatabase_1_1agent__db_ab6c241f90eed44318868b0b99a957232_icgraph.dot` (0 KB)
  - `namespacedemo__absolute__path__fix_a30c645d2d192e7db670bd085a39b91c2_cgraph.dot` (1 KB)
  - `namespacedemo__absolute__path__fix_ac14101eb4f40f11faa42d7d01ccb09b3_icgraph.dot` (0 KB)
  - `namespacedemo__absolute__path__fix_aec105d2bd0206a76dea21836fcc49bd4_icgraph.dot` (0 KB)
  - `namespacedemo__dynamic__tokens_a3d5ef89047a3e00095104ee726bed6df_cgraph.dot` (0 KB)
  - `namespacedemo__dynamic__tokens_a3d5ef89047a3e00095104ee726bed6df_icgraph.dot` (0 KB)
  - `namespacedemo__heredoc__fix_ab608838bbf3efe5aeaa8c2efd5b80eb6_cgraph.dot` (0 KB)
  - `namespacedemo__heredoc__fix_ab608838bbf3efe5aeaa8c2efd5b80eb6_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_a1fcd2cb73d689c5a7ac4c69b2ea73616_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_a1fcd2cb73d689c5a7ac4c69b2ea73616_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_a3ecc9a2a26cfba0c9e84b2b09d9ea8b6_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_a3ecc9a2a26cfba0c9e84b2b09d9ea8b6_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_a521dcdcc5d0e6470eea2d4463d92d160_icgraph.dot` (5 KB)
  - `namespacedemo__improvements_a7fe0015c485ad4db14ad31aa89af8202_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_a7fe0015c485ad4db14ad31aa89af8202_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_a94340b2327743884fbc5c689f5b7d05f_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_a94340b2327743884fbc5c689f5b7d05f_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_aa9e1e8bdd79dbd29e746066f4d310aed_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_aa9e1e8bdd79dbd29e746066f4d310aed_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_ab70df92bee53be17e3ba83298bec4e1e_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_ab70df92bee53be17e3ba83298bec4e1e_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_ac136f13f3ad265259e73679a1dc70016_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_ac136f13f3ad265259e73679a1dc70016_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_ad282bb03383baaa52b8987f66221dfa3_cgraph.dot` (4 KB)
  - `namespacedemo__improvements_ad282bb03383baaa52b8987f66221dfa3_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_aec4fa1455387ae6faa95b3bd951ea183_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_aec4fa1455387ae6faa95b3bd951ea183_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_af9a2275e75ae3e21151c21fa514ded89_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_af9a2275e75ae3e21151c21fa514ded89_icgraph.dot` (0 KB)
  - `namespacedemo__improvements_afd38bcde85c7eb7536eb53814f63ea9a_cgraph.dot` (0 KB)
  - `namespacedemo__improvements_afd38bcde85c7eb7536eb53814f63ea9a_icgraph.dot` (0 KB)
  - `namespacedemo__minifier_a7ee1603133e69bf421a3fe23455d6c89_icgraph.dot` (0 KB)
  - `namespacedemo__minifier_a92ad425e02ff235b3ba82c3494006d45_icgraph.dot` (0 KB)
  - `namespacedemo__minifier_a9a876c9be28d0db5047c327492d93c64_cgraph.dot` (1 KB)
  - `namespacedemo__minifier_a9a876c9be28d0db5047c327492d93c64_icgraph.dot` (0 KB)
  - `namespacedemo__minifier_a9ada130677be44ad1ae9895f760cd48f_icgraph.dot` (0 KB)
  - `namespacedemo__minifier_aa0a2c0a7e89ad6d45baa05620b1dcae3_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_a10e0dd4e3d92432537b67fc7e18bc5b5_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_a2efbacedbdff6b41135a09ebc648e1a6_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_a6247f1ba0cda69e80d0ca06edfcf0bec_cgraph.dot` (2 KB)
  - `namespacedemo__skills__system_a6247f1ba0cda69e80d0ca06edfcf0bec_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_a7119ee2b559ba2584ab8a6cb4922c2de_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_ac210ddb775d78e0a593c7b807b86daec_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_ac30c9359dc876acbe3265479356b036e_icgraph.dot` (0 KB)
  - `namespacedemo__skills__system_ad54dcb724d73881461267caf96325936_icgraph.dot` (0 KB)
  - `namespacedemo__task__completion__fix_a0f1e8e40e77951dbf6d276e7f0252368_cgraph.dot` (0 KB)
  - `namespacedemo__task__completion__fix_a0f1e8e40e77951dbf6d276e7f0252368_icgraph.dot` (0 KB)
  - `namespacemanual__test__write_a25cfc9a67a28019272545f3c673cd232_icgraph.dot` (0 KB)
  - `namespacemanual__test__write_a5ce2643d29ab0fbe178d828257665f03_cgraph.dot` (0 KB)
  - `namespacemanual__test__write_a5ce2643d29ab0fbe178d828257665f03_icgraph.dot` (0 KB)
  - `namespacemanual__test__xml_a57b3fdb3b0fda93d5bc04cd65988246d_icgraph.dot` (0 KB)
  - `namespacemanual__test__xml_a7422ccf070167384f145d0a9af885fcc_icgraph.dot` (0 KB)
  - `namespacemanual__test__xml_a7ff7d4caf57ba1fe8a6eec8049ba2cdd_cgraph.dot` (1 KB)
  - `namespacemanual__test__xml_a7ff7d4caf57ba1fe8a6eec8049ba2cdd_icgraph.dot` (0 KB)
  - `namespacemanual__test__xml_aa48c53e57d6f7f7a0129733b301c01a5_icgraph.dot` (0 KB)
  - `namespacemanual__test__xml_ae0ea90384d299bb571cf7589aa1d77e1_icgraph.dot` (0 KB)
  - `namespacemodels_1_1metadata_a28d1646da3a97c054cd49e96f17c69df_cgraph.dot` (0 KB)
  - `namespacemodels_1_1metadata_a74979497137366bcbefb76bfc2bcb555_cgraph.dot` (0 KB)
  - `namespacemodels_1_1metadata_ad02c6726cf2ee370a30c9dd7f6e11386_cgraph.dot` (0 KB)
  - `namespacemodels_1_1metadata_af1deaacdde9b07ed1e1839b504b05c03_icgraph.dot` (1 KB)
  - `namespacepdfocr_a0350b44b7fe5a464ec4d7eb5d96c4329_icgraph.dot` (1 KB)
  - `namespacepdfocr_a099154a3f8d734ab6f18654cd5e5f6e5_cgraph.dot` (2 KB)
  - `namespacepdfocr_a099154a3f8d734ab6f18654cd5e5f6e5_icgraph.dot` (0 KB)
  - `namespacepdfocr_a396c2e32c75389b6d5604dec60a3dd00_icgraph.dot` (0 KB)
  - `namespacepdfocr_a42dc9f3b338729bee1d8c6ab01d8666f_icgraph.dot` (2 KB)
  - `namespacepdfocr_a5693f39c769fd1fcd9ec603497d3acfd_icgraph.dot` (2 KB)
  - `namespacepdfocr_a69dd0035c18ba7bd000e635b3041e1cf_icgraph.dot` (0 KB)
  - `namespacepdfocr_a7b52493a1b64d3386a4925cbaa3e82cf_icgraph.dot` (2 KB)
  - `namespacepdfocr_a81b1c455180a0a207040985e551a88db_cgraph.dot` (2 KB)
  - `namespacepdfocr_a81b1c455180a0a207040985e551a88db_icgraph.dot` (1 KB)
  - `namespacepdfocr_ab2a132de0991ecfc1920d46139077101_icgraph.dot` (0 KB)
  - `namespacepdfocr_abfb3d61192e485a1e34e0fe83935043d_icgraph.dot` (0 KB)
  - `namespacepdfocr_ac179521a93537a816beca0f185027d82_cgraph.dot` (0 KB)
  - `namespacepdfocr_ac179521a93537a816beca0f185027d82_icgraph.dot` (1 KB)
  - `namespacepdfocr_ac731da60c6eeccf59b74b31bdb947e53_cgraph.dot` (0 KB)
  - `namespacepdfocr_ac731da60c6eeccf59b74b31bdb947e53_icgraph.dot` (1 KB)
  - `namespacepdfocr_ac7f53dae8b4a44d22b069d65f97240c4_cgraph.dot` (3 KB)
  - `namespacepdfocr_ac7f53dae8b4a44d22b069d65f97240c4_icgraph.dot` (0 KB)
  - `namespacepdfocr_ad27e899ac4d3719ac2771d6737ebab30_cgraph.dot` (0 KB)
  - `namespacepdfocr_ad27e899ac4d3719ac2771d6737ebab30_icgraph.dot` (1 KB)
  - `namespacepdfocr_ad8298da323ae5f1a1630b7c8e278e1fb_icgraph.dot` (1 KB)
  - `namespacepdfocr_ae40f3e496d2e1a1d103e6dfa71895128_cgraph.dot` (5 KB)
  - `namespacepdfocr_ae40f3e496d2e1a1d103e6dfa71895128_icgraph.dot` (0 KB)
  - `namespacepdfocr_aeeef62cce7a050c3d64bc38595fce6ba_icgraph.dot` (2 KB)
  - `namespacetest__acp__benchmark_a142ccd77f3f9cf2609111961c1791722_icgraph.dot` (0 KB)
  - `namespacetest__acp__benchmark_a4fba479f6d3e0a59261e9b47e69d3bc3_icgraph.dot` (0 KB)
  - `namespacetest__acp__benchmark_aa049271dedf5e1cbf6e5cac40893c1df_cgraph.dot` (1 KB)
  - `namespacetest__acp__benchmark_aa685f60bb724976ed6b993e445cf7e88_icgraph.dot` (0 KB)
  - `namespacetest__acp__benchmark_af071ad4c4942dd22ecb269e0939c51a3_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_a0baaa3dc0ae5a9bb03a8176b123b834b_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_a3122200e793efb8c1a1c51114825e2da_cgraph.dot` (3 KB)
  - `namespacetest__anthropic__features_a3122200e793efb8c1a1c51114825e2da_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_a546df6e27cf4d22efa772a4ab30d3bab_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_a5abdf71d9d3eec1c28efc40c8601693e_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_a70e047808585610a06898db97ec02596_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_a747b06575370b6bd939761f1a24973f0_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_aa4c2e155ec02302e90e13072a484b033_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_ab35c76ae253b7b76a34966292d66b44c_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_ae05d31a08e7cfd14c51afc92721d4c1b_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__features_afda33bba66bb0e1f0d66a5c9715667a8_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_a0f23b08a614e7a676b798fa487bdc2f0_cgraph.dot` (3 KB)
  - `namespacetest__anthropic__integration_a0f23b08a614e7a676b798fa487bdc2f0_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_a2c8b5e5073e055ab7894b5661d68a41c_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_a4264b9b5a52cd6cc33525879cc6e5def_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_a4f47dbe5fdc7a971217926475ae38867_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_a516ff6fd06ddcc43cadee4644f9fc09e_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_aa47b57fd1e94e74501a3c092d9ae8305_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_ab7a6d91e04bae89f3b4363ab084ba4b3_icgraph.dot` (0 KB)
  - `namespacetest__anthropic__integration_afda01d90142522037da3377ead1906b1_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_a656c5badeb442b2e292d56ea3043bf09_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_a9333070f1a3ab445dc377dc92ae18e3c_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_aa919388a226535a1e0a575fee235c640_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_aaf966a415e2a30d28f39ea31b3e5c4e8_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_abe7c3ba3136933bb78db52fd41c8b4ad_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_ac6c1221ad325e710578fc18a4f852243_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_ad535edcf7f7ce4286ba58e07decea6bd_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_adc680a3d596f09419e4c9ff9632299d9_cgraph.dot` (3 KB)
  - `namespacetest__axe__improvements_adc680a3d596f09419e4c9ff9632299d9_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_adcafdef14f40f33da557ce0824b4ac0f_icgraph.dot` (0 KB)
  - `namespacetest__axe__improvements_ae1d3592668c6843922cddef2a397de1d_icgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_a2bb87e5531f531b7fb734927ee837adf_cgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_a2bb87e5531f531b7fb734927ee837adf_icgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_a35afb66b14174bae3c39efd8dd247f45_cgraph.dot` (2 KB)
  - `namespacetest__collab__tool__syntax_a35afb66b14174bae3c39efd8dd247f45_icgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_aa8ac70ed15a8a0db044cadadf5a82152_cgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_aa8ac70ed15a8a0db044cadadf5a82152_icgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_ab07b7e5d9dbefaa8a57d6cca450a87cb_icgraph.dot` (2 KB)
  - `namespacetest__collab__tool__syntax_ac2fbb67241504f81841e6625d3755251_cgraph.dot` (0 KB)
  - `namespacetest__collab__tool__syntax_ac2fbb67241504f81841e6625d3755251_icgraph.dot` (0 KB)
  - `namespacetest__database__location_a0706372cb2566cf0890c33d0df2a7193_icgraph.dot` (0 KB)
  - `namespacetest__database__location_a3d827865d668ddfdca679f108708a9f3_cgraph.dot` (2 KB)
  - `namespacetest__database__location_a3d827865d668ddfdca679f108708a9f3_icgraph.dot` (0 KB)
  - `namespacetest__database__location_a71045ab4bbb455002ff95b92c038a5cc_icgraph.dot` (0 KB)
  - `namespacetest__database__location_a7c5ad561821aeaaed9f7b8809d26a0d4_icgraph.dot` (0 KB)
  - `namespacetest__database__location_ac71cc2f0c6d22e67d2b2ffbb38db2012_icgraph.dot` (0 KB)
  - `namespacetest__database__location_adca062884bb502ca767fd1ea05226b22_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a1485e22657313b22ed83bb3b96f12863_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a333b032e09e0c66244d77ccfd7b3d3de_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a34af531bef5a8af618c7604dbde38a05_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a70186e2719d904a492d7c879601f6ddf_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a758845b9e70768c0a8a214fd23d7ca9f_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a8875f3da35378c09f8603b4aa55844b5_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a8bfd86e51dc4fb4919b2009bbf058b06_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_a9d2a94c19563344a4f90e72d8bd22693_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_ab2af52c1065b57818c983210fe05ffd3_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_abe82951b692d03953cc8434102338ec5_cgraph.dot` (4 KB)
  - `namespacetest__detect__agent__token_ad6d2aae1b8724f1e48234dcc5e5241e6_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_aeee6bbb752ca41a51411832e33a61cac_icgraph.dot` (0 KB)
  - `namespacetest__detect__agent__token_af2241d0234d13c05de8f1da6fbfdfff3_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_a0f0075e8c68b419c6e53c2fcae7162d0_cgraph.dot` (2 KB)
  - `namespacetest__double__execution_a0f0075e8c68b419c6e53c2fcae7162d0_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_a1c9f11f03b42a63b11ef071067464011_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_a83a7e7d6862f3a58911d5fb991fe7364_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_ad1bc40aba1f233228bfecd8b163c5fa6_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_af14292f1e8d06e7a28c36b35f034e535_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_af386013c5a4266e320b3deb66e26c598_icgraph.dot` (0 KB)
  - `namespacetest__double__execution_afad032aefd65108bdad810a2351da390_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_a11c90bf8d8af60818e439b8a9bb0d1dd_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_a2001cdfc69537dfb63d4c7a5ce4ed958_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_a30c6c9e8bd8d080109d64e7d9c71f9aa_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_a8d168daa3cd51cf709c35e40b5b3970c_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_a9ce19d959f3085f51b3796a44fbd2b9e_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_ab9f7eb0439d1a3b876c365830d7225ae_cgraph.dot` (2 KB)
  - `namespacetest__dynamic__max__tokens_ab9f7eb0439d1a3b876c365830d7225ae_icgraph.dot` (0 KB)
  - `namespacetest__dynamic__max__tokens_acceb70ea8d69c492841d7068ef05e184_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_a238b3c8c07dc1d001ddaf9a57d05d719_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_a7933bfeaad467bd549a2b93625c1571c_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_a82828f315442e9d80275261f052a7cc9_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_a8eeb792c37aa1f4c73b5e6151ac6d538_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_ab619fc553293802b7d261330b561e10b_cgraph.dot` (2 KB)
  - `namespacetest__efficiency__analysis_ab619fc553293802b7d261330b561e10b_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_ac8d56aba10c1ef9afeba7929b99d56dd_icgraph.dot` (0 KB)
  - `namespacetest__efficiency__analysis_ae66ff1876f3298ef19606bb494653fa8_icgraph.dot` (0 KB)
  - `namespacetest__exec__heredoc_a73ff5b19a641f10e1d01e489ce043300_cgraph.dot` (0 KB)
  - `namespacetest__exec__heredoc_a73ff5b19a641f10e1d01e489ce043300_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_a0443e870ae066b9fc4e0f7e3df169b4f_cgraph.dot` (2 KB)
  - `namespacetest__github__agent_a0443e870ae066b9fc4e0f7e3df169b4f_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_a1036e6afacddcae7eda73a1d8652ad56_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_a1f69e934a4e7472868f80314deabf4ed_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_ab0c8ce207274690710ac397a438a244e_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_ab138dcb8f05e71cd26e362b7a047286d_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_ab6052d7edd2fdc362e37506471884622_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_ace04319f4afc4d93d3574175de18563a_icgraph.dot` (0 KB)
  - `namespacetest__github__agent_aeb32aaa53f55876aaedef2ee469f0e16_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a19b53cd9d17d1fa9b47e500331eb94d1_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a364fea9f74600d28ce5a32e543b22c62_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a40b929cefae71f98ecac314dd893ee8c_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a63f186264c534b96eeca9548edab7590_cgraph.dot` (7 KB)
  - `namespacetest__heredoc__parsing_a63f186264c534b96eeca9548edab7590_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a6923699a5ca5787de4a3efa4b4dd05c7_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a72d2d139c7557dbeb5b9eacb02cca06f_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a846f28e9f201754909937862a919a5d2_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_a93b465a47ce3c42cadd3646feceb647b_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_aa60a912a8cd82428df2853db75721cf2_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_aac5307dd05d04fb9417a8f208a522726_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_aacd0ae4097198e815eafc92e02537aa5_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_ab9cfc4722ca63fa70ad0d17f0bb530e3_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_abdb30342f586f113dde7f78faa90df90_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_ac343e8c84deee6b5a82ff3ebc4272e8a_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_ac831fbd6e9285f1dfc56f818e77d6adc_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_ae979787278e8458894fc47d41ee91959_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_aef5efefd222904ca078685c608c5e834_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_af1230141c62f6100ba98c4577a081acf_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_afd303f6bca87dab9ed8b0ba0131276f8_icgraph.dot` (0 KB)
  - `namespacetest__heredoc__parsing_afd4ddae09aa029e474ba9c896ad7de12_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a0aac5fd9548c629b8eb94f1192a7c62b_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a13d13bd318e88c815d3f918b14c58b6a_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a26b9a09bdac6423cc73b55a65d174bf8_cgraph.dot` (2 KB)
  - `namespacetest__inline__exec__blocks_a26b9a09bdac6423cc73b55a65d174bf8_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a35db5c41685ac4211102518b51067a84_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a46fc4d1806b1eb9a81ececc9a8611213_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a5acf345064235bb8847bd79a1eba5019_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_a728e6ca79e4539c841a3c64e9d23158d_icgraph.dot` (0 KB)
  - `namespacetest__inline__exec__blocks_af27f7d86e71d90b8910a55ef3e4c7794_icgraph.dot` (0 KB)
  - `namespacetest__integration__bug__fix_a2c78b0ab8efa3082b90abcbce2086e43_icgraph.dot` (0 KB)
  - `namespacetest__integration__bug__fix_a2d5289dda77de4cd496d4fe2cdabc472_cgraph.dot` (1 KB)
  - `namespacetest__integration__bug__fix_a8a4a1dd818800a6b2370137edd6ebfde_icgraph.dot` (0 KB)
  - `namespacetest__integration__bug__fix_aa88b74dcc94b776c04dcda9310017469_icgraph.dot` (0 KB)
  - `namespacetest__integration__database__fix_a007ae765bb0c72a53ca7e7ab8a40a4ee_icgraph.dot` (0 KB)
  - `namespacetest__integration__database__fix_a8f88ac4584a4ca11b728db9d4d654e0f_cgraph.dot` (0 KB)
  - `namespacetest__integration__database__fix_a8f88ac4584a4ca11b728db9d4d654e0f_icgraph.dot` (0 KB)
  - `namespacetest__large__code__files_a823870e65175d3bc30c05ee9d07ebaa8_icgraph.dot` (4 KB)
  - `namespacetest__large__code__files_ab15bd6c4301fd3ff95dd4e04c99a3aa3_icgraph.dot` (2 KB)
  - `namespacetest__large__code__files_af10e0b7958fb7a993caf48b2b71b7c45_icgraph.dot` (1 KB)
  - `namespacetest__minifier_ab5ef82acc5a855c72a334f5de46522e4_cgraph.dot` (0 KB)
  - `namespacetest__minifier_ab5ef82acc5a855c72a334f5de46522e4_icgraph.dot` (0 KB)
  - `namespacetest__mission__md__tokens_a1a168d9573b7800b3073aad4e9e54548_cgraph.dot` (1 KB)
  - `namespacetest__mission__md__tokens_a5be245824db8e958ffef1b364d9283d0_icgraph.dot` (0 KB)
  - `namespacetest__mission__md__tokens_abcc6a74944f38a92173727b712fc487e_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_a1ba37a9fac15549945c06fb43994bb6f_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_a276aa4bbcffb0925b514639210806efe_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_a3e823f38d948c377fde5c1b122d955e0_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_a54ec739c0ab2309fa9e35ced284e55db_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_a95c06a738f1ec6c24d7cd1eccd4e7f10_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_abb104cdfaa987741e37fd6eed43cc596_icgraph.dot` (0 KB)
  - `namespacetest__models__yaml_afe45ae826969327c02f4dd9fad6bde1d_cgraph.dot` (2 KB)
  - `namespacetest__models__yaml_afe45ae826969327c02f4dd9fad6bde1d_icgraph.dot` (0 KB)
  - `namespacetest__session__preprocessor_a85297dd3abb6618ec764fd4fb146caab_cgraph.dot` (0 KB)
  - `namespacetest__session__preprocessor_a85297dd3abb6618ec764fd4fb146caab_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a0b97a3be42797f5f5ab85a93bba7c0a4_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a0c204884c148d8b5eb4f628c4313d40f_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a18cf69530455ab1948852b9f814903b7_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a45cd5ed1af80b0256a2b0687138267d4_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a52cdd9f42d350f9aa189ecc24e6f2271_cgraph.dot` (3 KB)
  - `namespacetest__silent__builds_a52cdd9f42d350f9aa189ecc24e6f2271_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a69ab5f227ac98865545ee3ab98cf88a4_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_a9383a3202b91979a12fb65e0e10a669d_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_ab56f793f6906f4dbb319aee4211c61b6_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_abfefe9c728dcd7aaff79a8e2a0e21dac_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_aef7cf3f447ea468df34a43a96fa7ba3d_icgraph.dot` (0 KB)
  - `namespacetest__silent__builds_afa53f6802edd1e9894ee93ed24211520_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a145d7d40e16eb6963f81b53de2ed3816_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a290f350f19c2e476150be9b126a9c522_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a298ae66d106237b30935b01ca560381c_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a2d841d1abd82159568a2f1b6032d5646_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a32c432bd8a8cf3361349f8206e26f425_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a3918438a938bfb7610783fa8db659f67_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a40422333f3eb2a94f787cd56b1045158_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a46036dcbf4333cd9ce11e41854fee8a6_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a663bbfbcf40faf39f23058ce3d5d1727_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a66809d2e5ae59b629bd4a6561544cb35_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a68659b2daa6eff9774f9602f61ea9b7b_cgraph.dot` (6 KB)
  - `namespacetest__skills__manager_a68659b2daa6eff9774f9602f61ea9b7b_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a69ff6e7884bf20bd3a31f5811c89d0a0_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_a950a3f069f87b99131e6f9f2b41b751e_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_aa0f79a4d11afee7cf7f124072509e44c_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_aaee7d74995fe0750100245ba590e9e61_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_ace43b2d352f716d48e0a40758e0ef02d_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_ae0411d14a6a613cef252ecda764a0590_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_ae3511f78feb1683ccd2af910ae4a2cab_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_ae7e526e524e9ca72fc9705903ab93ca3_icgraph.dot` (0 KB)
  - `namespacetest__skills__manager_af646f63246579ef15faf833c9c564401_icgraph.dot` (0 KB)
  - `namespacetest__spawned__agents_a30b576e2227c48ed67a58316f914924e_cgraph.dot` (1 KB)
  - `namespacetest__spawned__agents_a30b576e2227c48ed67a58316f914924e_icgraph.dot` (0 KB)
  - `namespacetest__spawned__agents_a42baa5e9890bb99de3e31df8c15ce71e_icgraph.dot` (0 KB)
  - `namespacetest__spawned__agents_a6d52b1e0882e22cd7294a7cac6d27ad2_icgraph.dot` (0 KB)
  - `namespacetest__spawned__agents_aadcd222919d82e631e3a65554e47157d_icgraph.dot` (0 KB)
  - `namespacetest__supervisor__protections_a4b1c43d32f0d74500c7d65b42e41991e_cgraph.dot` (1 KB)
  - `namespacetest__supervisor__protections_a6be4bf53379d8a7a4aacfe2f4f3d7ca4_icgraph.dot` (0 KB)
  - `namespacetest__supervisor__protections_a832f5207ae74dd70b0f3f7c23ef2dc67_icgraph.dot` (0 KB)
  - `namespacetest__supervisor__protections_ae0a7e17def5c59cca787f18afa101bd4_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a0142468c1a5ad1c750c47f4140b8ff77_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a2ed677a464fa9724e13c93f53aa18995_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a30bfaead8fee85f8afe96436bc087670_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a320ce8329e56e5231bb676d3a8631147_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a585c45ca9bebd2014da6ce51333d4318_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a683421951a27cc37d5998776b4610324_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a7904e6a2684bb10b760f666c3bd1c379_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a79d15d85cffcdd769e6124608e0e4c25_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_a8d35a5ff7786b799ab327fb49cd49ef8_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_aa8f2b022cb47c4033f4bc90ed42e16ac_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_ad78af8bf27f604116064d4872e9f2681_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_adafad825e82f81c901f94736322ccfce_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_ae1aa5643896cdd04e5862fcd87df5e8d_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_af3dbc4f6e6a67a07acbe0ca1f5e10bed_cgraph.dot` (6 KB)
  - `namespacetest__task__completion__detection_af70efc1e7fcefb6ff8c7c601c402cc0e_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_af9e90bb6fa556b2d1e2c16db6527cabb_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_afa3a05cccd0f8be7a45ee1718378975b_icgraph.dot` (0 KB)
  - `namespacetest__task__completion__detection_afa82e2ff5961f204c7240346db03d561_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_a52d64b7049e5f80ba9ea15b63a0f22d6_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_a5abcef20a7866734557d4b9316b5ec47_cgraph.dot` (3 KB)
  - `namespacetest__token__error__handling_a5abcef20a7866734557d4b9316b5ec47_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_a7a1a12825cf845d4de80e18cf972a35d_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_a87c83c23d69fed7487f32dd6a9280877_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_aa29ac843592b157dadd5184f2810627c_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_aab6090d95d2686c8a07056ba484799a1_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_aebe5ae49936eccebdca7d0a8706296b6_icgraph.dot` (0 KB)
  - `namespacetest__token__error__handling_aff60ebebd09e9608822f5fb57d344ed4_icgraph.dot` (0 KB)
  - `namespacetest__workshop__pr23__validation_a48ce4ff047f11f1f011e9301f477078c_cgraph.dot` (0 KB)
  - `namespacetest__workshop__pr23__validation_a48ce4ff047f11f1f011e9301f477078c_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a11f17425c3946c4a2c50bcb56852f52e_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a3a8c1433d19bbd15c9d507d494b4c49f_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a4522e57578ea1ba596d6b7c49a274c65_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a58a84116cbfdda538a612e23621e4a84_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a62ca47969e7ca35ac9678021312a59c3_icgraph.dot` (1 KB)
  - `namespacetest__write__blocks_a669bacf194a0c36da43e44f1c3d3b8f3_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a77c816038348e6403b7d1cb87bf1b49e_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a84f018c25f8bb77ccf86173ae0cb14c9_cgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a84f018c25f8bb77ccf86173ae0cb14c9_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a868f02f0bc6cbcf85f5598312caeda49_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_a93b7d0da40c150aa9f5a7cdfa321aa15_cgraph.dot` (4 KB)
  - `namespacetest__write__blocks_a93b7d0da40c150aa9f5a7cdfa321aa15_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_abc2ed9d023ae22219a7bc9f314e36ca5_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_add4bb907173efd0dda523b2b5e91acf0_icgraph.dot` (0 KB)
  - `namespacetest__write__blocks_afc0956b20195927c54ffcacd8c921a10_icgraph.dot` (0 KB)
  - `namespacetest__xml__new__formats_a1eb85e7781a776715ce07b6a151e94e9_cgraph.dot` (2 KB)
  - `namespacetest__xml__new__formats_a1eb85e7781a776715ce07b6a151e94e9_icgraph.dot` (0 KB)
  - `namespacetest__xml__new__formats_a2119efffc15a8e209e2ba0e3b4f6ece8_icgraph.dot` (0 KB)
  - `namespacetest__xml__new__formats_a85bfc4b8035093404ca9c401ed627baa_icgraph.dot` (0 KB)
  - `namespacetest__xml__new__formats_aa36a28c04af39fa05921068c87c52ba4_icgraph.dot` (0 KB)
  - `namespacetest__xml__new__formats_aa5ff845df27054fbf897b8df1a708381_icgraph.dot` (0 KB)
  - `namespacetest__xml__new__formats_ab3afbf3a719b2ceed675659db545d33c_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a001331c5f9b42f113ee515cf7aea9945_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a0ab6477fc4d88777ca0eea40580d235c_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a0eef09b23f55b17ca084f3e6fe8e67b9_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a199344369b08b2bf382e1e6288412ab3_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a203fa2a03f282583f84df5be66ea0c82_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a22b0ef73f81ce7421850ff7532369c19_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a25bd7e58fec7c6299ebac96ea0de32d9_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a28a03a428d498800f54c7157895f30b5_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a33b307deaba29a7aa4cd1c711ec79911_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a35c64f3c432a1e4e4adbd26208b6ca45_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a394ae75deec3582c5e3bdc004233197a_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a3aa2426f55750af1133e5fc1b1c36e67_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a3fdad6dac67fbf70d41cfd14c2b89e22_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a58d2f9651f470dcfd808649b60907735_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a66df6a1928c34dda206663f687557384_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a737c8c0243dd4a3d0fa693705117155e_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a759d08bc58c1831513a866d0938f5d65_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a7c1b6b062381453eddbf83b6ca21e3c7_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a7e4f75add26363732dae85a9bdcc347d_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_a90094a566aafb0701daef36198cd556e_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_aa37d41a6c52207c087d5f7424d076687_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_aaa5cb7f5026e1e9f4ca16c2f1cb2a2ca_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_aad7db75bc5175031691c418fee94aec7_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ab079c4377f445b5c6eebf5baba329b67_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ab2600f4903d958c7af9f1a430b611f38_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ab6d570dfd1467928e4eb91e17d1d5196_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_abd14e011ca843d292f30c126f21c0df5_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_accb88c4b9a03295ed3215c44a19a7813_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ad51ec0d91297eb3bf754f91a7526e4ca_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ad662eb2404de825c6f0344ccc68ee342_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ad78892ef14d7e59c36e38500fe0a6e4d_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ad7a5ddc5b1abdfe665fed57fc0fd6212_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_adaadf1ae3cf0619aa35bfcfec6a252e6_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ae4730d8fee431d14a8b1c01383021c8e_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ae493d07b545ec49f5a67cbc708d6cf96_cgraph.dot` (12 KB)
  - `namespacetest__xml__tool__parser_ae493d07b545ec49f5a67cbc708d6cf96_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_ae8baa71b32d27c2c4a77aff9f7844f4f_icgraph.dot` (0 KB)
  - `namespacetest__xml__tool__parser_af0d38d6bf7a18c6244d2145584a00a2d_icgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a122c52142b547165846d82dbd99949d4_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a122c52142b547165846d82dbd99949d4_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a41726c547bb435a3ff3dccb41fc6e5d3_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a47b835433d2e313fbdcb3c1350ab8fe0_cgraph.dot` (8 KB)
  - `namespacetools_1_1build__analyzer_a47b835433d2e313fbdcb3c1350ab8fe0_icgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a4b58af030b42bb980ae11592434ca765_icgraph.dot` (4 KB)
  - `namespacetools_1_1build__analyzer_a50c5c40cb65f2089e49959a412ed302c_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a50c5c40cb65f2089e49959a412ed302c_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a5a0d0bf7af120fdae4d537c9c852a3d9_icgraph.dot` (2 KB)
  - `namespacetools_1_1build__analyzer_a5ac10ab2b3b30b6e0064795179d7a36c_cgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a5ac10ab2b3b30b6e0064795179d7a36c_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a6a042d3b9933670399f165daf9c8fcb6_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a6a042d3b9933670399f165daf9c8fcb6_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a6b68897d94300a6fe15be6a392fe21ab_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a6b68897d94300a6fe15be6a392fe21ab_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a8a2e248981c1bf55e061c43ea33eb62e_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a8a2e248981c1bf55e061c43ea33eb62e_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_a9314866ed29a3b6596c60692e623f17f_icgraph.dot` (2 KB)
  - `namespacetools_1_1build__analyzer_a9508c930f379c7a1a86cfcbce4656aa6_cgraph.dot` (4 KB)
  - `namespacetools_1_1build__analyzer_a9508c930f379c7a1a86cfcbce4656aa6_icgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a9b85168990042e03ca24eea6a79bc2cd_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_a9b85168990042e03ca24eea6a79bc2cd_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_aaca7acb4ee4ffc81aaadd176db622eeb_cgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_aaca7acb4ee4ffc81aaadd176db622eeb_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_ac68f2add72229581ea5e4ac64bd62f2c_icgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_ac7ebff7127f6b11ce05109aebcceb27d_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_ad3c492d6e19c78b5a075cf2d226bcbd0_icgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_ada540ddd4288231265da6cef5eea9e4a_cgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_ada540ddd4288231265da6cef5eea9e4a_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_adb11a626c64e923dfc5853158f9791fa_cgraph.dot` (3 KB)
  - `namespacetools_1_1build__analyzer_adb11a626c64e923dfc5853158f9791fa_icgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_adc3482effdbd91cff486d8d5c1f3d892_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_ae46450f0cf52ad119daa6c8d0abc38da_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_ae5e451ebccb1624c28ae83fd6d34ef6c_cgraph.dot` (0 KB)
  - `namespacetools_1_1build__analyzer_ae5e451ebccb1624c28ae83fd6d34ef6c_icgraph.dot` (1 KB)
  - `namespacetools_1_1build__analyzer_aeac24013322272bd945b7f85ff8f483d_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_a014831525cb97488090bd375260dbbc0_cgraph.dot` (1 KB)
  - `namespacetools_1_1llmprep_a014831525cb97488090bd375260dbbc0_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_a20b859872059debb1575e62e5e08c610_cgraph.dot` (1 KB)
  - `namespacetools_1_1llmprep_a20b859872059debb1575e62e5e08c610_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_a2c49d26631d8d1206df8393dad232cdf_cgraph.dot` (1 KB)
  - `namespacetools_1_1llmprep_a2c49d26631d8d1206df8393dad232cdf_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_a3f552e87da06945cef10f68ce045c2fc_icgraph.dot` (2 KB)
  - `namespacetools_1_1llmprep_a929070bf51c742d3c582757de10f50f5_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_a980ccd4bf3e21443fbfed35710f895c3_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_aa319b2f21e97e10a16d320311f94ec68_cgraph.dot` (1 KB)
  - `namespacetools_1_1llmprep_aa319b2f21e97e10a16d320311f94ec68_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_abcd0488f00dd4447d9894ca8428fc09f_cgraph.dot` (4 KB)
  - `namespacetools_1_1llmprep_abcd0488f00dd4447d9894ca8428fc09f_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_adc453a8004d55d963611856fb9fae055_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_aea869e372d5ebe1bd4bb60ff65eef5b7_cgraph.dot` (1 KB)
  - `namespacetools_1_1llmprep_aea869e372d5ebe1bd4bb60ff65eef5b7_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_af6c0514c69d00c17a6679713530e0e7d_icgraph.dot` (0 KB)
  - `namespacetools_1_1llmprep_afaf3dd9e542148d869654fe84b5a2c1b_icgraph.dot` (2 KB)
  - `namespacetools_1_1minifier_a1630a58d0997c2a2b5a3ce016724addf_icgraph.dot` (1 KB)
  - `namespacetools_1_1minifier_a1891c0e16ec30fddff99c105a8c937b2_cgraph.dot` (0 KB)
  - `namespacetools_1_1minifier_a1891c0e16ec30fddff99c105a8c937b2_icgraph.dot` (1 KB)
  - `namespacetools_1_1minifier_a25b99dc57972f81c283eb4f4785fbb34_icgraph.dot` (1 KB)
  - `namespacetools_1_1minifier_a6518e5a9a554ade99baa729734a1bc32_icgraph.dot` (1 KB)
  - `namespacetools_1_1minifier_a90c1982b6a18089fdd441a06d159838e_icgraph.dot` (1 KB)
  - `namespacetools_1_1minifier_abfc117aec684ce9f71f3bc2b62816ff2_cgraph.dot` (0 KB)
  - `namespacetools_1_1minifier_abfc117aec684ce9f71f3bc2b62816ff2_icgraph.dot` (0 KB)
  - `namespacetools_1_1minifier_acbce42ca8e81d30a52cf2ea48e9f1055_cgraph.dot` (0 KB)
  - `namespacetools_1_1minifier_acbce42ca8e81d30a52cf2ea48e9f1055_icgraph.dot` (1 KB)
  - `namespacetools_1_1minifier_ae166d4d8a8bc0833f94cf2d7609e69b3_icgraph.dot` (1 KB)
  - `namespaceutils_1_1token__stats_a1e7eb57a760361efe5d08c347d5b8a39_icgraph.dot` (1 KB)
  - `namespaceutils_1_1token__stats_a54a42760c488a25025c244562ac9500b_cgraph.dot` (0 KB)
  - `namespaceutils_1_1token__stats_a54a42760c488a25025c244562ac9500b_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_a2cf71ce78b5013e106a63952168e63b6_cgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_a2cf71ce78b5013e106a63952168e63b6_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_a4251bc03225ee22aacfdb5869cd0b8f7_cgraph.dot` (4 KB)
  - `namespaceutils_1_1xml__tool__parser_a57988f65906393ac9687744afaca5b0e_icgraph.dot` (0 KB)
  - `namespaceutils_1_1xml__tool__parser_aa150ac2b37ac7c5d29a193a6b9331ada_icgraph.dot` (0 KB)
  - `namespaceutils_1_1xml__tool__parser_aa1de87a85f19c603d85018f0300dd820_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_aa45118f6c9307ce9543f0222b42894ec_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_aaca276344ac9dc2942732d2979bba627_cgraph.dot` (0 KB)
  - `namespaceutils_1_1xml__tool__parser_aaca276344ac9dc2942732d2979bba627_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_ac718012cbdfe70444dea3d2646aba8bf_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_acd18e34b8713011c876e3ae157a4fb6c_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_ad87245f63393791b038eb9fa6908a882_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_af0031b06895650625c760d44404c838b_icgraph.dot` (1 KB)
  - `namespaceutils_1_1xml__tool__parser_af092055a5bd17baa3af12fd97b3f8f4e_cgraph.dot` (3 KB)
  - `namespaceutils_1_1xml__tool__parser_af092055a5bd17baa3af12fd97b3f8f4e_icgraph.dot` (0 KB)
  - `namespaceworkshop_1_1hammer_a1c7a907566cb3ef4ac6a0d0376399573_icgraph.dot` (2 KB)
  - `namespaceworkshop_1_1hammer_a8c5ece0b4daa963e748911ada0b7f8f2_icgraph.dot` (2 KB)
  - `structGetNextBit__Data__coll__graph.dot` (1 KB)
  - `structGetNextByte__Data__coll__graph.dot` (0 KB)
  - `structNode__coll__graph.dot` (0 KB)
  - `structbitstream__coll__graph.dot` (1 KB)
  - `structdos__header__coll__graph.dot` (2 KB)
  - `structexepack__header__coll__graph.dot` (1 KB)
  - `structmemstream__coll__graph.dot` (1 KB)
  - `unlzexe_8c__incl.dot` (1 KB)
  - `unlzexe_8c_a006f22989de2042e481f380685a4bf55_cgraph.dot` (0 KB)
  - `unlzexe_8c_a006f22989de2042e481f380685a4bf55_icgraph.dot` (0 KB)
  - `unlzexe_8c_a019eabe66c4e1eb74dee48f721fce3a7_cgraph.dot` (0 KB)
  - `unlzexe_8c_a019eabe66c4e1eb74dee48f721fce3a7_icgraph.dot` (0 KB)
  - `unlzexe_8c_a38648f3d653a7637c80328a81f21fa31_cgraph.dot` (0 KB)
  - `unlzexe_8c_a38648f3d653a7637c80328a81f21fa31_icgraph.dot` (0 KB)
  - `unlzexe_8c_a3af47884cdb4a016fbee50af94b883ff_icgraph.dot` (0 KB)
  - `unlzexe_8c_a3c04138a5bfe5d72780bb7e82a18e627_cgraph.dot` (3 KB)
  - `unlzexe_8c_a64935c62813a7915e3a5db04d23290d9_icgraph.dot` (0 KB)
  - `unlzexe_8c_a81ee635bcd730cb2fe1a19fd1339e4f1_icgraph.dot` (0 KB)
  - `unlzexe_8c_a88a8845e0edb63f4a80a773bb60d1a29_icgraph.dot` (0 KB)
  - `unlzexe_8c_aaf416b3f984609e62a7dbbca9ec6c80a_cgraph.dot` (0 KB)
  - `unlzexe_8c_aaf416b3f984609e62a7dbbca9ec6c80a_icgraph.dot` (0 KB)
  - `unlzexe_8c_ac31e4a877b09226400b2ca4aa48987c0_icgraph.dot` (0 KB)
  - `unlzexe_8c_aca838a1cf52850e61f6014cdaef73c33_icgraph.dot` (1 KB)
  - `unlzexe_8c_ae673e158bc0bb8344206036a1e2884b5_icgraph.dot` (0 KB)
  - `unlzexe_8c_af8e30b9dd84d20734e79ef24efe86422_icgraph.dot` (0 KB)
  - `unpack_8c__incl.dot` (2 KB)
  - `unpack_8c_a0491863eefc3a0bff4f05873a06be10b_icgraph.dot` (0 KB)
  - `unpack_8c_a0ddf1224851353fc92bfbff6f499fa97_cgraph.dot` (5 KB)
  - `unpack_8c_a0dfa67fb32ccf515fe1d0bcbad6baaad_icgraph.dot` (0 KB)
  - `unpack_8c_a4f32bb963042b237f521b9041e51b657_icgraph.dot` (1 KB)
  - `unpack_8c_a60ebdc495a048f2a3952b84afc1c83a4_icgraph.dot` (1 KB)
  - `unpack_8c_a69d5dabed1fb8c2f4a1e18b77b53e5e7_cgraph.dot` (0 KB)
  - `unpack_8c_a69d5dabed1fb8c2f4a1e18b77b53e5e7_icgraph.dot` (0 KB)
  - `unpack_8c_a885224d332365560cd88c8b3d1b3eb07_cgraph.dot` (3 KB)
  - `unpack_8c_a885224d332365560cd88c8b3d1b3eb07_icgraph.dot` (0 KB)
  - `unpack_8c_aab7c23393b181e27f2f911fe1af86bf9_cgraph.dot` (0 KB)
  - `unpack_8c_aab7c23393b181e27f2f911fe1af86bf9_icgraph.dot` (0 KB)
  - `unpack_8c_ab166129a9f12c6e49a637c9f1f97c223_icgraph.dot` (1 KB)
  - `unpack_8c_ab566dc664a4e4d4f3ba1426886b6fa87_icgraph.dot` (1 KB)
  - `unpack_8c_ab948b8e984a81faa144a40843c3d66fd_icgraph.dot` (0 KB)
  - `unpack_8c_ace86dc31fa6f3fbad700399aff95d798_icgraph.dot` (0 KB)
  - `unpack_8c_acf701ccde86ffd36a6237db2dda542b0_icgraph.dot` (0 KB)
  - `unpack_8c_ae34b7b1297a5c90355c0211bfcdf0f9e_icgraph.dot` (1 KB)
  - `unpack_8c_ae7b3092ac9489d8d18f03866a3bc6c5b_cgraph.dot` (1 KB)
  - `unpack_8c_ae7b3092ac9489d8d18f03866a3bc6c5b_icgraph.dot` (0 KB)
  - `unpack_8c_aeea3f163bc06617cab408be25494545f_icgraph.dot` (0 KB)
  - `unpack_8c_aef3edf80d855356b2674782f3a083f68_icgraph.dot` (1 KB)

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
