"""
Token usage statistics and cost estimation for AXE.
Pricing data for different AI model providers.
"""

from typing import Dict, Tuple, Optional

# Pricing per 1M tokens (input, output)
# Prices as of January 2026
MODEL_PRICING = {
    # Anthropic Claude models (per 1M tokens)
    'claude-opus-4-5-20251101': (15.00, 75.00),  # Claude Opus 4.5
    'claude-sonnet-4-20250514': (3.00, 15.00),   # Claude Sonnet 4
    'claude-3-5-sonnet-20241022': (3.00, 15.00), # Claude 3.5 Sonnet
    'claude-3-opus-20240229': (15.00, 75.00),    # Claude 3 Opus
    'claude-3-5-sonnet-20240620': (3.00, 15.00), # Claude 3.5 Sonnet
    
    # OpenAI models (per 1M tokens)
    'gpt-5.2-2025-12-11': (5.00, 15.00),         # GPT-5.2
    'gpt-4o': (2.50, 10.00),                      # GPT-4o
    'gpt-4-turbo': (10.00, 30.00),                # GPT-4 Turbo
    'gpt-3.5-turbo': (0.50, 1.50),                # GPT-3.5 Turbo
    
    # xAI Grok models (per 1M tokens)
    'grok-4-1-fast': (5.00, 10.00),               # Grok 4.1 Fast (estimated)
    'grok-code-fast': (5.00, 10.00),              # Grok Code Fast
    'grok-2': (5.00, 10.00),                      # Grok 2
    'grok-2-vision': (5.00, 10.00),               # Grok 2 Vision
    'grok-beta': (5.00, 10.00),                   # Grok Beta
    
    # HuggingFace models (free inference API)
    'meta-llama/Llama-3.3-70B-Instruct': (0.00, 0.00),
    'meta-llama/Llama-3.1-70B-Instruct': (0.00, 0.00),
    'meta-llama/Llama-3.1-8B-Instruct': (0.00, 0.00),
    
    # GitHub Copilot models (included with Copilot subscription)
    'openai/gpt-4o': (0.00, 0.00),  # Free with GitHub Copilot
    'openai/gpt-4o-mini': (0.00, 0.00),  # Free with GitHub Copilot
    
    # DeepSeek models (per 1M tokens)
    'deepseek-ai/DeepSeek-V3.2': (0.27, 1.10),  # Very competitive pricing
    
    # Qwen/Dashscope models (per 1M tokens, estimated)
    'Qwen/Qwen3-VL-235B-A22B-Thinking-25700': (2.00, 6.00),
    'Qwen/Qwen3-Coder-480B-A35B-Instruct': (2.00, 6.00),
    'Qwen/Qwen3-VL-235B-A22B-Thinking': (2.00, 6.00),
}

# Default pricing for unknown models (per 1M tokens)
DEFAULT_PRICING = (5.00, 15.00)


def get_model_pricing(model_name: str) -> Tuple[float, float]:
    """
    Get pricing for a model.
    
    Args:
        model_name: Name of the model
    
    Returns:
        Tuple of (input_price_per_1m, output_price_per_1m) in USD
    """
    return MODEL_PRICING.get(model_name, DEFAULT_PRICING)


def estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost for token usage.
    
    Args:
        model_name: Name of the model
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Estimated cost in USD
    """
    input_price, output_price = get_model_pricing(model_name)
    
    # Calculate cost (prices are per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    
    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """
    Format cost for display.
    
    Args:
        cost: Cost in USD
    
    Returns:
        Formatted string (e.g., "$0.23" or "$2.45")
    """
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1.00:
        return f"${cost:.2f}"
    else:
        return f"${cost:.2f}"


class TokenStats:
    """Track and calculate token usage statistics."""
    
    def __init__(self):
        """Initialize token statistics tracker."""
        self.agent_stats = {}  # {agent_name: {'input': N, 'output': N, 'messages': N, 'model': str}}
    
    def add_usage(self, agent_name: str, model: str, input_tokens: int, output_tokens: int) -> None:
        """
        Record token usage for an agent.
        
        Args:
            agent_name: Name of the agent
            model: Model name used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {
                'input': 0,
                'output': 0,
                'messages': 0,
                'model': model
            }
        
        self.agent_stats[agent_name]['input'] += input_tokens
        self.agent_stats[agent_name]['output'] += output_tokens
        self.agent_stats[agent_name]['messages'] += 1
        self.agent_stats[agent_name]['model'] = model  # Update to latest model used
    
    def get_agent_stats(self, agent_name: str) -> Optional[Dict]:
        """
        Get statistics for a specific agent.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Dictionary with stats, or None if agent not found
        """
        return self.agent_stats.get(agent_name)
    
    def get_total_stats(self) -> Dict:
        """
        Get total statistics across all agents.
        
        Returns:
            Dictionary with total input, output, messages, and cost
        """
        total_input = sum(stats['input'] for stats in self.agent_stats.values())
        total_output = sum(stats['output'] for stats in self.agent_stats.values())
        total_messages = sum(stats['messages'] for stats in self.agent_stats.values())
        
        # Calculate total cost
        total_cost = 0.0
        for agent_name, stats in self.agent_stats.items():
            cost = estimate_cost(stats['model'], stats['input'], stats['output'])
            total_cost += cost
        
        return {
            'input': total_input,
            'output': total_output,
            'total': total_input + total_output,
            'messages': total_messages,
            'cost': total_cost
        }
    
    def get_all_stats(self) -> Dict:
        """
        Get statistics for all agents.
        
        Returns:
            Dictionary mapping agent_name to stats with cost
        """
        result = {}
        for agent_name, stats in self.agent_stats.items():
            cost = estimate_cost(stats['model'], stats['input'], stats['output'])
            result[agent_name] = {
                **stats,
                'total': stats['input'] + stats['output'],
                'cost': cost
            }
        return result
