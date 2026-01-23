# GPT-5.2 Codex Implementation Guide

## Overview

This document explains how GPT-5.2 Codex support was added to AXE, including the Responses API integration and reasoning effort parameter support.

## The Problem

GPT-5.2 Codex is **not a chat model**. When users tried to use it, they got:

```
⚠️ Error code: 404 - {'error': {'message': 'This is not a chat model and thus not 
supported in the v1/chat/completions endpoint. Did you mean to use v1/completions?', ...
```

## The Solution

GPT-5.2 Codex requires the **Responses API** (`/v1/responses`) instead of Chat Completions (`/v1/chat/completions`).

## Reasoning Effort Parameter

GPT-5.2 Codex supports different **reasoning effort levels** that control how much "thinking" the model does before responding. Higher reasoning effort produces better results for complex tasks but increases latency and cost.

### Reasoning Effort Levels

| Level | Description | Best For | Latency | Cost |
|-------|-------------|----------|---------|------|
| `none` | Fastest, minimal deliberation | Basic tasks, high throughput | ⚡ Lowest | 💰 Cheapest |
| `low` | Quick responses, simple logic | Simple code generation | ⚡⚡ | 💰💰 |
| `medium` | Balanced speed/reasoning | Day-to-day coding, bug fixes | ⚡⚡⚡ | 💰💰💰 |
| `high` | Increased deliberation | Complex engineering, multi-step planning | 🐢 | 💰💰💰💰 |
| `xhigh` | Maximum reasoning depth | Multi-file refactoring, deep debugging | 🐢🐢 Slowest | 💰💰💰💰💰 |

### Pre-configured Reasoning Variants

AXE provides convenient pre-configured agents with different reasoning levels:

- **`gpt_codex`** (aliases: `codex`, `gptcode`) - Standard with `medium` reasoning
- **`gpt_codex_fast`** (aliases: `codex-fast`, `cf`) - Fast with `low` reasoning  
- **`gpt_codex_high`** (aliases: `codex-high`, `ch`) - Enhanced with `high` reasoning
- **`gpt_codex_xhigh`** (aliases: `codex-xhigh`, `cx`) - Maximum with `xhigh` reasoning

### When to Use Each Level

**Use `none` or `low` for:**
- Simple code generation
- Quick bug fixes
- Straightforward refactoring
- High-throughput scenarios

**Use `medium` (default) for:**
- Day-to-day coding tasks
- Moderate complexity bug fixes
- Standard refactoring
- Balanced speed and quality

**Use `high` for:**
- Complex algorithm design
- Multi-step problem solving
- Performance optimization
- Debugging challenging issues

**Use `xhigh` for:**
- Architectural decisions
- Major refactoring across multiple files
- Security audits
- Deep debugging of systemic issues

## Implementation Details

### 1. Model Metadata (`models.yaml`)

Added model with special `api_type` flag and reasoning effort support:

```yaml
gpt-5.2-codex:
  context_tokens: 400000
  max_output_tokens: 128000
  input_modes: [text, image]
  output_modes: [text, function_calling]
  api_type: responses  # Flag indicating Responses API
  supports_reasoning_effort: true  # Flag indicating reasoning effort is supported
  default_reasoning_effort: medium  # Default level if not overridden
```

Also added to `use_max_completion_tokens` list since it's a GPT-5.2 variant.

### 2. Provider Configuration (`providers.yaml`)

Added to OpenAI provider's models list:

```yaml
openai:
  models:
    - gpt-5.2-codex
    # ... other models
```

### 3. Agent Configuration (`axe.yaml`)

Created multiple agent variants with different reasoning levels:

```yaml
gpt_codex:
  alias: [codex, gptcode]
  provider: openai
  model: gpt-5.2-codex
  reasoning_effort: medium  # Default reasoning level
  role: OpenAI's most advanced agentic coding model
  context_tokens: 400000
  api_endpoint: responses  # Override to use Responses API
  system_prompt: |
    You are GPT-5.2 Codex...

# Fast variant (low reasoning for quick tasks)
gpt_codex_fast:
  alias: [codex-fast, cf]
  provider: openai
  model: gpt-5.2-codex
  reasoning_effort: low  # Low reasoning for speed
  role: Fast coding assistant for quick code generation
  # ...

# High reasoning variant (for complex tasks)
gpt_codex_high:
  alias: [codex-high, ch]
  provider: openai
  model: gpt-5.2-codex
  reasoning_effort: high  # High reasoning for complex problems
  role: Deep reasoning specialist for complex multi-step problems
  # ...

# Maximum reasoning variant (for architectural decisions)
gpt_codex_xhigh:
  alias: [codex-xhigh, cx]
  provider: openai
  model: gpt-5.2-codex
  reasoning_effort: xhigh  # Maximum reasoning depth
  role: Maximum reasoning for architectural decisions and major refactoring
  # ...
```

### 4. Helper Functions (`models/metadata.py`)

Added detection and validation functions:

```python
def uses_responses_api(model: str) -> bool:
    """Check if a model requires the Responses API."""
    model_info = get_model_info(model)
    return model_info.get('api_type') == 'responses'

def supports_reasoning_effort(model: str) -> bool:
    """Check if a model supports reasoning effort parameter."""
    model_info = get_model_info(model)
    return model_info.get('supports_reasoning_effort', False)

def get_default_reasoning_effort(model: str) -> Optional[str]:
    """Get the default reasoning effort level for a model."""
    model_info = get_model_info(model)
    return model_info.get('default_reasoning_effort', None)

VALID_REASONING_EFFORTS = {'none', 'low', 'medium', 'high', 'xhigh'}

def validate_reasoning_effort(effort: str) -> bool:
    """Validate that reasoning effort is a valid value."""
    return effort in VALID_REASONING_EFFORTS
```

### 5. API Call Logic (`core/agent_manager.py`)

Updated OpenAI provider handling with reasoning effort support:

```python
elif provider in ['openai', 'xai', 'github', 'ollama']:
    # Detect Responses API requirement
    uses_responses = uses_responses_api(model) or agent.get('api_endpoint') == 'responses'
    
    if uses_responses:
        # Use Responses API
        api_params = {
            'model': model,
            'input': full_prompt,  # Note: 'input' not 'messages'
        }
        if system_prompt:
            api_params['instructions'] = system_prompt  # Note: 'instructions'
        
        api_params['max_output_tokens'] = max_output
        
        # Add reasoning effort if supported
        if supports_reasoning_effort(model):
            # Priority: agent config > model default > None (omit parameter)
            reasoning_effort = agent.get('reasoning_effort') or get_default_reasoning_effort(model)
            if reasoning_effort:
                if validate_reasoning_effort(reasoning_effort):
                    api_params['reasoning'] = {'effort': reasoning_effort}
                    print(c(f"Reasoning effort: {reasoning_effort}", Colors.CYAN))
                else:
                    print(c(f"Warning: Invalid reasoning effort '{reasoning_effort}', ignoring", Colors.YELLOW))
        
        resp = client.responses.create(**api_params)
        
        # Track tokens
        if token_callback and hasattr(resp, 'usage'):
            input_tokens = getattr(resp.usage, 'input_tokens', 0)
            output_tokens = getattr(resp.usage, 'output_tokens', 0)
            token_callback(agent_name, model, input_tokens, output_tokens)
        
        return resp.output_text  # Note: 'output_text' not 'choices'
    else:
        # Standard Chat Completions API (existing code)
        ...
```

## Key Differences: Responses API vs Chat Completions

| Feature | Chat Completions | Responses API |
|---------|-----------------|---------------|
| Endpoint | `/v1/chat/completions` | `/v1/responses` |
| Input Parameter | `messages` (list of dicts) | `input` (string) |
| System Prompt | `messages[0]` with role='system' | `instructions` (string) |
| Output Param | `max_tokens` or `max_completion_tokens` | `max_output_tokens` |
| **Reasoning Effort** | N/A | `reasoning` = `{'effort': 'low'\|'medium'\|'high'\|'xhigh'\|'none'}` |
| Response Field | `resp.choices[0].message.content` | `resp.output_text` |
| Token Usage | `resp.usage.prompt_tokens` | `resp.usage.input_tokens` |
| Token Usage | `resp.usage.completion_tokens` | `resp.usage.output_tokens` |

## Detection Logic

The system determines which API to use via:

1. **Model metadata**: `api_type: responses` in `models.yaml`
2. **Agent config override**: `api_endpoint: responses` in `axe.yaml`
3. **Detection function**: `uses_responses_api(model)` returns True if either condition is met

This allows:
- Automatic detection based on model
- Manual override per agent if needed
- Easy addition of future Responses API models

## Usage

Users can invoke GPT-5.2 Codex with different reasoning levels:

```bash
# Standard (medium reasoning)
@gpt_codex   # Direct name
@codex       # Alias
@gptcode     # Alias

# Fast (low reasoning)
@gpt_codex_fast  # Direct name
@codex-fast      # Alias
@cf              # Short alias

# High reasoning
@gpt_codex_high  # Direct name
@codex-high      # Alias
@ch              # Short alias

# Maximum reasoning
@gpt_codex_xhigh  # Direct name
@codex-xhigh      # Alias
@cx               # Short alias
```

The system automatically routes to the correct API endpoint and applies the appropriate reasoning effort level.

## Testing

Added comprehensive tests:

1. **`test_codex_agent.py`**: Tests agent configuration and metadata
2. **`test_codex_integration.py`**: Tests API endpoint selection logic
3. **`test_models_yaml.py`**: Tests model metadata and helper functions
4. **`test_reasoning_effort.py`**: Tests reasoning effort parameter support (16 tests)
5. **`validate_codex_config.py`**: Comprehensive validation script

All tests verify:
- Correct API detection
- Reasoning effort parameter handling
- Agent config override priority
- Validation of reasoning effort levels
- Backwards compatibility
- No regression in existing agents

## Backwards Compatibility

✅ **No breaking changes:**
- Regular GPT models (gpt-5.2, gpt-4o, etc.) still use Chat Completions
- Claude models unaffected
- All existing tests pass
- Existing agents work unchanged

## Future Extensions

To add more Responses API models:

1. Add model to `models.yaml` with `api_type: responses`
2. Add model to appropriate provider in `providers.yaml`
3. Optionally create agent in `axe.yaml`

The detection logic will handle it automatically.

## References

- OpenAI Responses API: https://platform.openai.com/docs/api-reference/responses
- OpenAI Chat Completions API: https://platform.openai.com/docs/api-reference/chat
