"""
Async Telegram bot handler for commands
Uses python-telegram-bot library with async/await
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from pathlib import Path
from typing import Optional


class TelegramBotHandler:
    """Async handler for Telegram bot commands"""

    def __init__(self, bot_token: str, chat_id: str, cache_dir: str = "./cache"):
        """
        Initialize Telegram bot handler

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Telegram chat ID to accept commands from
            cache_dir: Directory to store persistent settings
        """
        self.logger = logging.getLogger('TelegramBot')
        self.bot_token = bot_token
        self.chat_id = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.cache_dir / 'telegram_settings.json'
        self.settings = self._load_settings()
        self.application = None

    def _load_settings(self) -> dict:
        """Load settings from cache file"""
        if self.settings_file.exists():
            try:
                import json
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.logger.debug(f"Loaded Telegram settings: {settings}")
                    return settings
            except Exception as e:
                self.logger.error(f"Failed to load settings: {str(e)}")
        return {'send_as_file': True}  # Default to sending as file

    def _save_settings(self):
        """Save settings to cache file"""
        try:
            import json
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            self.logger.debug(f"Saved Telegram settings: {self.settings}")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {str(e)}")

    def get_send_as_file(self) -> bool:
        """Get the send_as_file preference"""
        return self.settings.get('send_as_file', True)

    def set_send_as_file(self, value: bool):
        """Set the send_as_file preference"""
        self.settings['send_as_file'] = value
        self._save_settings()
        self.logger.info(f"Updated send_as_file setting to: {value}")

    async def sendfile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /sendfile command"""
        if update.message.chat.id != self.chat_id:
            return
        
        self.set_send_as_file(True)
        await update.message.reply_text("✅ Photos will now be sent as files (original quality)")
        self.logger.info("Switched to sending photos as files")

    async def sendphoto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /sendphoto command"""
        if update.message.chat.id != self.chat_id:
            return
        
        self.set_send_as_file(False)
        await update.message.reply_text("✅ Photos will now be sent as compressed images")
        self.logger.info("Switched to sending photos as compressed images")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        if update.message.chat.id != self.chat_id:
            return
        
        mode = "files (original quality)" if self.get_send_as_file() else "compressed photos"
        message = (
            f"📊 Current settings:\n"
            f"Photo mode: {mode}\n\n"
            f"Commands:\n"
            f"/sendfile - Send as files\n"
            f"/sendphoto - Send compressed"
        )
        await update.message.reply_text(message)

    def setup_application(self) -> Application:
        """Setup the Telegram application with command handlers"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("sendfile", self.sendfile_command))
        self.application.add_handler(CommandHandler("sendphoto", self.sendphoto_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        self.logger.info("Telegram bot application configured")
        return self.application

    def run_polling_sync(self):
        """Run the bot in polling mode (blocking, for sync code)"""
        if not self.application:
            self.setup_application()
        
        self.logger.info("Starting Telegram bot in polling mode...")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize and start the application
            loop.run_until_complete(self.application.initialize())
            loop.run_until_complete(self.application.start())
            loop.run_until_complete(self.application.updater.start_polling(drop_pending_updates=True))
            
            # Keep running until stopped
            loop.run_forever()
        except Exception as e:
            self.logger.error(f"Error in bot polling: {e}")
        finally:
            # Cleanup
            try:
                loop.run_until_complete(self.application.updater.stop())
                loop.run_until_complete(self.application.stop())
                loop.run_until_complete(self.application.shutdown())
            except:
                pass
            loop.close()
