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
    'claude-3-opus-20240229': {
        'context_tokens': 200000,
        'max_output_tokens': 4096,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'claude-3-5-sonnet-20240620': {
        'context_tokens': 200000,
        'max_output_tokens': 8192,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'claude-opus-4-5-20251101': {
        'context_tokens': 300000,
        'max_output_tokens': 16384,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # OpenAI models
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
    'openai/gpt-4o': {  # GitHub API variant
        'context_tokens': 128000,
        'max_output_tokens': 16384,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    'openai/gpt-4o-mini': {  # GitHub API variant
        'context_tokens': 128000,
        'max_output_tokens': 16384,
        'input_modes': ['text', 'image'],
        'output_modes': ['text', 'function_calling']
    },
    
    # Meta LLaMA models (HuggingFace)
    'meta-llama/Llama-3.1-70B-Instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    'meta-llama/Llama-3.1-8B-Instruct': {
        'context_tokens': 128000,
        'max_output_tokens': 4096,
        'input_modes': ['text'],
        'output_modes': ['text']
    },
    
    # xAI Grok models
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
}

# Default metadata for unknown models
DEFAULT_METADATA = {
    'context_tokens': 8000,
    'max_output_tokens': 2048,
    'input_modes': ['text'],
    'output_modes': ['text']
}


def get_model_info(model_name: str) -> Dict:
    """
    Get metadata for a specific model.
    
    Args:
        model_name: Name of the model (e.g., 'claude-3-opus-20240229')
    
    Returns:
        Dictionary with model metadata, or default metadata if model not found
    """
    return MODEL_METADATA.get(model_name, DEFAULT_METADATA.copy())


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
