"""
Async Telegram bot handler for commands
Uses python-telegram-bot library with async/await
"""

import asyncio
import calendar
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


class TelegramBotHandler:
    """Async handler for Telegram bot commands"""

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        cache_dir: str = "./cache",
        output_dir: str = "./photos",
    ):
        """
        Initialize Telegram bot handler

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Telegram chat ID to accept commands from
            cache_dir: Directory to store persistent settings
            output_dir: Directory where photos are stored
        """
        self.logger = logging.getLogger("TelegramBot")
        self.bot_token = bot_token
        self.chat_id = int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.cache_dir / "telegram_settings.json"
        self.settings = self._load_settings()
        self.application = None

    def _load_settings(self) -> dict:
        """Load settings from cache file"""
        if self.settings_file.exists():
            try:
                import json

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
            import json

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

    async def sendfile_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /sendfile command"""
        if update.message.chat.id != self.chat_id:
            return

        self.set_send_as_file(True)
        await update.message.reply_text(
            "✅ Photos will now be sent as files (original quality)"
        )
        self.logger.info("Switched to sending photos as files")

    async def sendphoto_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /sendphoto command"""
        if update.message.chat.id != self.chat_id:
            return

        self.set_send_as_file(False)
        await update.message.reply_text(
            "✅ Photos will now be sent as compressed images"
        )
        self.logger.info("Switched to sending photos as compressed images")

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command"""
        if update.message.chat.id != self.chat_id:
            return

        mode = (
            "files (original quality)"
            if self.get_send_as_file()
            else "compressed photos"
        )
        message = (
            f"📊 Current settings:\n"
            f"Photo mode: {mode}\n\n"
            f"Commands:\n"
            f"/sendfile - Send as files\n"
            f"/sendphoto - Send compressed\n"
            f"/photos - Pick a date to view photos"
        )
        await update.message.reply_text(message)

    def _create_calendar(self, year: int, month: int) -> InlineKeyboardMarkup:
        """Create an inline keyboard calendar for the given month"""
        keyboard = []

        # Header with month and year
        header = [
            InlineKeyboardButton("<<", callback_data=f"cal_prev_{year}_{month}"),
            InlineKeyboardButton(
                f"{calendar.month_name[month]} {year}", callback_data="cal_ignore"
            ),
            InlineKeyboardButton(">>", callback_data=f"cal_next_{year}_{month}"),
        ]
        keyboard.append(header)

        # Day names
        day_names = [
            InlineKeyboardButton(day, callback_data="cal_ignore")
            for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        ]
        keyboard.append(day_names)

        # Calendar days
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
                else:
                    # Check if photos exist for this date
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                    has_photos = self._check_photos_exist(date_str)
                    label = f"📷{day}" if has_photos else str(day)
                    row.append(
                        InlineKeyboardButton(
                            label, callback_data=f"cal_day_{year}_{month}_{day}"
                        )
                    )
            keyboard.append(row)

        # Close button
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="cal_close")])

        return InlineKeyboardMarkup(keyboard)

    def _check_photos_exist(self, date_str: str) -> bool:
        """Check if any photos exist for the given date"""
        try:
            # Extract year from date_str (format: YYYY-MM-DD)
            year = date_str.split("-")[0]
            year_dir = self.output_dir / year

            # If year directory doesn't exist, no photos for this date
            if not year_dir.exists():
                return False

            # Check if any files match the pattern in the year subfolder
            for ext in ["jpg", "jpeg", "png", "gif", "tiff", "tif", "bmp", "webp"]:
                if list(year_dir.glob(f"{date_str}_*.{ext}")):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking photos for {date_str}: {e}")
            return False

    def _get_photos_by_date(self, date_str: str) -> List[Path]:
        """Get all photos for a specific date"""
        photos = []
        try:
            # Extract year from date_str (format: YYYY-MM-DD)
            year = date_str.split("-")[0]
            year_dir = self.output_dir / year

            # If year directory doesn't exist, return empty list
            if not year_dir.exists():
                return []

            # Get photos from the year subfolder
            for ext in ["jpg", "jpeg", "png", "gif", "tiff", "tif", "bmp", "webp"]:
                photos.extend(year_dir.glob(f"{date_str}_*.{ext}"))
            # Sort by filename
            photos.sort()
            return photos
        except Exception as e:
            self.logger.error(f"Error getting photos for {date_str}: {e}")
            return []

    def _get_photo_metadata(self, photo_path: Path) -> Dict[str, str]:
        """Extract metadata from photo using exiftool"""
        try:
            result = subprocess.run(
                [
                    "exiftool",
                    "-j",
                    "-ImageDescription",
                    "-Description",
                    "-Title",
                    str(photo_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout:
                metadata = json.loads(result.stdout)[0]

                # Try different metadata fields for description
                description = (
                    metadata.get("ImageDescription")
                    or metadata.get("Description")
                    or metadata.get("Title")
                    or ""
                ).strip()

                return {"description": description}
        except Exception as e:
            self.logger.debug(f"Could not read metadata from {photo_path.name}: {e}")

        return {"description": ""}

    async def photos_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /photos command - show calendar picker"""
        if update.message.chat.id != self.chat_id:
            return

        # Show current month calendar
        now = datetime.now()
        calendar_markup = self._create_calendar(now.year, now.month)

        await update.message.reply_text(
            "📅 Select a date to view photos:\n(Days with 📷 have photos)",
            reply_markup=calendar_markup,
        )

    async def calendar_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle calendar button callbacks"""
        query = update.callback_query
        await query.answer()

        # Only respond to authorized chat
        if query.message.chat.id != self.chat_id:
            return

        data = query.data

        # Ignore clicks on empty cells and header
        if data == "cal_ignore":
            return

        # Close calendar
        if data == "cal_close":
            await query.message.delete()
            return

        # Navigate to previous month
        if data.startswith("cal_prev_"):
            _, _, year, month = data.split("_")
            year, month = int(year), int(month)
            # Go to previous month
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1

            calendar_markup = self._create_calendar(year, month)
            await query.message.edit_reply_markup(reply_markup=calendar_markup)
            return

        # Navigate to next month
        if data.startswith("cal_next_"):
            _, _, year, month = data.split("_")
            year, month = int(year), int(month)
            # Go to next month
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

            calendar_markup = self._create_calendar(year, month)
            await query.message.edit_reply_markup(reply_markup=calendar_markup)
            return

        # Day selected
        if data.startswith("cal_day_"):
            _, _, year, month, day = data.split("_")
            year, month, day = int(year), int(month), int(day)
            date_str = f"{year:04d}-{month:02d}-{day:02d}"

            # Get photos for this date
            photos = self._get_photos_by_date(date_str)

            if not photos:
                await query.message.edit_text(
                    f"📅 {date_str}\n\n❌ No photos found for this date."
                )
                return

            # Delete the calendar message
            await query.message.delete()

            # Send a status message
            status_msg = await context.bot.send_message(
                chat_id=self.chat_id,
                text=f"📅 {date_str}\n\n📷 Found {len(photos)} photo(s). Sending...",
            )

            # Send all photos for this date
            send_as_file = self.get_send_as_file()
            for idx, photo_path in enumerate(photos, 1):
                try:
                    # Extract metadata
                    metadata = self._get_photo_metadata(photo_path)

                    # Build caption with description
                    caption_parts = [f"📅 {date_str} ({idx}/{len(photos)})"]

                    if metadata["description"]:
                        caption_parts.append(f"\n\n{metadata['description']}")

                    caption = "".join(caption_parts)

                    with open(photo_path, "rb") as photo_file:
                        if send_as_file:
                            await context.bot.send_document(
                                chat_id=self.chat_id,
                                document=photo_file,
                                caption=caption,
                                filename=photo_path.name,
                            )
                        else:
                            await context.bot.send_photo(
                                chat_id=self.chat_id, photo=photo_file, caption=caption
                            )
                except Exception as e:
                    self.logger.error(f"Failed to send photo {photo_path}: {e}")
                    await context.bot.send_message(
                        chat_id=self.chat_id,
                        text=f"❌ Failed to send {photo_path.name}: {str(e)}",
                    )

            # Update status message
            await status_msg.edit_text(
                f"📅 {date_str}\n\n✅ Sent {len(photos)} photo(s)!"
            )
            return

    def setup_application(self) -> Application:
        """Setup the Telegram application with command handlers"""
        self.application = Application.builder().token(self.bot_token).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("sendfile", self.sendfile_command))
        self.application.add_handler(
            CommandHandler("sendphoto", self.sendphoto_command)
        )
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("photos", self.photos_command))

        # Add callback query handler for calendar interactions
        self.application.add_handler(CallbackQueryHandler(self.calendar_callback))

        self.logger.info("Telegram bot application configured")
        return self.application

    async def _register_commands(self):
        """Register bot commands with Telegram so they appear in the command menu"""
        try:
            commands = [
                BotCommand("sendfile", "Send photos as files (original quality)"),
                BotCommand("sendphoto", "Send photos as compressed images"),
                BotCommand("status", "Show current settings"),
                BotCommand("photos", "Pick a date to view photos"),
            ]
            await self.application.bot.set_my_commands(commands)
            self.logger.info("Bot commands registered with Telegram")
        except Exception as e:
            self.logger.error(f"Failed to register commands: {e}")

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
            loop.run_until_complete(self._register_commands())
            loop.run_until_complete(
                self.application.updater.start_polling(drop_pending_updates=True)
            )

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
            except Exception:
                pass
            loop.close()
