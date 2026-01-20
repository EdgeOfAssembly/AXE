"""
Configuration manager for AXE.

Implements three-file architecture:
  1. models.yaml - Static model metadata (loaded first)
  2. providers.yaml - Provider infrastructure (loaded second)
  3. axe.yaml - User configuration (loaded third)

Includes validation to ensure consistency across all config files.
"""

import os
import json
from typing import Optional, Any, Dict, List

# Try to import yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .constants import DEFAULT_CONFIG
from utils.formatting import Colors, c


class Config:
    """Configuration manager with three-file architecture and validation."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = DEFAULT_CONFIG.copy()
        self.config_path = config_path
        self.models_config = {}
        self.providers_config = {}
        
        # Determine base directory for config files
        if config_path and os.path.exists(config_path):
            self.base_dir = os.path.dirname(os.path.abspath(config_path))
        else:
            self.base_dir = os.getcwd()
        
        # Load configuration in strict order
        self._load_all_configs(config_path)

    def _load_all_configs(self, axe_config_path: Optional[str] = None) -> None:
        """Load all three config files in order with validation."""
        print(c("Loading configuration...", Colors.CYAN))
        
        # 1. Load models.yaml first (static reference data)
        models_path = os.path.join(self.base_dir, 'models.yaml')
        if os.path.exists(models_path):
            self.models_config = self._load_yaml_file(models_path)
            model_count = len(self.models_config.get('models', {}))
            print(c(f"  ✓ models.yaml ({model_count} models loaded)", Colors.GREEN))
        else:
            print(c(f"  ⚠ models.yaml not found, using defaults", Colors.YELLOW))
        
        # 2. Load providers.yaml second (provider infrastructure)
        providers_path = os.path.join(self.base_dir, 'providers.yaml')
        if os.path.exists(providers_path):
            providers_file = self._load_yaml_file(providers_path)
            self.providers_config = providers_file.get('providers', {})
            enabled_count = sum(1 for p in self.providers_config.values() if p.get('enabled', True))
            disabled_providers = [name for name, p in self.providers_config.items() if not p.get('enabled', True)]
            provider_summary = f"{enabled_count} enabled"
            if disabled_providers:
                provider_summary += f", {len(disabled_providers)} disabled ({', '.join(disabled_providers)})"
            print(c(f"  ✓ providers.yaml ({provider_summary})", Colors.GREEN))
            
            # Validate providers against models
            self._validate_providers()
        else:
            # Backward compatibility: try to load from axe.yaml
            print(c(f"  ⚠ providers.yaml not found, checking axe.yaml for legacy providers...", Colors.YELLOW))
        
        # 3. Load axe.yaml last (user config)
        if axe_config_path and os.path.exists(axe_config_path):
            self.load(axe_config_path)
        else:
            # Try default locations
            for path in ['axe.yaml', 'axe.yml', 'axe.json', '.axe.yaml', '.axe.json']:
                full_path = os.path.join(self.base_dir, path)
                if os.path.exists(full_path):
                    self.load(full_path)
                    break
        
        # If providers weren't loaded from providers.yaml, check axe.yaml (backward compat)
        if not self.providers_config and 'providers' in self.config:
            print(c("  ⚠ Using legacy providers from axe.yaml (consider migrating to providers.yaml)", Colors.YELLOW))
            self.providers_config = self.config.get('providers', {})
        
        # Merge providers into main config for backward compatibility
        if self.providers_config:
            self.config['providers'] = self.providers_config
        
        # Validate agents against providers and models
        if 'agents' in self.config:
            self._validate_agents()
        
        print(c("Configuration validated successfully.", Colors.GREEN))

    def _load_yaml_file(self, path: str) -> Dict:
        """Load a YAML or JSON file and return its contents."""
        try:
            with open(path, 'r') as f:
                if path.endswith(('.yaml', '.yml')) and HAS_YAML:
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            print(c(f"  ✗ Error loading {path}: {e}", Colors.RED))
            return {}

    def load(self, path: str) -> None:
        """Load axe.yaml config file."""
        try:
            loaded = self._load_yaml_file(path)
            if loaded:
                # Deep merge with defaults
                self._deep_merge(self.config, loaded)
                # Track the loaded config path
                self.config_path = path
                agent_count = len(self.config.get('agents', {}))
                print(c(f"  ✓ axe.yaml ({agent_count} agents configured)", Colors.GREEN))
        except Exception as e:
            print(c(f"  ✗ Error loading axe.yaml: {e}", Colors.RED))

    def save(self, path: Optional[str] = None) -> None:
        """Save current config to file."""
        path = path or self.config_path or 'axe.yaml'
        try:
            with open(path, 'w') as f:
                if path.endswith(('.yaml', '.yml')) and HAS_YAML:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                else:
                    json.dump(self.config, f, indent=2)
            print(c(f"Config saved: {path}", Colors.GREEN))
        except Exception as e:
            print(c(f"Config save error: {e}", Colors.RED))

    def _validate_providers(self) -> None:
        """Validate that all models in providers exist in models.yaml."""
        if not self.models_config:
            return  # Skip validation if models.yaml wasn't loaded
        
        models_list = self.models_config.get('models', {})
        errors = []
        
        for provider_name, provider_config in self.providers_config.items():
            if not isinstance(provider_config, dict):
                continue
            
            provider_models = provider_config.get('models', [])
            for model_id in provider_models:
                if model_id not in models_list:
                    errors.append(
                        f"Provider '{provider_name}' lists model '{model_id}' "
                        f"but it's not defined in models.yaml"
                    )
        
        if errors:
            print(c("\n✗ Validation Errors in providers.yaml:", Colors.RED))
            for error in errors:
                print(c(f"  • {error}", Colors.RED))
            print(c("  Fix: Add missing models to models.yaml or remove from providers.yaml\n", Colors.YELLOW))

    def _validate_agents(self) -> None:
        """Validate that agent configurations are valid."""
        agents = self.config.get('agents', {})
        models_list = self.models_config.get('models', {})
        errors = []
        
        for agent_name, agent_config in agents.items():
            if not isinstance(agent_config, dict):
                continue
            
            # Validate provider is defined and enabled
            provider = agent_config.get('provider')
            if provider:
                if provider not in self.providers_config:
                    errors.append(
                        f"Agent '{agent_name}' uses provider '{provider}' "
                        f"but it's not defined in providers.yaml"
                    )
                elif not self.providers_config[provider].get('enabled', True):
                    errors.append(
                        f"Agent '{agent_name}' uses provider '{provider}' "
                        f"but it is disabled in providers.yaml. Enable it first."
                    )
                else:
                    # Validate model is in provider's model list
                    model = agent_config.get('model')
                    if model:
                        provider_models = self.providers_config[provider].get('models', [])
                        if model not in provider_models:
                            errors.append(
                                f"Agent '{agent_name}' uses model '{model}' "
                                f"but it's not in provider '{provider}' model list"
                            )
                        
                        # Validate model exists in models.yaml (if loaded)
                        if models_list and model not in models_list:
                            errors.append(
                                f"Agent '{agent_name}' uses model '{model}' "
                                f"but it's not defined in models.yaml"
                            )
                        
                        # Check for uppercase in model IDs (should be lowercase)
                        # Exception: GitHub Models use prefixes by design
                        if provider != 'github' and model != model.lower():
                            suggestion = model.lower()
                            errors.append(
                                f"Agent '{agent_name}' uses model '{model}' "
                                f"but model IDs must be lowercase. Did you mean '{suggestion}'?"
                            )
        
        if errors:
            print(c("\n✗ Validation Errors in agent configuration:", Colors.RED))
            for error in errors:
                print(c(f"  • {error}", Colors.RED))
            print(c("  Fix: Update agent definitions in axe.yaml to match providers.yaml and models.yaml\n", Colors.YELLOW))


    def _deep_merge(self, base: dict, update: dict) -> None:
        """Deep merge update into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, *keys, default=None) -> Any:
        """Get nested config value."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_tool_whitelist(self) -> set:
        """Get flat set of all allowed tools."""
        tools = set()
        for category_tools in self.config.get('tools', {}).values():
            tools.update(category_tools)
        return tools
