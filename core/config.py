"""
Configuration manager for AXE.

Supports YAML and JSON configuration files with deep merging.
"""

import os
import json
from typing import Optional, Any

# Try to import yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .constants import DEFAULT_CONFIG
from utils.formatting import Colors, c


class Config:
    """Configuration manager supporting YAML and JSON."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = DEFAULT_CONFIG.copy()
        self.config_path = config_path

        if config_path and os.path.exists(config_path):
            self.load(config_path)
        else:
            # Try default locations
            for path in ['axe.yaml', 'axe.yml', 'axe.json', '.axe.yaml', '.axe.json']:
                if os.path.exists(path):
                    self.load(path)
                    break

    def load(self, path: str) -> None:
        """Load config from YAML or JSON file."""
        try:
            with open(path, 'r') as f:
                if path.endswith(('.yaml', '.yml')) and HAS_YAML:
                    loaded = yaml.safe_load(f)
                else:
                    loaded = json.load(f)

                # Deep merge with defaults
                self._deep_merge(self.config, loaded)
                print(c(f"Loaded config: {path}", Colors.DIM))
        except Exception as e:
            print(c(f"Config load error: {e}", Colors.RED))

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
