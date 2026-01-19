# AXE API Provider Documentation

Comprehensive documentation for all supported API providers in AXE (Agent eXecution Engine).

## Table of Contents

1. [Anthropic (Claude)](#anthropic-claude)
2. [OpenAI (GPT)](#openai-gpt)
3. [HuggingFace (Llama)](#huggingface-llama)
4. [xAI (Grok)](#xai-grok)
5. [GitHub Models](#github-models)

---

## Anthropic (Claude)

### Top Models

| Model | Context Window | Input Price | Output Price | Best For |
|-------|---------------|-------------|--------------|----------|
| **claude-3-5-sonnet-20241022** | 200K tokens | $3/M | $15/M | Coding, agents, vision, artifacts |
| **claude-3-opus-20240229** | 200K tokens | $15/M | $75/M | Deep reasoning, research |
| **claude-3-5-haiku-20241022** | 200K tokens | $1/M | $5/M | Fast chat, bulk tasks |

### Features

- **Vision**: Best-in-class image, graph, and chart understanding
- **Coding**: Superior code writing, bug tracking, refactoring
- **Agentic**: Multi-step workflows, tool use
- **200K context**: ~150,000 words or 500 pages

### Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### cURL Example

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096,
    "system": "You are a helpful coding assistant.",
    "messages": [
      {"role": "user", "content": "Write a C function to parse WAD files"}
    ]
  }'
```

### Python Example

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    system="You are a helpful coding assistant.",
    messages=[{"role": "user", "content": "Analyze this binary..."}]
)
print(response.content[0].text)
```

### Documentation

- Official: https://docs.anthropic.com/
- Models: https://docs.anthropic.com/en/docs/about-claude/models

---

## OpenAI (GPT)

### Top Models

| Model | Context Window | Input Price | Output Price | Best For |
|-------|---------------|-------------|--------------|----------|
| **gpt-4o** | 128K tokens | $2.50/M | $10/M | Multimodal, fast, cost-effective |
| **gpt-4-turbo** | 128K tokens | $10/M | $30/M | Long documents, text focus |
| **gpt-4o-mini** | 128K tokens | $0.15/M | $0.60/M | Simple tasks, high volume |

### Features

- **Multimodal**: Text, images, audio (GPT-4o)
- **Speed**: GPT-4o is 2x faster than GPT-4-turbo
- **Vision**: High-performance image understanding
- **128K context**: ~96,000 words or 300 pages

### Environment Variable

```bash
export OPENAI_API_KEY="sk-..."
```

### cURL Example

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "max_tokens": 4096,
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain x86 assembly calling conventions"}
    ]
  }'
```

### Python Example

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=4096,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Analyze this code..."}
    ]
)
print(response.choices[0].message.content)
```

### Vision Example (Images)

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "Describe this image"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ]
  }'
```

### Documentation

- Official: https://platform.openai.com/docs
- Models: https://platform.openai.com/docs/models

---

## HuggingFace (Llama)

### Top Models

| Model | Context Window | Pricing | Best For |
|-------|---------------|---------|----------|
| **meta-llama/Llama-3.1-70B-Instruct** | 128K tokens | Free tier / Pro | Complex reasoning, coding |
| **meta-llama/Llama-3.1-8B-Instruct** | 128K tokens | Free tier | Fast inference, simple tasks |
| **meta-llama/Llama-3.2-90B-Vision** | 128K tokens | Pro tier | Multimodal (text + images) |

### Features

- **Open Source**: Full model weights available
- **Instruction-tuned**: Optimized for chat and dialogue
- **Free Tier**: Limited compute per month
- **128K context**: Extended context for long documents

### Requirements

1. Create HuggingFace account
2. Request access to Meta Llama models (community license)
3. Generate API token from account settings

### Environment Variable

```bash
export HUGGINGFACE_API_KEY="hf_..."
```

### cURL Example

```bash
curl -X POST https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-70B-Instruct \
  -H "Authorization: Bearer $HUGGINGFACE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "What is the purpose of the DOS interrupt 21h?"
  }'
```

### Chat-style cURL Example

```bash
curl -X POST https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-70B-Instruct/v1/chat/completions \
  -H "Authorization: Bearer $HUGGINGFACE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-70B-Instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain far pointers in 16-bit DOS"}
    ],
    "max_tokens": 1024
  }'
```

### Python Example

```python
from huggingface_hub import InferenceClient

client = InferenceClient(token=os.getenv("HUGGINGFACE_API_KEY"))
response = client.chat_completion(
    model="meta-llama/Llama-3.1-70B-Instruct",
    max_tokens=4096,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Analyze this assembly..."}
    ]
)
print(response.choices[0].message.content)
```

### Documentation

- Official: https://huggingface.co/docs/api-inference
- Model Card: https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct

---

## xAI (Grok)

### Top Models

| Model | Context Window | Input Price | Output Price | Best For |
|-------|---------------|-------------|--------------|----------|
| **grok-2** | 131K tokens | $2/M | $10/M | General purpose, chat |
| **grok-beta** | 131K tokens | $5/M | $15/M | Advanced reasoning |
| **grok-2-vision** | 131K tokens | $2/M | $10/M | Image understanding |

### Features

- **OpenAI-compatible API**: Easy integration
- **Tool calling**: Function/tool execution support
- **Real-time knowledge**: Access to X (Twitter) data
- **131K context**: ~100,000 words or 300 pages

### Environment Variable

```bash
export XAI_API_KEY="xai-..."
```

### cURL Example

```bash
curl -X POST "https://api.x.ai/v1/chat/completions" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-2",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain DOS memory models"}
    ],
    "max_tokens": 1024
  }'
```

### Python Example (OpenAI SDK)

```python
from openai import OpenAI

# xAI uses OpenAI-compatible API
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)
response = client.chat.completions.create(
    model="grok-2",
    max_tokens=4096,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the best approach to..."}
    ]
)
print(response.choices[0].message.content)
```

### Documentation

- Official: https://docs.x.ai/
- Models: https://docs.x.ai/docs/models

---

## GitHub Models

### Top Models

| Model | Context Window | Cost | Best For |
|-------|---------------|------|----------|
| **openai/gpt-4o** | 128K tokens | Higher | Best accuracy, multimodal |
| **openai/gpt-4o-mini** | 128K tokens | Lower | Fast, cost-effective |
| **openai/gpt-4.1** | 128K tokens | Higher | Latest capabilities |

### Features

- **GitHub Integration**: Native for Copilot workflows
- **Multiple providers**: Access OpenAI, Microsoft, Meta models
- **Token-based**: Uses GitHub PAT for authentication

### Requirements

1. GitHub account with Copilot subscription
2. Personal Access Token with `models:read` permission

### Environment Variable

```bash
export GITHUB_TOKEN="ghp_..."
```

### cURL Example

```bash
curl -X POST "https://models.github.ai/inference" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain GitHub Actions workflows"}
    ]
  }'
```

### Python Example (OpenAI SDK)

```python
from openai import OpenAI

# GitHub Models uses OpenAI-compatible API
client = OpenAI(
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url="https://models.github.ai/inference"
)
response = client.chat.completions.create(
    model="openai/gpt-4o",
    max_tokens=4096,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Review this pull request..."}
    ]
)
print(response.choices[0].message.content)
```

### Documentation

- Official: https://docs.github.com/en/rest/models/inference
- Model Comparison: https://docs.github.com/en/copilot/reference/ai-models/model-comparison

---

## Quick Reference

### Environment Variables Summary

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI (GPT)
export OPENAI_API_KEY="sk-..."

# HuggingFace (Llama)
export HUGGINGFACE_API_KEY="hf_..."

# xAI (Grok)
export XAI_API_KEY="xai-..."

# GitHub Models
export GITHUB_TOKEN="ghp_..."
```

### API Endpoints Summary

| Provider | Endpoint |
|----------|----------|
| Anthropic | `https://api.anthropic.com/v1/messages` |
| OpenAI | `https://api.openai.com/v1/chat/completions` |
| HuggingFace | `https://api-inference.huggingface.co/models/{model}` |
| xAI | `https://api.x.ai/v1/chat/completions` |
| GitHub | `https://models.github.ai/inference` |

### Model Selection Guide

| Use Case | Recommended Model | Provider |
|----------|------------------|----------|
| Code review & security | claude-3-5-sonnet-20241022 | Anthropic |
| General coding | gpt-4o | OpenAI |
| Open-source preference | Llama-3.1-70B-Instruct | HuggingFace |
| Creative brainstorming | grok-2 | xAI |
| GitHub integration | openai/gpt-4o | GitHub |
| Budget-conscious | gpt-4o-mini | OpenAI |
| Deep reasoning | claude-3-opus-20240229 | Anthropic |
| Fast responses | claude-3-5-haiku-20241022 | Anthropic |

---

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check API key is set correctly
2. **429 Rate Limited**: Reduce request frequency or upgrade plan
3. **Model not found**: Verify exact model name spelling
4. **Context too long**: Reduce input size or use model with larger context

### Testing API Keys

```bash
# Test Anthropic
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'

# Test OpenAI
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'

# Test xAI
curl -s https://api.x.ai/v1/chat/completions \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"grok-2","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```
