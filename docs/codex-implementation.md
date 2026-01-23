# GPT-5.2 Codex Implementation Guide

## Overview

This document explains how GPT-5.2 Codex support was added to AXE, including the Responses API integration.

## The Problem

GPT-5.2 Codex is **not a chat model**. When users tried to use it, they got:

```
⚠️ Error code: 404 - {'error': {'message': 'This is not a chat model and thus not 
supported in the v1/chat/completions endpoint. Did you mean to use v1/completions?', ...
```

## The Solution

GPT-5.2 Codex requires the **Responses API** (`/v1/responses`) instead of Chat Completions (`/v1/chat/completions`).

## Implementation Details

### 1. Model Metadata (`models.yaml`)

Added model with special `api_type` flag:

```yaml
gpt-5.2-codex:
  context_tokens: 400000
  max_output_tokens: 128000
  input_modes: [text, image]
  output_modes: [text, function_calling]
  api_type: responses  # Flag indicating Responses API
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

Created new agent with aliases and API endpoint override:

```yaml
gpt_codex:
  alias:
    - codex
    - gptcode
  provider: openai
  model: gpt-5.2-codex
  role: OpenAI's most advanced agentic coding model
  context_tokens: 400000
  api_endpoint: responses  # Override to use Responses API
  system_prompt: |
    You are GPT-5.2 Codex...
```

### 4. Helper Function (`models/metadata.py`)

Added detection function:

```python
def uses_responses_api(model: str) -> bool:
    """Check if a model requires the Responses API."""
    model_info = get_model_info(model)
    return model_info.get('api_type') == 'responses'
```

### 5. API Call Logic (`core/agent_manager.py`)

Updated OpenAI provider handling:

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

Users can invoke GPT-5.2 Codex with:

```bash
@gpt_codex   # Direct name
@codex       # Alias
@gptcode     # Alias
```

The system automatically routes to the correct API endpoint.

## Testing

Added comprehensive tests:

1. **`test_codex_agent.py`**: Tests agent configuration and metadata
2. **`test_codex_integration.py`**: Tests API endpoint selection logic
3. **`test_models_yaml.py`**: Tests model metadata and helper functions
4. **`validate_codex_config.py`**: Comprehensive validation script

All tests verify:
- Correct API detection
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
