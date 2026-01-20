# Configuration Architecture

AXE uses a three-file configuration architecture that separates static model data, provider infrastructure, and user-customizable settings. This design provides clean separation of concerns and makes the system easier to maintain and extend.

## Overview

```
models.yaml      → Static model metadata (loaded FIRST)
    ↓
providers.yaml   → Provider infrastructure (loaded SECOND)
    ↓
axe.yaml         → User configuration (loaded THIRD)
```

The loading order ensures that:
1. Model capabilities are defined before providers reference them
2. Provider configurations are validated before agents use them
3. User settings override defaults where appropriate

## File Descriptions

### 1. models.yaml (Static Model Reference Data)

**Purpose**: Pure, static model specifications that rarely change

**Contains**:
- `context_tokens` - Maximum input context window size
- `max_output_tokens` - Maximum output tokens per generation
- `input_modes` - Supported input types (text, image, audio, etc.)
- `output_modes` - Supported output types (text, function_calling, etc.)
- Provider-specific features (prompt_caching, extended_thinking, etc.)
- Cost information (optional)

**Example**:
```yaml
models:
  gpt-4o:
    context_tokens: 128000
    max_output_tokens: 16000
    input_modes: [text, image, audio]
    output_modes: [text, function_calling]
  
  claude-sonnet-4-5-20250929:
    context_tokens: 200000
    max_output_tokens: 64000
    input_modes: [text, image]
    output_modes: [text, function_calling]
    extended_thinking:
      enabled: true
      budget_tokens: 16000
```

**Key Rules**:
- All model IDs must be **lowercase**
- **No provider prefixes** (except GitHub Models which uses them by design)
- This is the **single source of truth** for model capabilities

### 2. providers.yaml (Provider Infrastructure)

**Purpose**: Provider connection and infrastructure details

**Contains**:
- `enabled` - Whether the provider is active
- `env_key` - Environment variable name for API key
- `base_url` - API endpoint URL (null for defaults)
- `models` - List of available models from this provider

**Example**:
```yaml
providers:
  anthropic:
    enabled: true
    env_key: ANTHROPIC_API_KEY
    base_url: null  # Uses default Anthropic endpoint
    models:
      - claude-opus-4-5-20251101
      - claude-sonnet-4-5-20250929
      - claude-haiku-4-5-20251001

  ollama:
    enabled: false  # Disabled by default, users enable when ready
    env_key: OLLAMA_API_KEY  # Placeholder
    base_url: http://localhost:11434/v1
    models:
      - llama3.1:70b
      - llama3.1:8b
```

**Key Features**:
- Providers can be enabled/disabled without editing agent definitions
- All models listed must exist in `models.yaml` (validated on load)
- Supports custom base URLs for self-hosted or regional endpoints

### 3. axe.yaml (User Configuration)

**Purpose**: User-focused, freely modifiable settings

**Contains**:
- Project settings (project_dir, version, etc.)
- Agent definitions with provider + model selection
- **Optional overrides** for model attributes (context_tokens, temperature, etc.)
- Multi-agent collaboration settings
- Tool configurations
- Directory access rules
- Sandbox settings

**Example**:
```yaml
agents:
  claude:
    provider: anthropic
    model: claude-sonnet-4-5-20250929
    # No context_tokens here - inherits from models.yaml
    role: "Expert coding assistant"
    system_prompt: "You are an expert..."

  gpt:
    provider: openai
    model: gpt-4o
    context_tokens: 64000  # OVERRIDE: Cap lower than model's 128k for cost
    role: "General assistant"
    system_prompt: "You are a helpful..."

  local:
    provider: ollama
    model: llama3.1:70b
    context_tokens: 32000  # OVERRIDE: Limited by local VRAM
    role: "Local private coding agent"
```

**Key Features**:
- Agents inherit model metadata from `models.yaml`
- Override attributes only when intentional (with comments explaining why)
- All model IDs must match those defined in `providers.yaml`

## Configuration Loading Process

### Startup Sequence

1. **Load models.yaml**
   - Parse static model metadata
   - Store in `models_config`
   - Display: `✓ models.yaml (87 models loaded)`

2. **Load providers.yaml**
   - Parse provider configurations
   - Validate all models exist in `models.yaml`
   - Store in `providers_config`
   - Display: `✓ providers.yaml (7 enabled, 1 disabled (ollama))`

3. **Load axe.yaml**
   - Parse user configuration
   - Validate agents against providers and models
   - Merge with defaults
   - Display: `✓ axe.yaml (19 agents configured)`

4. **Final Validation**
   - Check all agent providers are enabled
   - Check all agent models are in provider's model list
   - Check model IDs are lowercase
   - Display: `Configuration validated successfully.`

### Example Startup Output

```
Loading configuration...
  ✓ models.yaml (87 models loaded)
  ✓ providers.yaml (7 enabled, 1 disabled (ollama))
  ✓ axe.yaml (19 agents configured)
Configuration validated successfully.
```

### Validation Errors

If configuration issues are detected, clear error messages are shown:

```
✗ Validation Error: Agent 'claude' uses model 'Claude-3-Opus' 
  but model IDs must be lowercase. Did you mean 'claude-3-opus'?

✗ Validation Error: Agent 'local' uses provider 'ollama' 
  but it is disabled in providers.yaml. Enable it first.

✗ Validation Error: Provider 'openai' lists model 'gpt-5' 
  but it's not defined in models.yaml.
```

## Key Naming Standard: `context_tokens`

All configuration files use `context_tokens` as the standard key name for context window size:

```yaml
# ✓ Correct
context_tokens: 128000

# ✗ Deprecated
context_window: 128000
```

This standardization ensures consistency across:
- models.yaml model definitions
- axe.yaml agent overrides
- Python code accessing context size

## Model ID Rules

### General Rule: Lowercase, No Prefixes

```yaml
# ✓ Correct
- gpt-4o
- claude-sonnet-4-5-20250929
- llama3.1:70b

# ✗ Incorrect
- GPT-4o                    # Uppercase
- openai/gpt-4o            # Has provider prefix
- Llama-3.1-70B-Instruct   # Mixed case
```

### Exception: GitHub Models

GitHub Models API uses prefixed IDs by design - keep them as-is:

```yaml
github:
  models:
    - openai/gpt-4o          # ✓ Correct for GitHub
    - meta/llama-3.3-70b-instruct
    - mistral-ai/codestral-2501
```

## Agent Overrides

Agents can override model defaults for specific use cases:

### Use Cases for Overrides

1. **Cost Control**: Cap context lower to reduce API costs
   ```yaml
   gpt:
     model: gpt-4o
     context_tokens: 64000  # OVERRIDE: Model supports 128k but cap for cost
   ```

2. **Hardware Limits**: Reduce context for local models
   ```yaml
   local:
     model: llama3.1:70b
     context_tokens: 32000  # OVERRIDE: Limited by local VRAM
   ```

3. **Performance**: Lower context for faster responses
   ```yaml
   quick:
     model: gpt-4o-mini
     context_tokens: 8000  # OVERRIDE: Faster with smaller context
   ```

### Override Best Practices

- **Always add a comment** explaining why the override is needed
- **Only override when intentional** - don't duplicate model defaults
- **Keep overrides minimal** - let models.yaml be the source of truth

## Backward Compatibility

### Missing providers.yaml

If `providers.yaml` doesn't exist, the system falls back to loading providers from `axe.yaml` (legacy format):

```
Loading configuration...
  ✓ models.yaml (87 models loaded)
  ⚠ providers.yaml not found, checking axe.yaml for legacy providers...
  ✓ axe.yaml (19 agents configured)
  ⚠ Using legacy providers from axe.yaml (consider migrating to providers.yaml)
Configuration validated successfully.
```

**Migration Path**: Move the `providers:` section from `axe.yaml` to a new `providers.yaml` file.

## Ollama Provider (Local LLMs)

The Ollama provider enables running local LLMs for privacy and cost savings:

### Setup

1. **Install Ollama**: https://ollama.ai/
2. **Enable in providers.yaml**:
   ```yaml
   ollama:
     enabled: true  # Change from false to true
   ```
3. **Pull models**:
   ```bash
   ollama pull llama3.1:70b
   ```
4. **Use with agents**:
   ```yaml
   local:
     provider: ollama
     model: llama3.1:70b
   ```

### Benefits

- **Privacy**: Data never leaves your machine
- **Cost**: No API fees
- **Offline**: Works without internet
- **Customization**: Use fine-tuned models

### Limitations

- **Hardware**: Requires significant RAM/VRAM
- **Speed**: Slower than cloud APIs
- **Features**: No vision/audio support (text only)

## Adding New Providers

To add a new provider:

1. **Add to providers.yaml**:
   ```yaml
   newprovider:
     enabled: true
     env_key: NEWPROVIDER_API_KEY
     base_url: https://api.newprovider.com/v1
     models:
       - model-name-1
       - model-name-2
   ```

2. **Add models to models.yaml**:
   ```yaml
   model-name-1:
     context_tokens: 128000
     max_output_tokens: 4000
     input_modes: [text]
     output_modes: [text]
   ```

3. **Add client initialization in core/agent_manager.py** (if needed):
   ```python
   elif name == 'newprovider' and HAS_NEWPROVIDER:
       self.clients[name] = NewProviderClient(api_key=api_key)
   ```

## Configuration Files Location

All three configuration files must be in the same directory:

```
project/
├── models.yaml      # Static model data
├── providers.yaml   # Provider infrastructure
├── axe.yaml         # User configuration
└── axe.py           # Main application
```

The system automatically finds them in:
1. The directory containing `axe.yaml`
2. The current working directory
3. The application directory

## Troubleshooting

### Model Not Found

**Error**: `Provider 'openai' lists model 'gpt-5' but it's not defined in models.yaml`

**Solution**: Add the model to `models.yaml` or remove it from the provider's model list

### Provider Disabled

**Error**: `Agent 'local' uses provider 'ollama' but it is disabled in providers.yaml`

**Solution**: Enable the provider: change `enabled: false` to `enabled: true`

### Model ID Case

**Error**: `Agent 'gpt' uses model 'GPT-4o' but model IDs must be lowercase`

**Solution**: Change to lowercase: `gpt-4o`

### Missing Provider

**Error**: `Agent 'custom' uses provider 'myprovider' but it's not defined in providers.yaml`

**Solution**: Add the provider to `providers.yaml` with proper configuration

## Best Practices

1. **Keep models.yaml clean**: Only add models that are actually available
2. **Document overrides**: Always explain why an override is needed
3. **Use lowercase IDs**: Except for GitHub Models (which uses prefixes)
4. **Enable only what you use**: Disable unused providers
5. **Test after changes**: Run `python3 -c "from core.config import Config; Config()"` to validate
6. **Version control**: Commit all three config files together
7. **Environment variables**: Store API keys in environment, not in config files

## Related Documentation

- **API Providers**: See `docs/api-providers.md` for provider-specific details
- **Agent Skills**: See `docs/features/agent-skills.md` for skills configuration
- **Model Metadata**: See `models/metadata.py` for programmatic access to model data

---

*This configuration architecture was introduced to provide clean separation of concerns and make AXE easier to maintain and extend.*
