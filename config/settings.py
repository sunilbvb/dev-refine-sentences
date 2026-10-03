"""Configuration, personal dictionary, custom snippets, and API keys manager.

100% Python Standard Library.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "whitelist": [
        "Antigravity",
        "Kubernetes",
        "k8s",
        "protobuf",
        "gRPC",
        "GraphQL",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Docker",
        "DevOps",
        "CI/CD",
        "API",
        "SDK",
    ],
    "snippets": {
        "lgtm": "Looks good to me!",
        "omw": "on my way",
        "wip": "work in progress",
        "fyi": "for your information",
        "imo": "in my opinion",
        "imho": "in my humble opinion",
        "tbh": "to be honest",
        "np": "no problem",
        "yw": "you're welcome",
        "brb": "be right back",
        "idk": "I don't know",
        "afaik": "as far as I know",
    },
    "api_keys": {
        "gemini": "",
        "openai": "",
        "anthropic": "",
    },
    "preferred_tone": "standard",
    "max_history_entries": 50,
}


class ConfigManager:
    """Manages user configuration, whitelist, text expansions, and AI API keys."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".config" / "refine_tool"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "config.json"
        self._ensure_config()

    def _ensure_config(self) -> None:
        """Create config directory and default config file if they do not exist."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            if not self.config_file.exists():
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2)
        except Exception:
            pass

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file or return default fallback."""
        if not self.config_file.exists():
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()

    def get_whitelist(self) -> List[str]:
        """Get list of protected whitelist words."""
        return self.load_config().get("whitelist", [])

    def get_snippets(self) -> Dict[str, str]:
        """Get dictionary of shortcut snippet expansions."""
        return self.load_config().get("snippets", {})

    def add_whitelist_word(self, word: str) -> None:
        """Add a word to whitelist."""
        cfg = self.load_config()
        if word not in cfg["whitelist"]:
            cfg["whitelist"].append(word)
            self._save_config(cfg)

    def add_snippet(self, shortcut: str, expansion: str) -> None:
        """Add or update a snippet expansion."""
        cfg = self.load_config()
        cfg["snippets"][shortcut.lower()] = expansion
        self._save_config(cfg)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Retrieve API key for provider (checks env var first, then config)."""
        prov = provider.lower().strip()
        env_map = {
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "chatgpt": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
        }

        # Check environment variable
        env_var = env_map.get(prov)
        if env_var and os.environ.get(env_var):
            return os.environ[env_var].strip()

        # Check config file
        cfg = self.load_config()
        keys = cfg.get("api_keys", {})
        key = keys.get(prov, "")
        if not key and prov == "chatgpt":
            key = keys.get("openai", "")
        if not key and prov == "claude":
            key = keys.get("anthropic", "")

        return key.strip() if key else None

    def set_api_key(self, provider: str, key: str) -> None:
        """Save API key for provider into config file."""
        prov = provider.lower().strip()
        if prov == "chatgpt":
            prov = "openai"
        if prov == "claude":
            prov = "anthropic"

        cfg = self.load_config()
        if "api_keys" not in cfg:
            cfg["api_keys"] = {}
        cfg["api_keys"][prov] = key.strip()
        self._save_config(cfg)

    def _save_config(self, cfg: Dict[str, Any]) -> None:
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass
