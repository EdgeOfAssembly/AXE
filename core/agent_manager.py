"""
Agent Manager for AXE.

Manages agent connections and API calls to various LLM providers.
"""

import os
from typing import Optional, List, Dict, Any, Callable

from .config import Config
from .constants import USE_MAX_COMPLETION_TOKENS
from models.metadata import get_model_info
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
        self._init_clients()

    def _uses_max_completion_tokens(self, model: str) -> bool:
        """Check if a model requires max_completion_tokens parameter."""
        # Check if model name or prefix matches models that need max_completion_tokens
        for model_prefix in USE_MAX_COMPLETION_TOKENS:
            if model.startswith(model_prefix):
                return True
        return False

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

        try:
            if provider == 'anthropic':
                resp = client.messages.create(
                    model=model,
                    max_tokens=32768,
                    system=system_prompt,
                    messages=[{'role': 'user', 'content': full_prompt}]
                )

                # Track tokens if callback provided
                if token_callback and hasattr(resp, 'usage'):
                    input_tokens = getattr(resp.usage, 'input_tokens', 0)
                    output_tokens = getattr(resp.usage, 'output_tokens', 0)
                    token_callback(agent_name, model, input_tokens, output_tokens)

                return resp.content[0].text

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
                    api_params['max_completion_tokens'] = 32768
                else:
                    api_params['max_tokens'] = 32768

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
                    max_tokens=32768,
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
