"""
Model metadata for AXE - specifications for different LLM models. 
Includes context window size, max output tokens, and supported modes. 
"""

from typing import Dict, List

# Model metadata structure:
# - context_tokens: Maximum input context window size in tokens
# - max_output_tokens: Maximum output tokens per generation
# - input_modes: List of supported input modes (text, image, etc.)
# - output_modes: List of supported output modes (text, function_calling, etc.)

MODEL_METADATA = {
    # Anthropic Claude models
    'claude-3-5-sonnet-20241022': {
        'context_tokens': 200000,
        'max_output_tokens': 8192,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'claude-3-opus-20240229':  {
        'context_tokens':  200000,
        'max_output_tokens': 4096,
        'input_modes':  ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'claude-3-5-sonnet-20240620': {
        'context_tokens': 200000,
        'max_output_tokens': 8192,
        'input_modes': ['text', 'image'],
        'output_modes':  ['text', 'function_calling']
    },
    'claude-opus-4-5-20251101': {
        'context_tokens': 300000,
        'max_output_tokens':  16384,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'claude-sonnet-4-20250514': {
        'context_tokens': 200000,
        'max_output_tokens': 8192,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # OpenAI models (direct API)
    'gpt-4o': {
        'context_tokens': 128000,
        'max_output_tokens': 16384,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'gpt-4-turbo': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'gpt-3.5-turbo': {
        'context_tokens': 16385,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'gpt-5. 2-2025-12-11': {
        'context_tokens': 256000,
        'max_output_tokens': 32768,
        'input_modes': ['text', 'image', 'audio'],
        'output_modes': ['text', 'function_calling']
    },
    
    # ==============================================================================
    # GitHub Models API - OpenAI GPT-4 series
    # ==============================================================================
    'openai/gpt-4o':  {
        'context_tokens': 131072,
        'max_output_tokens': 16384,
        'input_modes': ['text', 'image', 'audio'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-4o-mini': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image', 'audio'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-4.1': {
        'context_tokens': 1048576,  # 1M tokens
        'max_output_tokens': 32768,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-4.1-mini': {
        'context_tokens': 1048576,  # 1M tokens
        'max_output_tokens': 32768,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-4. 1-nano': {
        'context_tokens': 1048576,  # 1M tokens
        'max_output_tokens': 32768,
        'input_modes':  ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # GitHub Models API - OpenAI GPT-5 series
    'openai/gpt-5':  {
        'context_tokens':  200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-5-chat': {
        'context_tokens': 200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-5-mini': {
        'context_tokens': 200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-5-nano': {
        'context_tokens': 200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # GitHub Models API - OpenAI o-series (reasoning models)
    'openai/o1': {
        'context_tokens': 200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/o1-mini': {
        'context_tokens': 128000,
        'max_output_tokens': 65536,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/o1-preview': {
        'context_tokens': 128000,
        'max_output_tokens': 32768,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'openai/o3':  {
        'context_tokens':  200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/o3-mini': {
        'context_tokens': 200000,
        'max_output_tokens':  100000,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/o4-mini': {
        'context_tokens': 200000,
        'max_output_tokens': 100000,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # GitHub Models API - OpenAI Embeddings
    'openai/text-embedding-3-large': {
        'context_tokens': 8191,
        'max_output_tokens': 3072,  # Embedding dimensions
        'input_modes': ['text'],
        'output_modes': ['embeddings']
    },
    'openai/text-embedding-3-small': {
        'context_tokens': 8191,
        'max_output_tokens':  1536,  # Embedding dimensions
        'input_modes': ['text'],
        'output_modes': ['embeddings']
    },
    
    # ==============================================================================
    # GitHub Models API - Meta Llama series
    # ==============================================================================
    'meta/llama-3.2-11b-vision-instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image', 'audio'],
        'output_modes': ['text']
    },
    'meta/llama-3.2-90b-vision-instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image', 'audio'],
        'output_modes': ['text']
    },
    'meta/llama-3.3-70b-instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'meta/llama-4-maverick-17b-128e-instruct-fp8': {
        'context_tokens': 1000000,  # 1M tokens! 
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'meta/llama-4-scout-17b-16e-instruct':  {
        'context_tokens':  10000000,  # 10M tokens!
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'meta/meta-llama-3.1-405b-instruct': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text']
    },
    'meta/meta-llama-3.1-8b-instruct': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    
    # ==============================================================================
    # GitHub Models API - Mistral AI series
    # ==============================================================================
    'mistral-ai/codestral-2501':  {
        'context_tokens':  256000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'mistral-ai/ministral-3b': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text', 'function_calling']
    },
    'mistral-ai/mistral-medium-2505': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'mistral-ai/mistral-small-2503': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # ==============================================================================
    # GitHub Models API - DeepSeek series
    # ==============================================================================
    'deepseek/deepseek-r1': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text', 'function_calling']
    },
    'deepseek/deepseek-r1-0528': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'deepseek/deepseek-v3-0324': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    
    # ==============================================================================
    # GitHub Models API - Microsoft Phi series
    # ==============================================================================
    'microsoft/phi-4': {
        'context_tokens': 16384,
        'max_output_tokens': 16384,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'microsoft/phi-4-mini-instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text']
    },
    'microsoft/phi-4-mini-reasoning': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'microsoft/phi-4-multimodal-instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['audio', 'image', 'text'],
        'output_modes': ['text']
    },
    'microsoft/phi-4-reasoning': {
        'context_tokens': 32768,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text']
    },
    'microsoft/mai-ds-r1': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    
    # ==============================================================================
    # GitHub Models API - Cohere series
    # ==============================================================================
    'cohere/cohere-command-a':  {
        'context_tokens':  131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text']
    },
    'cohere/cohere-command-r-08-2024': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'cohere/cohere-command-r-plus-08-2024': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text', 'function_calling']
    },
    
    # ==============================================================================
    # GitHub Models API - AI21 Labs
    # ==============================================================================
    'ai21-labs/ai21-jamba-1.5-large': {
        'context_tokens': 262144,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    
    # ==============================================================================
    # GitHub Models API - xAI Grok series
    # ==============================================================================
    'xai/grok-3':  {
        'context_tokens':  131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text']
    },
    'xai/grok-3-mini':  {
        'context_tokens':  131072,
        'max_output_tokens': 4096,
        'input_modes':  ['text'],
        'output_modes': ['text']
    },
    
    # ==============================================================================
    # Meta LLaMA models (HuggingFace direct API)
    # ==============================================================================
    'meta-llama/Llama-3.1-70B-Instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes':  ['text']
    },
    'meta-llama/Llama-3.1-8B-Instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'meta-llama/Llama-3.3-70B-Instruct':  {
        'context_tokens':  128000,
        'max_output_tokens': 4096,
        'input_modes':  ['text'],
        'output_modes': ['text']
    },
    
    # ==============================================================================
    # xAI Grok models (direct API)
    # ==============================================================================
    'grok-beta': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'grok-2': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'grok-4-1-fast': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text', 'function_calling']
    },
    'grok-code-fast': {
        'context_tokens': 131072,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'grok-2-vision': {
        'context_tokens': 32768,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text']
    },
    'grok-2-image': {
        'context_tokens': 4096,
        'max_output_tokens': 1,  # Generates images
        'input_modes': ['text'],
        'output_modes': ['image']
    },
    
    # ==============================================================================
    # Dashscope/Qwen models
    # ==============================================================================
    'Qwen/Qwen3-VL-235B-A22B-Thinking-25700':  {
        'context_tokens':  128000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text']
    },
    'Qwen/Qwen3-Coder-480B-A35B-Instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'Qwen/Qwen3-VL-235B-A22B-Thinking':  {
        'context_tokens':  128000,
        'max_output_tokens': 4096,
        'input_modes':  ['text', 'image'],
        'output_modes': ['text']
    },
    'Qwen/Qwen-Image':  {
        'context_tokens':  4096,
        'max_output_tokens': 1,  # Generates images
        'input_modes': ['text'],
        'output_modes': ['image']
    },
    'Qwen/Qwen-Image-Edit-2511': {
        'context_tokens': 4096,
        'max_output_tokens': 1,  # Edits images
        'input_modes': ['text', 'image'],
        'output_modes': ['image']
    },
    
    # ==============================================================================
    # DeepSeek models (direct API)
    # ==============================================================================
    'deepseek-ai/DeepSeek-V3.2':  {
        'context_tokens':  128000,
        'max_output_tokens': 4096,
        'input_modes':  ['text'],
        'output_modes': ['text', 'function_calling']
    },
}

# Default metadata for unknown models
DEFAULT_METADATA = {
    'context_tokens': 8000,
    'max_output_tokens': 2048,
    'input_modes': ['text'],
    'output_modes': ['text']
}


def get_model_info(model_name:  str) -> Dict:
    """
    Get metadata for a specific model.
    
    Args:
        model_name: Name of the model (e.g., 'claude-3-opus-20240229')
    
    Returns:
        Dictionary with model metadata, or default metadata if model not found
    """
    return MODEL_METADATA.get(model_name, DEFAULT_METADATA. copy())


def format_token_count(tokens: int) -> str:
    """
    Format token count for display (e.g., 200000 -> "200,000").
    
    Args:
        tokens: Number of tokens
    
    Returns:
        Formatted string with commas
    """
    return f"{tokens:,}"


def format_input_modes(modes: List[str]) -> str:
    """
    Format input modes for display. 
    
    Args:
        modes: List of input modes (e.g., ['text', 'image'])
    
    Returns:
        Formatted string (e.g., "text, image")
    """
    return ', '.join(modes)


def format_output_modes(modes: List[str]) -> str:
    """
    Format output modes for display.
    
    Args:
        modes: List of output modes (e.g., ['text', 'function_calling'])
    
    Returns:
        Formatted string (e.g., "text, function_calling")
    """
    return ', '.join(modes)