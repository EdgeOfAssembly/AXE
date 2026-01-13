# Anthropic Claude-Specific Features in AXE

This document describes the Anthropic Claude-specific optimizations implemented in AXE to enable handling large codebases more efficiently with minimal token count and cost.

## Overview

AXE now includes four major Anthropic-specific features:

1. **Prompt Caching** (Highest Priority) - Significantly reduces processing time and costs for repetitive tasks
2. **Extended Thinking** - Enhanced reasoning capabilities for complex tasks
3. **Token Counting** - Precise token counts from Anthropic API
4. **Files API** (Beta) - Upload large files once, reference multiple times

All features are **opt-in** and maintain **full backward compatibility** with other providers (OpenAI, xAI, HuggingFace, GitHub).

## Features

### 1. Prompt Caching

Prompt caching reduces costs by reusing previously processed content. The cache has a 5-minute lifetime by default and is automatically refreshed when used.

#### Configuration

In `models.yaml`:

```yaml
anthropic:
  prompt_caching:
    enabled: true                              # Enable prompt caching
    cache_breakpoints: ["system", "tools"]     # What to cache
    default_ttl: "5m"                          # Cache lifetime: "5m" or "1h"
```

#### How It Works

- Static content (system prompts, tool definitions) is automatically cached
- Cache is created on first use (costs normal rate)
- Subsequent uses read from cache (90% cost reduction)
- Cache refreshes automatically when accessed within TTL

#### Token Savings Example

```
First call:  10,000 input tokens → Normal cost
Second call: 9,500 cached + 500 new → ~90% savings
Third call:  9,500 cached + 500 new → ~90% savings
```

#### Automatic Features

- AXE automatically converts system prompts to cacheable format
- Cache statistics are tracked and logged:
  - `cache_creation_input_tokens` - Tokens used to create cache
  - `cache_read_input_tokens` - Tokens read from cache
  - Cache hit rate and savings percentage

#### Example Output

```
Cache created: 2000 tokens
Cache hit: 1800 tokens read (90.0% of input)
```

### 2. Extended Thinking

Extended thinking gives Claude enhanced reasoning capabilities for complex tasks, with step-by-step thought process.

#### Configuration

Extended thinking is configured per model in `models.yaml`:

```yaml
models:
  claude-opus-4-5-20251101:
    extended_thinking:
      enabled: true
      budget_tokens: 32000     # Maximum tokens for reasoning
  
  claude-sonnet-4-5-20250929:
    extended_thinking:
      enabled: true
      budget_tokens: 16000
  
  claude-haiku-4-5-20251001:
    extended_thinking:
      enabled: true
      budget_tokens: 10000
```

#### Supported Models

- Claude Opus 4.5, 4.1, 4.0 (budget: 24k-32k tokens)
- Claude Sonnet 4.5, 4.0 (budget: 16k tokens)
- Claude Haiku 4.5 (budget: 10k tokens)

#### How It Works

- Claude creates internal `thinking` blocks before responding
- Thinking is transparent (you can see the reasoning)
- Thinking blocks include cryptographic signatures for verification
- Claude incorporates insights from reasoning into final response

#### Example

```python
# Extended thinking is automatically enabled for supported models
response = agent_manager.call_agent('coder', 'Write optimized algorithm...')
# Claude will think through the problem step-by-step internally
# Then provide the optimized solution
```

Console output:
```
Extended thinking enabled with budget: 32000 tokens
```

### 3. Token Counting

Get precise token counts from Anthropic's API before sending large messages.

#### Configuration

```yaml
anthropic:
  token_counting:
    enabled: true
    threshold_estimated_tokens: 10000   # Use precise counting above this
```

#### How It Works

1. AXE estimates tokens using `char_count / 4` heuristic
2. If estimate > 10,000 tokens, calls Anthropic's `/v1/messages/count_tokens` endpoint
3. Uses precise count for optimization decisions
4. Non-Anthropic providers continue using estimation

#### API Usage

```python
# Automatic - happens internally in agent_manager
agent_manager.call_agent('coder', large_prompt)

# Manual - for custom use cases
token_count = agent_manager.count_tokens_anthropic(
    model='claude-opus-4-5-20251101',
    messages=[{'role': 'user', 'content': 'Your prompt here'}],
    system='System prompt',
    tools=[...]  # Optional
)
```

#### Benefits

- Avoid rate limits by knowing exact token counts
- Make informed model routing decisions
- Optimize prompts to specific lengths
- Prevent failed requests due to token limits

### 4. Files API (Beta)

Upload large files once, reference multiple times without re-uploading.

#### Configuration

```yaml
anthropic:
  files_api:
    enabled: false                  # Beta feature, disabled by default
    upload_threshold_kb: 50         # Auto-upload files > 50KB
    supported_types:
      - "application/pdf"
      - "text/plain"
      - "image/jpeg"
      - "image/png"
```

#### How It Works

1. Upload file: `file_id = files_manager.upload_file('/path/to/document.pdf')`
2. Store `file_id` in session data
3. Reference file in messages using `file_id` instead of content
4. File persists for duration of session

#### Usage

```python
from core.anthropic_features import get_files_api_manager

# Initialize manager
files_manager = get_files_api_manager(client, config)

# Upload file
file_info = files_manager.upload_file('/path/to/large_document.pdf')
if file_info:
    file_id = file_info['id']
    # Store file_id in session for later reference
```

**Note**: Files API implementation is a placeholder. Full support requires Anthropic SDK updates.

## Token Statistics with Cache Tracking

The `TokenStats` class now tracks cache performance:

```python
from utils.token_stats import TokenStats

stats = TokenStats()

# Standard usage tracking
stats.add_usage('agent1', 'claude-opus-4-5-20251101', 1000, 500)

# Usage with cache tracking
stats.add_usage('agent1', 'claude-opus-4-5-20251101', 500, 300,
                cache_creation_tokens=2000,
                cache_read_tokens=1800)

# Get statistics
agent_stats = stats.get_agent_stats('agent1')
print(f"Cache hits: {agent_stats['cache']['hits']}")
print(f"Cache hit rate: {agent_stats['cache']['hit_rate']:.1%}")

total_stats = stats.get_total_stats()
print(f"Total cache savings: {total_stats['cache']['read']} tokens")
```

## Configuration Reference

Complete `models.yaml` configuration:

```yaml
# Anthropic-specific configuration
anthropic:
  # Prompt caching - reduces costs for repetitive prompts
  prompt_caching:
    enabled: true
    cache_breakpoints: ["system", "tools"]
    default_ttl: "5m"              # "5m" (free refresh) or "1h" (premium)
  
  # Files API - upload large files once, reference multiple times
  files_api:
    enabled: false                 # Beta feature, disabled by default
    upload_threshold_kb: 50
    supported_types: ["application/pdf", "text/plain", "image/jpeg", "image/png"]
  
  # Token counting - use precise API counts for large prompts
  token_counting:
    enabled: true
    threshold_estimated_tokens: 10000

# Per-model extended thinking configuration
models:
  claude-opus-4-5-20251101:
    context_tokens: 200000
    max_output_tokens: 64000
    input_modes: [text, image]
    output_modes: [text, function_calling]
    extended_thinking:
      enabled: true
      budget_tokens: 32000
  
  claude-sonnet-4-5-20250929:
    context_tokens: 200000
    max_output_tokens: 64000
    input_modes: [text, image]
    output_modes: [text, function_calling]
    extended_thinking:
      enabled: true
      budget_tokens: 16000
  
  claude-haiku-4-5-20251001:
    context_tokens: 200000
    max_output_tokens: 8000
    input_modes: [text, image]
    output_modes: [text, function_calling]
    extended_thinking:
      enabled: true
      budget_tokens: 10000
```

## Backward Compatibility

All features maintain full backward compatibility:

- **Non-Anthropic providers**: Features are skipped automatically
- **Token callbacks**: Support both standard (4 params) and enhanced (6 params with cache)
- **Existing code**: No changes required to existing code
- **Configuration**: All features are opt-in via configuration

## Performance Impact

Based on integration tests:

- **Prompt Caching**: Up to 90% token cost reduction on cached content
- **Extended Thinking**: Improved quality on complex tasks (small cost increase for thinking)
- **Token Counting**: Negligible overhead (free API, called only for large prompts)
- **Files API**: Eliminates redundant uploads for large files

### Example Workflow Savings

```
Scenario: Code analysis with large codebase context

Without caching:
  Call 1: 15,000 input tokens → $0.225 cost
  Call 2: 15,000 input tokens → $0.225 cost
  Call 3: 15,000 input tokens → $0.225 cost
  Total: 45,000 tokens → $0.675

With caching:
  Call 1: 15,000 input tokens → $0.225 cost (cache creation)
  Call 2: 14,000 cached + 1,000 new → $0.037 cost (90% savings)
  Call 3: 14,000 cached + 1,000 new → $0.037 cost (90% savings)
  Total: 18,000 billable tokens → $0.299 (56% overall savings)
```

## Testing

Comprehensive test coverage:

- **Unit tests**: `tests/test_anthropic_features.py` (10 tests)
- **Integration tests**: `tests/test_anthropic_integration.py` (8 tests)
- **Backward compatibility**: All existing tests pass

Run tests:
```bash
python tests/test_anthropic_features.py
python tests/test_anthropic_integration.py
python tests/test_models_yaml.py  # Backward compatibility
```

## Troubleshooting

### Caching not working

1. Check config: `prompt_caching.enabled: true` in `models.yaml`
2. Verify Anthropic API key is set
3. Ensure using streaming API (AXE does this automatically)
4. Check cache TTL hasn't expired (5 minutes default)

### Extended thinking not available

1. Verify model supports extended thinking (Claude 4.x series only)
2. Check `extended_thinking.enabled: true` for model in `models.yaml`
3. Ensure sufficient `budget_tokens` configured

### Token counting fails

1. Check `token_counting.enabled: true`
2. Verify Anthropic client initialized
3. Reduce threshold if needed (default: 10,000 tokens)

### Files API not working

1. Feature is beta - `enabled: false` by default
2. Requires Anthropic SDK updates (placeholder implementation)
3. Check beta header: `anthropic-beta: files-api-2025-04-14`

## References

- **Prompt Caching**: `/home/runner/work/AXE/AXE/claude/ocr_out/Prompt caching - Claude Docs.txt`
- **Extended Thinking**: `/home/runner/work/AXE/AXE/claude/ocr_out/Building with extended thinking - Claude Docs.txt`
- **Token Counting**: `/home/runner/work/AXE/AXE/claude/ocr_out/Token counting - Claude Docs.txt`
- **Files API**: `/home/runner/work/AXE/AXE/claude/ocr_out/Files API - Claude Docs.txt`

## Support

For issues or questions:
1. Check configuration in `models.yaml`
2. Review test files for usage examples
3. Check Anthropic API status and documentation
4. Verify API key and rate limits
