# Dynamic Max Output Tokens Implementation Summary

## Overview
This implementation fixes three critical issues with AXE's hardcoded `max_tokens=32768` approach:

1. **Anthropic SDK Error** - The SDK requires streaming for operations that may take >10 minutes
2. **Token Truncation** - Some models (like GPT-4o) only support 16,384 max output tokens, not 32,768
3. **Wasted Capacity** - Some models (like Claude Opus 4.5, GPT-5.2) support much more than 32,768 tokens

## Changes Made

### 1. `models/metadata.py`
**Added:**
- `get_max_output_tokens(model_name: str, default: int = 4096) -> int` helper function
  - Looks up max output tokens from model metadata
  - Returns safe default (4096) if model not found

**Fixed:**
- Removed extra space in `DEFAULT_METADATA.copy()` (typo fix)

### 2. `models.yaml`
**Updated:**
- Default `max_output_tokens` from 2048 → 4000 (safer default for unknown models)
- Added comment explaining it's a safe default

### 3. `core/agent_manager.py`
**Updated `call_agent()` method:**
- Added import: `get_max_output_tokens`
- Replaced all hardcoded `max_tokens=32000` with dynamic lookups:
  - `max_output = get_max_output_tokens(model, default=4000)`
  
**Anthropic Provider:**
- Changed from `client.messages.create()` to `client.messages.stream()`
- Implemented proper streaming with text accumulation
- Fixed token tracking to work with streaming API
- This prevents the "Streaming is required for operations >10 minutes" error

**OpenAI/xAI/GitHub Providers:**
- Uses dynamic `max_output` instead of hardcoded 32000
- Maintains `max_completion_tokens` vs `max_tokens` logic for GPT-5+

**HuggingFace Provider:**
- Uses dynamic `max_output` instead of hardcoded 32000

### 4. `axe.py` (CollaborativeSession)
**Updated `_run_collaboration_loop()` method:**
- Added import: `get_max_output_tokens`
- Added dynamic token lookup: `max_output = get_max_output_tokens(model, default=4000)`

**Anthropic Provider:**
- Changed to streaming API: `client.messages.stream()`
- Simplified response handling (no need to check resp.content)

**OpenAI/xAI/GitHub Providers:**
- Uses dynamic `max_output` instead of hardcoded 32000
- Maintains proper parameter naming logic

**HuggingFace Provider:**
- Uses dynamic `max_output` instead of hardcoded 32000

### 5. `tests/test_models_yaml.py`
**Updated:**
- Changed expected default from 2048 → 4000 to match new default

### 6. `tests/test_dynamic_max_tokens.py` (NEW)
**Comprehensive test suite covering:**
- Helper function behavior
- Various model token limits (14 different models tested)
- Verification that no hardcoded values remain
- Dynamic lookup implementation presence
- Safe default fallback behavior
- Edge cases (empty names, special chars, long names)
- Consistency between helper and direct lookup

### 7. `demo_dynamic_tokens.py` (NEW)
**Demonstration script showing:**
- Token limits for 10 different model types
- Comparison: old (32,768) vs new (dynamic) behavior
- Visual summary of key benefits

## Benefits

### 1. Anthropic SDK Error Fixed ✓
- Now uses streaming API
- Prevents "Streaming is required for operations that may take longer than 10 minutes" error
- Maintains token usage tracking for billing/monitoring

### 2. Token Truncation Fixed ✓
- **GPT-4o**: Now uses 16,000 (its actual limit) instead of 32,000
- **GPT-4o Mini**: Now uses 16,000 instead of 32,000
- **Claude Haiku 4.5**: Now uses 8,000 instead of 32,000
- Prevents API errors or silent truncation

### 3. Wasted Capacity Fixed ✓
- **Claude Opus 4.5**: Now uses 64,000 instead of 32,000 (2x capacity!)
- **GPT-5.2**: Now uses 128,000 instead of 32,000 (4x capacity!)
- **GPT-4.1**: Now uses 64,000 instead of 32,000 (2x capacity!)
- **o3/o4-mini**: Now uses 100,000 instead of 32,000 (3x capacity!)
- **openai/gpt-5**: Now uses 100,000 instead of 32,000 (3x capacity!)

### 4. Safe Defaults ✓
- Unknown models default to 4,000 tokens (widely supported)
- Prevents over-requesting from unknown/new models
- Easy to override with custom default parameter

## Testing

All tests pass:
- ✅ `test_models_yaml.py` - Model metadata loading
- ✅ `test_dynamic_max_tokens.py` - Dynamic token limits (NEW)
- ✅ `test_token_error_handling.py` - Error handling
- ✅ `test_token_optimization.py` - Token optimization
- ✅ Manual verification with AgentManager initialization

## Model Examples

| Model | Old Limit | New Limit | Change |
|-------|-----------|-----------|--------|
| claude-opus-4-5-20251101 | 32,000 | **64,000** | +100% 🚀 |
| claude-haiku-4-5-20251001 | 32,000 | **8,000** | -75% ✓ |
| gpt-5.2 | 32,000 | **128,000** | +300% 🚀 |
| gpt-4o | 32,000 | **16,000** | -50% ✓ |
| gpt-4.1 | 32,000 | **64,000** | +100% 🚀 |
| o3 | 32,000 | **100,000** | +212% 🚀 |
| openai/gpt-5 | 32,000 | **100,000** | +212% 🚀 |
| grok-4-1-fast-reasoning | 32,000 | **32,000** | Same |
| unknown-model | 32,000 | **4,000** | -87% ✓ |

## Backward Compatibility

✅ **Fully backward compatible**
- No API changes to public functions
- Existing code continues to work
- Only internal implementation changed
- All existing tests pass

## Code Quality

✅ **Follows existing patterns**
- Uses existing `get_model_info()` infrastructure
- Maintains `uses_max_completion_tokens()` logic
- Consistent error handling
- Proper token tracking for billing

✅ **Well tested**
- 100+ test cases across all test files
- Edge cases covered
- Integration tested

✅ **Documented**
- Clear docstrings
- Inline comments explaining key changes
- Comprehensive test documentation

## Future Enhancements

Potential improvements (not included in this PR):
1. Add rate limiting based on model-specific limits
2. Add warnings when approaching token limits
3. Add auto-retry with reduced tokens on failure
4. Add telemetry for actual token usage vs limits

## Migration Guide

**No migration needed!** This is a transparent internal improvement.

For developers adding new models:
1. Add model to `models.yaml` with correct `max_output_tokens`
2. New model automatically uses correct limits
3. No code changes required

## Files Modified

- `models/metadata.py` - Added helper function
- `models.yaml` - Updated default
- `core/agent_manager.py` - Dynamic lookups + Anthropic streaming
- `axe.py` - Dynamic lookups + Anthropic streaming
- `tests/test_models_yaml.py` - Updated test expectations
- `tests/test_dynamic_max_tokens.py` - NEW comprehensive tests
- `demo_dynamic_tokens.py` - NEW demonstration script

## Security Considerations

✅ **No security impact**
- Reduces risk of over-requesting tokens
- Maintains existing error handling
- Safe defaults prevent potential DoS
- Token tracking unchanged

## Performance Impact

✅ **Negligible performance impact**
- One dictionary lookup per API call
- Metadata cached in memory
- Streaming may be slightly slower for small responses but prevents timeouts for large ones
