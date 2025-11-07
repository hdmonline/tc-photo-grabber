"""
Telegram settings manager
Persists user preferences for Telegram notifications
"""

import json
import logging
from pathlib import Path


class TelegramSettings:
    """Manage Telegram notification settings"""

    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize settings manager

        Args:
            cache_dir: Directory to store settings
        """
        self.logger = logging.getLogger("TelegramSettings")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.cache_dir / "telegram_settings.json"
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        """Load settings from cache file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    self.logger.debug(f"Loaded Telegram settings: {settings}")
                    return settings
            except Exception as e:
                self.logger.error(f"Failed to load settings: {str(e)}")
        return {"send_as_file": True}  # Default to sending as file

    def _save_settings(self):
        """Save settings to cache file"""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)
            self.logger.debug(f"Saved Telegram settings: {self.settings}")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {str(e)}")

    def get_send_as_file(self) -> bool:
        """Get the send_as_file preference"""
        return self.settings.get("send_as_file", True)

    def set_send_as_file(self, value: bool):
        """Set the send_as_file preference"""
        self.settings["send_as_file"] = value
        self._save_settings()
        self.logger.info(f"Updated send_as_file setting to: {value}")
