#!/usr/bin/env python3
"""
Example demonstrating Anthropic-specific features in AXE.
This script shows how to use:
- Prompt caching for token savings
- Extended thinking for complex reasoning
- Token counting for precise estimates
- Cache statistics tracking
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.config import Config
from core.agent_manager import AgentManager
from utils.token_stats import TokenStats
from models.metadata import (
    supports_extended_thinking,
    get_extended_thinking_budget,
    is_anthropic_model
)
def example_prompt_caching():
    """Example 1: Prompt Caching"""
    print("=" * 70)
    print("EXAMPLE 1: PROMPT CACHING")
    print("=" * 70)
    print()
    print("Scenario: Analyzing multiple functions in the same codebase")
    print("- First call: System prompt and context are cached")
    print("- Subsequent calls: Only new content is processed")
    print()
    stats = TokenStats()
    model = 'claude-opus-4-5-20251101'
    # Simulate three calls with caching
    stats.add_usage('coder', model, 2000, 800, cache_creation_tokens=10000, cache_read_tokens=0)
    print("Call 1: Cache created: 10,000 tokens, New: 2,000 tokens")
    stats.add_usage('coder', model, 1500, 750, cache_creation_tokens=0, cache_read_tokens=9500)
    print("Call 2: Cache hit: 9,500 tokens, New: 1,500 tokens")
    stats.add_usage('coder', model, 1800, 800, cache_creation_tokens=0, cache_read_tokens=9500)
    print("Call 3: Cache hit: 9,500 tokens, New: 1,800 tokens")
    print()
    agent_stats = stats.get_agent_stats('coder')
    total_cached = agent_stats['cache']['read']
    total_input = agent_stats['input'] + agent_stats['cache']['creation']
    savings_pct = (total_cached / (total_input + total_cached)) * 100
    print(f"Token savings: {savings_pct:.1f}%")
    print()
def example_extended_thinking():
    """Example 2: Extended Thinking"""
    print("=" * 70)
    print("EXAMPLE 2: EXTENDED THINKING")
    print("=" * 70)
    print()
    models = [
        ('claude-opus-4-5-20251101', 'Flagship, highest reasoning'),
        ('claude-sonnet-4-5-20250929', 'Balanced performance'),
        ('claude-haiku-4-5-20251001', 'Fast and efficient'),
    ]
    for model, desc in models:
        if supports_extended_thinking(model):
            budget = get_extended_thinking_budget(model)
            print(f"{model}: {desc}")
            print(f"  Thinking budget: {budget:,} tokens")
        print()
def main():
    """Run examples."""
    print()
    print("ANTHROPIC FEATURES EXAMPLES")
    print()
    example_prompt_caching()
    example_extended_thinking()
    print("For more info: docs/ANTHROPIC_FEATURES.md")
    print()
if __name__ == '__main__':
    main()