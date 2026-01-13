"""
Model metadata for AXE - specifications for different LLM models. 
Includes context window size, max output tokens, and supported modes. 

This module loads model metadata from models.yaml at the project root.
"""

import os
import yaml
from typing import Dict, List

# Load model metadata from models.yaml
_models_yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.yaml')

def _load_models_yaml():
    """Load model metadata from models.yaml"""
    try:
        with open(_models_yaml_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: models.yaml not found at {_models_yaml_path}. Using empty configuration.")
        return {}
    except yaml.YAMLError as e:
        print(f"Warning: Failed to parse models.yaml: {e}. Using empty configuration.")
        return {}

_config = _load_models_yaml()
MODEL_METADATA = _config.get('models', {})
DEFAULT_METADATA = _config.get('default', {
    'context_tokens': 8000,
    'max_output_tokens': 4000,
    'input_modes': ['text'],
    'output_modes': ['text']
})
USE_MAX_COMPLETION_TOKENS = set(_config.get('use_max_completion_tokens', []))


def uses_max_completion_tokens(model_name: str) -> bool:
    """
    Check if a model requires max_completion_tokens parameter.
    
    Uses prefix matching to support model families (e.g., "gpt-5" matches "gpt-5.2").
    This is intentional to cover versioned models within the same family.
    
    Args:
        model_name: Name of the model to check
    
    Returns:
        True if model requires max_completion_tokens, False otherwise
    """
    for prefix in USE_MAX_COMPLETION_TOKENS:
        if model_name.startswith(prefix):
            return True
    return False


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


def get_max_output_tokens(model_name: str, default: int = 4000) -> int:
    """
    Get the max output tokens for a model.
    
    Args:
        model_name: Name of the model
        default: Default value if model not found (safe default: 4000)
    
    Returns:
        Max output tokens for the model
    """
    model_info = get_model_info(model_name)
    return model_info.get('max_output_tokens', default)


def supports_extended_thinking(model_name: str) -> bool:
    """
    Check if a model supports extended thinking.
    
    Args:
        model_name: Name of the model
    
    Returns:
        True if model supports extended thinking
    """
    model_info = get_model_info(model_name)
    return 'extended_thinking' in model_info and model_info['extended_thinking'].get('enabled', False)


def get_extended_thinking_budget(model_name: str) -> int:
    """
    Get the extended thinking token budget for a model.
    
    Args:
        model_name: Name of the model
    
    Returns:
        Token budget for extended thinking, or 0 if not supported
    """
    model_info = get_model_info(model_name)
    if 'extended_thinking' in model_info:
        return model_info['extended_thinking'].get('budget_tokens', 0)
    return 0


def is_anthropic_model(model_name: str) -> bool:
    """
    Check if a model is an Anthropic Claude model.
    
    Args:
        model_name: Name of the model
    
    Returns:
        True if model is from Anthropic
    """
    return model_name.startswith('claude-')


def get_anthropic_config() -> Dict:
    """
    Get Anthropic-specific configuration from models.yaml.
    
    Returns:
        Dictionary with Anthropic configuration
    """
    return _config.get('anthropic', {})