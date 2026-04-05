"""
Configuration manager for storing and loading application settings.
"""

import json
import os
from pathlib import Path


CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG = {
    "groq_api_key": "",
    "text_model": "llama-3.3-70b-versatile",
    "vision_model": "llama-3.2-11b-vision-preview",
    "output_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"),
    "uploads_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"),
    # TRELLIS settings
    "trellis_steps": 12,
    "trellis_cfg_strength": 7.5,
    "theme": "dark",
}


def load_config() -> dict:
    """Load configuration from file, returning defaults if not found."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(stored)
            return config
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"[Config] Save error: {e}")


def get_setting(key: str, default=None):
    """Get a single setting value."""
    config = load_config()
    return config.get(key, default)


def set_setting(key: str, value) -> None:
    """Set a single setting value."""
    config = load_config()
    config[key] = value
    save_config(config)


def ensure_directories():
    """Ensure required directories exist."""
    config = load_config()
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["uploads_dir"]).mkdir(parents=True, exist_ok=True)

