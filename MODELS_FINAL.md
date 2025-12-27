# AXE Multi-Agent System - Model Configuration Reference

> **Version**: 1.0  
> **Last Updated**: December 2025  

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Anthropic (Claude)](#anthropic-claude)
3. [HuggingFace (Llama)](#huggingface-llama)
4. [OpenAI (GPT)](#openai-gpt)
5. [xAI (Grok)](#xai-grok)
6. [GitHub Models](#github-models)
7. [Model Capabilities Matrix](#model-capabilities-matrix)
8. [Usage Examples](#usage-examples)

---

## Quick Start

### Environment Setup
```bash
# Load all API keys at once
source /path/to/models_env.sh

# Or set individually
export ANTHROPIC_API_KEY='your-key'
export HUGGINGFACE_API_KEY='your-key'
export OPENAI_API_KEY='your-key'
export XAI_API_KEY='your-key'
export GITHUB_TOKEN='your-key'
```

### Test Connection
```python
from axe import test_model_connection
test_model_connection("llama")  # Test HuggingFace Llama
test_model_connection("claude") # Test Anthropic Claude
```

---

## Anthropic (Claude)

### Configuration
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-...'
```

### Latest Models
| Model | Type | Context | Best For |
|-------|------|---------|----------|
| `claude-opus-4-5` | General | 200K tokens | Complex reasoning, coding, analysis |

### Usage
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

### Notes
- Highest quality reasoning
- Best for supervisor/coordinator roles
- Credit-based billing

---

## HuggingFace (Llama)

### Configuration
```bash
export HUGGINGFACE_API_KEY="hf_..."

# Or using HuggingFace CLI
hf auth login
```

### Latest Models

| Model | Type | Context | Best For |
|-------|------|---------|----------|
| `meta-llama/Llama-4-Maverick-17B-128E-Instruct` | General/Coding/Vision | Large | Multi-modal tasks |
| `meta-llama/Llama-3.1-405B-Instruct` | General/Coding | Large | High-quality reasoning |
| `meta-llama/Llama-4-Scout-17B-16E-Instruct` | Vision | Large | Image understanding |

### Usage - OpenAI-Compatible API
```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HUGGINGFACE_API_KEY"],
)

completion = client.chat.completions.create(
    model="meta-llama/Llama-3.1-405B-Instruct:sambanova",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
)
print(completion.choices[0].message)
```

### Usage - Transformers (Local)
```python
from transformers import AutoProcessor, AutoModelForMultimodalLM

processor = AutoProcessor.from_pretrained(
    "meta-llama/Llama-4-Scout-17B-16E-Instruct"
)
model = AutoModelForMultimodalLM.from_pretrained(
    "meta-llama/Llama-4-Scout-17B-16E-Instruct"
)
```

### Notes
- **WORKING** - Verified with HuggingFace Inference API
- Good for worker agents
- Free tier available with quotas

---

## OpenAI (GPT)

### Configuration
```bash
export OPENAI_API_KEY="sk-proj-..."
```

### Latest Models
| Model | Type | Context | Best For |
|-------|------|---------|----------|
| `gpt-5.2-2025-12-11` | General | Large | Latest capabilities |

### Usage
```python
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.chat.completions.create(
    model="gpt-5.2-2025-12-11",
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

### Notes
- Credit-based billing
- Extensive function calling support

---

## xAI (Grok)

### Configuration
```bash
export XAI_API_KEY="xai-..."
```

### Latest Models

| Model | Input | Output | Context | Rate Limit | Capabilities |
|-------|-------|--------|---------|------------|--------------|
| `grok-4-1-fast` | Text | Text | 2M tokens | 4M tokens/min | Function calling, structured outputs |
| `grok-code-fast` | Text | Text | 256K tokens | 2M tokens/min | Function calling, structured outputs |
| `grok-2-vision` | Image+Text | Text | 32K tokens | - | Function calling, structured outputs |
| `grok-2-image` | Text | Image | - | - | Image generation |

### Usage - Text Generation
```python
from xai_sdk import Client

client = Client(api_key=os.environ["XAI_API_KEY"])

# Text completion
response = client.chat.completions.create(
    model="grok-4-1-fast",
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

### Usage - Image Generation
```python
from xai_sdk import Client

client = Client(api_key=os.environ["XAI_API_KEY"])

response = client.image.sample(
    model="grok-2-image",
    prompt="A cat in a tree",
    image_format="url"
)
print(response.url)
```

### Notes
- Very generous rate limits
- Good for high-throughput tasks
- Premium+ tier recommended
- Docs: https://docs.x.ai/docs/models

---

## GitHub Models

### Configuration
```bash
export GITHUB_TOKEN="github_pat_..."
```

### Available Models
Same top models as Anthropic and OpenAI are available through GitHub Copilot:
- `claude-opus-4-5` (Anthropic)
- `gpt-5.1` (OpenAI)

### Usage
```python
# Via GitHub Copilot API (enterprise)
# Configuration depends on your GitHub setup
```

### Notes
- **WORKING** - Verified with GitHub Copilot models
- Requires GitHub Copilot subscription
- Per-seat or usage-based billing

---

## Model Capabilities Matrix

| Provider | Model | Text | Vision | Code | Function Calling | Context | Status |
|----------|-------|------|--------|------|------------------|---------|--------|
| Anthropic | claude-opus-4-5 | ✅ | ✅ | ✅ | ✅ | 200K | 🔴 No credits |
| HuggingFace | Llama-4-Maverick-17B | ✅ | ✅ | ✅ | ✅ | Large | ✅ Working |
| HuggingFace | Llama-3.1-405B | ✅ | ❌ | ✅ | ✅ | Large | ✅ Working |
| OpenAI | gpt-5.2 | ✅ | ✅ | ✅ | ✅ | Large | 🔴 No credits |
| xAI | grok-4-1-fast | ✅ | ❌ | ✅ | ✅ | 2M | 🔴 No credits |
| xAI | grok-code-fast | ✅ | ❌ | ✅ | ✅ | 256K | 🔴 No credits |
| xAI | grok-2-vision | ✅ | ✅ | ✅ | ✅ | 32K | 🔴 No credits |
| GitHub | claude-opus-4-5 | ✅ | ✅ | ✅ | ✅ | 200K | ✅ Working |
| GitHub | gpt-5.1 | ✅ | ✅ | ✅ | ✅ | Large | ✅ Working |

---

## Usage Examples

### Multi-Agent Collaboration
```bash
# Start a collaboration session with multiple models
python3 axe.py \
    --collab llama,grok \
    --workspace ../playground \
    --time 30 \
    --task "Analyze the wadextract code in doom/wadextract"
```

### Model Communication Example
```
@llama1: I found an issue in the sprite rendering code. @grok2, can you verify?
@grok2: Checking now... confirmed. The HERETIC sprite enum values are offset.
@boss: Good catch team. @llama1 please fix and @grok2 write tests.
```

### Test Projects for Multi-Agent Work
- `doom/wadextract` - WAD file extraction utilities
- `doom/dmspec16.txt` - DOOM specifications document
- `ChaosForgeHash` - Hash utilities
- `brain3d_v2` - 3D brain visualization

### Supervisor Role Assignment
```bash
# The model that starts axe.py becomes @boss
python3 axe.py --task "Your task"
# This model is now @boss, workers will be @llama1, @grok1, etc.
```

---

## Troubleshooting

### No Credits Error
If you see "no credits" errors for Anthropic, OpenAI, or Grok:
- Use HuggingFace Llama models (free tier available)
- Use GitHub Copilot models (included with subscription)

### Rate Limiting
```python
import time

def call_with_retry(func, *args, max_retries=3, **kwargs):
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except RateLimitError:
            time.sleep(2 ** i)  # Exponential backoff
    raise Exception("Max retries exceeded")
```

---

