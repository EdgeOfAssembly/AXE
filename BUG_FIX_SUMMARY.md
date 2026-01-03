# Bug Fix Summary - Multi-Agent Collaboration Issues

## Overview
This PR fixes 4 critical bugs that prevented multi-agent collaborative sessions from working correctly. These bugs caused agents to fail at creating files, spawned agents to never receive turns, token limit errors to go unhandled, and commands to execute twice.

## Bugs Fixed

### Bug 1: XML Tag Formats Not Supported ✅

**Problem**: Agents used XML formats (`<exec>`, `<read>`, `<write file="">`) that were not parsed by the system, causing all file operations to be silently ignored.

**Root Cause**: The `parse_simple_xml_tags()` function in `utils/xml_tool_parser.py` only supported `<read_file>`, `<shell>`, `<bash>`, and `<write_file path="">` formats. The simpler formats that agents actually used were not recognized.

**Fix**:
- Added parsing support for `<exec>command</exec>`
- Added parsing support for `<read>path</read>`
- Added parsing support for `<write file="path">content</write>`
- All three formats now properly mapped to READ, EXEC, and WRITE operations

**Files Modified**:
- `utils/xml_tool_parser.py` - Extended `parse_simple_xml_tags()` function

**Tests Added**:
- `test_xml_new_formats.py` - Comprehensive tests for all new formats

---

### Bug 2: Spawned Agents Never Get Turns ✅

**Problem**: When the supervisor spawned new agents, they were added to the agent list but could never receive turns because the agent resolution system didn't know about them.

**Root Cause**: 
- Spawned agents were registered using their UUID as the key in `self.agents`, `self.agent_ids`, and `self.agent_aliases`
- But `AgentManager.resolve_agent()` only knew about static agent names from config ('claude', 'gpt', etc.)
- When the main loop tried to resolve a UUID, it returned `None`, causing the agent to be skipped

**Fix**:
1. Added `self.spawned_agents` dictionary to `CollaborativeSession` to store dynamically spawned agent configurations
2. Updated `_handle_spawn_request()` to store full agent config including provider, model, and system prompt
3. Updated main loop to check `spawned_agents` first before calling `resolve_agent()`
4. Updated `_get_system_prompt_for_collab()` to handle both static and spawned agents
5. Added `_get_spawned_agent_system_prompt()` helper to provide appropriate prompts

**Files Modified**:
- `axe.py` - Multiple functions updated for spawned agent support

**Tests Added**:
- `test_spawned_agents.py` - Tests for data structures and resolution logic

---

### Bug 3: Token Limit Errors (413) Not Handled ✅

**Problem**: When agents hit 413 token limit errors, the system just captured it as a string response without any retry logic, detection, or recovery mechanism.

**Root Cause**: The API exception handler in the main collaboration loop used a generic `except Exception as e` that treated all errors the same, with no special handling for token limit issues.

**Fix**:
1. Enhanced exception handler to detect token limit errors by checking for:
   - HTTP 413 status code
   - 'tokens_limit_reached' in error message
   - 'context_length_exceeded' in error message
   - 'maximum context length' in error message

2. Implemented error tracking:
   - Increment error_count for each agent in database
   - Track consecutive token errors

3. Added automatic recovery:
   - After 3 token errors, force agent to sleep
   - Log all token errors with supervisor event tracking
   - Protect supervisor from being slept (must always be available)
   - Suggest spawning replacement agents

4. Improved error reporting:
   - Clear error messages indicating token limit issues
   - Error count displayed to help diagnose patterns
   - Truncated error messages for display and logging

**Files Modified**:
- `axe.py` - Enhanced API exception handler in main collaboration loop

**Tests Added**:
- `test_token_error_handling.py` - Tests for detection, tracking, and recovery

---

### Bug 4: Double Execution Bug ✅

**Problem**: Commands could be executed twice, wasting tokens and potentially causing issues like duplicate database inserts or double file writes with truncation.

**Root Cause**: Both `parse_all_tool_formats()` in xml_tool_parser.py and `ResponseProcessor.process_response()` in axe.py were processing native ```READ/WRITE/EXEC blocks, causing duplicate execution.

**Fix**: The fix was already implemented in a previous PR:
- `parse_axe_native_blocks()` call is commented out in `parse_all_tool_formats()`
- Native blocks are ONLY processed by `ResponseProcessor.process_response()`
- This ensures each command executes exactly once

**Verification**:
- Added comprehensive tests to verify the fix
- Documented the fix with clear comments in code
- Created integration tests to confirm single execution

**Files Verified**:
- `utils/xml_tool_parser.py` - Verified parse_axe_native_blocks() is commented out
- `axe.py` - Verified ResponseProcessor handles native blocks correctly

**Tests Added**:
- `test_double_execution.py` - Tests to verify and document the fix

---

## Test Results

All tests pass successfully:

```
✅ test_xml_new_formats.py - 6/6 tests passed
✅ test_spawned_agents.py - 4/4 tests passed  
✅ test_token_error_handling.py - 8/8 tests passed
✅ test_double_execution.py - 7/7 tests passed
✅ test_xml_tool_parser.py - All existing tests still pass
```

## Impact

These fixes enable:
1. **Functional File Operations**: Agents can now successfully create, read, and modify files using their preferred XML syntax
2. **Dynamic Team Scaling**: Supervisors can spawn new agents that properly participate in collaboration
3. **Resilient Operations**: Token limit errors are gracefully handled without crashing the session
4. **Reliable Execution**: Commands execute exactly once, preventing data corruption and wasted resources

## Backward Compatibility

All changes are backward compatible:
- Existing XML formats (`<read_file>`, `<shell>`, `<write_file path="">`) continue to work
- Static agent configuration unchanged
- Non-token API errors handled as before
- Native markdown blocks (```READ, ```EXEC, ```WRITE) work as expected

## Files Changed

- `utils/xml_tool_parser.py` - Added new XML tag format support
- `axe.py` - Fixed spawned agent registration and token error handling
- `test_xml_new_formats.py` - New test file
- `test_spawned_agents.py` - New test file
- `test_token_error_handling.py` - New test file
- `test_double_execution.py` - New test file

## Future Enhancements

Potential improvements for future PRs:
1. Retry logic with exponential backoff for token errors
2. Automatic context window reduction on token errors
3. More sophisticated agent replacement strategies
4. Metrics dashboard for agent error rates
5. Context window usage monitoring
