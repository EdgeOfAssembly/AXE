"""
Agent Manager for AXE.

Manages agent connections and API calls to various LLM providers.
"""

import os
from typing import Optional, List, Dict, Any, Callable

from .config import Config
from models.metadata import (
    get_model_info, uses_max_completion_tokens, get_max_output_tokens,
    supports_extended_thinking, get_extended_thinking_budget, 
    is_anthropic_model, get_anthropic_config
)
from utils.formatting import Colors, c

# Optional imports - gracefully handle missing dependencies
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from huggingface_hub import InferenceClient
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False


class AgentManager:
    """Manages agent connections and API calls."""

    def __init__(self, config: Config):
        self.config = config
        self.clients: Dict[str, Any] = {}
        self.anthropic_features = None  # Will be initialized if Anthropic is available
        self._init_clients()

    def _uses_max_completion_tokens(self, model: str) -> bool:
        """Check if a model requires max_completion_tokens parameter."""
        return uses_max_completion_tokens(model)

    def _init_clients(self) -> None:
        """Initialize API clients for enabled providers."""
        providers = self.config.get('providers', default={})

        for name, prov_config in providers.items():
            if not prov_config.get('enabled', True):
                continue

            env_key = prov_config.get('env_key', '')
            api_key = os.getenv(env_key)

            if not api_key:
                continue

            try:
                if name == 'anthropic' and HAS_ANTHROPIC:
                    self.clients[name] = Anthropic(api_key=api_key)
                    # Initialize Anthropic features
                    from core.anthropic_features import get_anthropic_features
                    anthropic_config = get_anthropic_config()
                    self.anthropic_features = get_anthropic_features(
                        client=self.clients[name],
                        config=anthropic_config
                    )
                elif name == 'openai' and HAS_OPENAI:
                    self.clients[name] = OpenAI(api_key=api_key)
                elif name == 'huggingface' and HAS_HUGGINGFACE:
                    self.clients[name] = InferenceClient(token=api_key)
                elif name == 'xai' and HAS_OPENAI:
                    # xAI uses OpenAI-compatible API
                    self.clients[name] = OpenAI(
                        api_key=api_key,
                        base_url=prov_config.get('base_url', 'https://api.x.ai/v1')
                    )
                elif name == 'github' and HAS_OPENAI:
                    # GitHub Copilot uses OpenAI-compatible API
                    self.clients[name] = OpenAI(
                        api_key=api_key,
                        base_url=prov_config.get('base_url', 'https://models.github.ai/inference')
                    )
            except Exception as e:
                print(c(f"Failed to init {name}: {e}", Colors.YELLOW))

    def resolve_agent(self, name: str) -> Optional[dict]:
        """Resolve agent name or alias to agent config."""
        agents = self.config.get('agents', default={})

        # Direct match
        if name in agents:
            return {**agents[name], 'name': name}

        # Alias match
        for agent_name, agent_config in agents.items():
            aliases = agent_config.get('alias', [])
            if name in aliases:
                return {**agent_config, 'name': agent_name}

        return None

    def list_agents(self) -> List[dict]:
        """List all available agents with status and metadata."""
        result = []
        agents = self.config.get('agents', default={})

        for name, agent_config in agents.items():
            provider = agent_config.get('provider', '')
            model = agent_config.get('model', '')
            available = provider in self.clients

            # Get model metadata
            model_info = get_model_info(model)

            result.append({
                'name': name,
                'aliases': agent_config.get('alias', []),
                'role': agent_config.get('role', ''),
                'provider': provider,
                'model': model,
                'available': available,
                'metadata': model_info
            })

        return result

    def call_agent(self, agent_name: str, prompt: str, context: str = "",
                   token_callback: Optional[Callable[[str, str, int, int], None]] = None,
                   system_prompt_override: Optional[str] = None) -> str:
        """
        Call an agent with a prompt.

        Args:
            agent_name: Name of the agent to call
            prompt: User prompt
            context: Optional context to include
            token_callback: Optional callback function(agent_name, model, input_tokens, output_tokens)
            system_prompt_override: Optional override for system prompt (for optimization)

        Returns:
            Agent response text
        """
        agent = self.resolve_agent(agent_name)
        if not agent:
            return f"Unknown agent: {agent_name}"

        provider = agent.get('provider', '')
        if provider not in self.clients:
            return f"Provider '{provider}' not available (missing API key or library)"

        client = self.clients[provider]
        model = agent.get('model', '')
        system_prompt = system_prompt_override if system_prompt_override is not None else agent.get('system_prompt', '')

        full_prompt = f"{prompt}\n\nContext:\n{context}" if context else prompt

        # Get model's actual max output tokens from metadata
        max_output = get_max_output_tokens(model, default=4000)

        try:
            if provider == 'anthropic':
                # Build system prompt - can be string or list for caching
                system_content = system_prompt
                
                # Apply prompt caching if enabled
                if self.anthropic_features and self.anthropic_features.is_prompt_caching_enabled():
                    # Convert system prompt to cacheable format
                    if isinstance(system_prompt, str) and system_prompt:
                        system_content = [
                            {
                                'type': 'text',
                                'text': system_prompt,
                                'cache_control': {'type': 'ephemeral'}
                            }
                        ]
                
                # Build API parameters
                api_params = {
                    'model': model,
                    'max_tokens': max_output,
                    'messages': [{'role': 'user', 'content': full_prompt}]
                }
                
                # Add system prompt if provided
                if system_content:
                    api_params['system'] = system_content
                
                # Add extended thinking if supported
                if supports_extended_thinking(model):
                    budget = get_extended_thinking_budget(model)
                    if budget > 0:
                        api_params['thinking'] = {
                            'type': 'enabled',
                            'budget_tokens': budget
                        }
                        print(c(f"Extended thinking enabled with budget: {budget} tokens", Colors.CYAN))
                
                # Use streaming for Anthropic to avoid SDK enforcement of 10-minute timeout
                # The SDK requires streaming when max_tokens is high enough that the request
                # could potentially take longer than 10 minutes to complete
                response = ""
                final_message = None
                with client.messages.stream(**api_params) as stream:
                    for text in stream.text_stream:
                        response += text
                    # Get final message to extract usage (must be inside context manager)
                    final_message = stream.get_final_message()

                # Track tokens if callback provided
                if token_callback and final_message and hasattr(final_message, 'usage'):
                    input_tokens = getattr(final_message.usage, 'input_tokens', 0)
                    output_tokens = getattr(final_message.usage, 'output_tokens', 0)
                    
                    # Extract cache statistics if available
                    cache_creation = getattr(final_message.usage, 'cache_creation_input_tokens', 0)
                    cache_read = getattr(final_message.usage, 'cache_read_input_tokens', 0)
                    
                    # Log cache performance
                    if cache_creation > 0:
                        print(c(f"Cache created: {cache_creation} tokens", Colors.GREEN))
                    if cache_read > 0:
                        savings_pct = (cache_read / (input_tokens + cache_read)) * 100 if (input_tokens + cache_read) > 0 else 0
                        print(c(f"Cache hit: {cache_read} tokens read ({savings_pct:.1f}% of input)", Colors.GREEN))
                    
                    # Call the callback with cache stats
                    # Check callback signature for backward compatibility:
                    # - Old signature: callback(agent_name, model, input_tokens, output_tokens)
                    # - New signature: callback(..., cache_creation, cache_read)
                    # We use reflection to maintain backward compatibility
                    try:
                        if hasattr(token_callback, '__code__') and token_callback.__code__.co_argcount >= 6:
                            # Enhanced callback with cache stats
                            token_callback(agent_name, model, input_tokens, output_tokens, cache_creation, cache_read)
                        else:
                            # Standard callback (backward compatible)
                            token_callback(agent_name, model, input_tokens, output_tokens)
                    except TypeError:
                        # Fallback: try standard signature if enhanced fails
                        token_callback(agent_name, model, input_tokens, output_tokens)

                return response

            elif provider in ['openai', 'xai', 'github']:
                # Use max_completion_tokens for GPT-5 and newer models
                api_params = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': full_prompt}
                    ]
                }
                if self._uses_max_completion_tokens(model):
                    api_params['max_completion_tokens'] = max_output
                else:
                    api_params['max_tokens'] = max_output

                resp = client.chat.completions.create(**api_params)

                # Track tokens if callback provided
                if token_callback and hasattr(resp, 'usage'):
                    input_tokens = getattr(resp.usage, 'prompt_tokens', 0)
                    output_tokens = getattr(resp.usage, 'completion_tokens', 0)
                    token_callback(agent_name, model, input_tokens, output_tokens)

                return resp.choices[0].message.content

            elif provider == 'huggingface':
                resp = client.chat_completion(
                    model=model,
                    max_tokens=max_output,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': full_prompt}
                    ]
                )

                # NOTE: The following is a very rough heuristic used only when a token
                #       callback is provided. It estimates tokens as character_count / 4,
                #       which can differ significantly from true model tokenization and
                #       should not be relied on for precise billing or quota enforcement.
                if token_callback:
                    # Approximate tokens (text length / 4) for coarse usage estimation only
                    input_tokens = len(system_prompt + full_prompt) // 4
                    output_tokens = len(resp.choices[0].message.content) // 4
                    token_callback(agent_name, model, input_tokens, output_tokens)

                return resp.choices[0].message.content

        except Exception as e:
            return f"API error ({provider}): {e}"

        return "No response"

    def count_tokens_anthropic(self, model: str, messages: List[Dict], 
                               system: str = "", tools: List[Dict] = None) -> Optional[int]:
        """
        Get precise token count from Anthropic API.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            system: System prompt string
            tools: Optional list of tool definitions
        
        Returns:
            Token count, or None if unavailable
        """
        if not self.anthropic_features:
            return None
        
        return self.anthropic_features.count_tokens(model, messages, system, tools)
