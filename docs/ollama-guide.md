# Ollama Integration Guide

## Overview

AXE supports Ollama for local LLM inference without requiring API keys or internet connectivity. All processing happens on your machine with full privacy.

## Installation

```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# The Ollama service should start automatically
# You can also manually start it with:
ollama serve
```

## Recommended Models for Testing/CI

Choose a model based on your available resources:

### Tiny Models (< 1GB) - Best for CI/Minimal Resources
```bash
ollama pull qwen2:0.5b       # ~352MB - fastest, minimal quality
ollama pull tinyllama        # ~637MB - good for basic tasks
```

### Small Models (1-2GB) - Good Balance
```bash
ollama pull llama3.2:1b      # ~1.3GB - better quality
ollama pull phi              # ~1.6GB - Microsoft Phi model
ollama pull llama3.2:3b      # ~2GB - recommended for testing
```

### Medium Models (4-8GB) - Production Quality
```bash
ollama pull llama3.1:8b      # ~4.7GB - good performance
ollama pull mistral:7b       # ~4.1GB - efficient
```

### Large Models (> 30GB) - Best Quality
```bash
ollama pull llama3.1:70b     # ~40GB - requires significant resources
ollama pull codellama:34b    # ~20GB - specialized for coding
```

## Configuration

Ollama is pre-configured in AXE and requires **no API key**:

**providers.yaml:**
```yaml
ollama:
  enabled: true
  requires_auth: false  # No API key needed
  env_key: null
  base_url: http://localhost:11434/v1
```

**axe.yaml:**
```yaml
agents:
  local:
    alias: [lo, local, ollama]
    provider: ollama
    model: llama3.2:3b  # Change to smaller model if needed
    role: Local private coding agent
```

## Usage

```bash
# Interactive mode
./axe.py
@ollama Hello, are you working?

# Command line mode
./axe.py -c "@ollama explain this code"

# Using alias
./axe.py -c "@local write a hello world in Python"
```

## Troubleshooting

### Model Too Large?
If `llama3.2:3b` is too large for your system:

1. **Use a smaller model:**
   ```bash
   ollama pull qwen2:0.5b
   ```

2. **Update axe.yaml:**
   ```yaml
   agents:
     local:
       model: qwen2:0.5b  # Change from llama3.2:3b
   ```

### Server Not Running?
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start manually if needed
ollama serve
```

### Performance Issues?
- Use smaller models (qwen2:0.5b, tinyllama)
- Close other applications to free RAM
- Consider using quantized models (Q4, Q5 variants)
- Monitor with: `ollama ps`

## Model Comparison

| Model | Size | RAM Needed | Speed | Quality | Use Case |
|-------|------|-----------|-------|---------|----------|
| qwen2:0.5b | 352MB | 1GB | Fastest | Basic | CI/Testing |
| tinyllama | 637MB | 2GB | Very Fast | Good | Quick tests |
| llama3.2:1b | 1.3GB | 3GB | Fast | Good | Testing |
| phi | 1.6GB | 3GB | Fast | Good | Testing |
| llama3.2:3b | 2GB | 4GB | Fast | Better | Recommended |
| llama3.1:8b | 4.7GB | 8GB | Medium | Great | Production |
| mistral:7b | 4.1GB | 8GB | Medium | Great | Production |
| llama3.1:70b | 40GB | 64GB | Slow | Best | High-end |

## Privacy & Security

✅ **Advantages:**
- No data sent to external servers
- Works completely offline
- No API costs
- Full privacy and control

⚠️ **Limitations:**
- Requires local compute resources
- Model quality depends on size
- No built-in content filtering
- Limited by local hardware

## Testing

Run the authentication tests:
```bash
python3 tests/test_ollama_auth.py
```

This will:
- Start Ollama server automatically
- Test initialization without API keys
- Verify all edge cases
- Clean up server when done

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Model Library](https://ollama.com/library)
- [AXE Documentation](../README.md)
