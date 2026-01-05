"""Configuration management for Readable app."""

import json
import os
from pathlib import Path
from typing import Optional
from .logger import get_logger

logger = get_logger("readable.config")


class Config:
    """Manages application configuration with file and environment variable support."""

    DEFAULT_CONFIG_FILE = Path.home() / ".readable" / "config.json"

    # Default configuration values
    DEFAULTS = {
        "tts_url": "http://100.71.118.55:8001",
        "max_text_length": 1_000_000,  # 1 million chars (~700 pages)
        "max_chunks": 100,  # Maximum chunks per reading
        "max_workers": 4,  # Parallel TTS workers
        "default_voice": "af_bella",
        "default_speed": 1.0,
        "cache_max_size_mb": 100,
        "history_max_size": 50,
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to config file (defaults to ~/.readable/config.json)
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load configuration from file and environment variables."""
        config = self.DEFAULTS.copy()

        # Load from file if exists
        if self.config_file.exists():
            try:
                file_config = json.loads(self.config_file.read_text())
                config.update(file_config)
                logger.info(f"Loaded config from {self.config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config file: {e}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Override with environment variables
        env_overrides = {
            "tts_url": os.getenv("KOKORO_TTS_URL"),
            "max_text_length": os.getenv("READABLE_MAX_TEXT_LENGTH"),
            "max_workers": os.getenv("READABLE_MAX_WORKERS"),
        }

        for key, value in env_overrides.items():
            if value is not None:
                try:
                    # Convert to appropriate type
                    if key in ["max_text_length", "max_chunks", "max_workers", "cache_max_size_mb", "history_max_size"]:
                        config[key] = int(value)
                    elif key in ["default_speed"]:
                        config[key] = float(value)
                    else:
                        config[key] = value
                    logger.info(f"Config override from env: {key}={value}")
                except ValueError as e:
                    logger.warning(f"Invalid environment variable {key}={value}: {e}")

        return config

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.data.get(key, default)

    def save(self):
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            self.config_file.write_text(json.dumps(self.data, indent=2))
            logger.info(f"Saved config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def create_default_config(self):
        """Create default configuration file."""
        self.data = self.DEFAULTS.copy()
        self.save()
        logger.info("Created default configuration file")

    @property
    def tts_url(self) -> str:
        """Get TTS API URL."""
        return self.data["tts_url"]

    @property
    def max_text_length(self) -> int:
        """Get maximum text length."""
        return self.data["max_text_length"]

    @property
    def max_chunks(self) -> int:
        """Get maximum chunks."""
        return self.data["max_chunks"]

    @property
    def max_workers(self) -> int:
        """Get maximum parallel workers."""
        return self.data["max_workers"]

    @property
    def default_voice(self) -> str:
        """Get default voice."""
        return self.data["default_voice"]

    @property
    def default_speed(self) -> float:
        """Get default speed."""
        return self.data["default_speed"]
