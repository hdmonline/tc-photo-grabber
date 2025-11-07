"""
Telegram notification service
Sends notifications and photos to a Telegram channel/chat
"""

import logging
from pathlib import Path
from typing import List, Optional

import requests


class TelegramNotifier:
    """Send notifications and photos to Telegram"""

    def __init__(self, bot_token: str, chat_id: str, bot_handler=None):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Telegram chat ID (can be a channel, group, or user)
            bot_handler: Optional TelegramBotHandler instance for settings
        """
        self.logger = logging.getLogger("TelegramNotifier")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.bot_handler = bot_handler

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a text message to Telegram

        Args:
            text: Message text to send
            parse_mode: Parse mode for formatting (Markdown, HTML, or None)

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {"chat_id": self.chat_id, "text": text}
            if parse_mode:
                data["parse_mode"] = parse_mode

            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            self.logger.info("Successfully sent message to Telegram")
            return True
        except requests.exceptions.HTTPError as e:
            # Log detailed error information
            error_msg = str(e)
            if hasattr(e.response, "text"):
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg}\nDetails: {error_detail}"

                    # If Markdown parsing failed, retry without formatting
                    if parse_mode and "can't parse" in str(error_detail).lower():
                        self.logger.warning(
                            "Markdown parsing failed, retrying without formatting"
                        )
                        return self.send_message(text, parse_mode=None)
                except Exception:
                    error_msg = f"{error_msg}\nResponse: {e.response.text}"
            self.logger.error(f"Failed to send Telegram message: {error_msg}")
            self.logger.error(f"Chat ID used: {self.chat_id}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
            return False

    def send_photo(self, photo_path: Path, caption: Optional[str] = None) -> bool:
        """
        Send a photo to Telegram (as document or photo based on settings)

        Args:
            photo_path: Path to the photo file
            caption: Optional caption for the photo

        Returns:
            True if successful, False otherwise
        """
        try:
            send_as_file = (
                self.bot_handler.get_send_as_file() if self.bot_handler else True
            )

            if send_as_file:
                # Send as document to preserve original resolution
                url = f"{self.base_url}/sendDocument"
                file_key = "document"
                timeout = 120
            else:
                # Send as photo (compressed)
                url = f"{self.base_url}/sendPhoto"
                file_key = "photo"
                timeout = 60

            with open(photo_path, "rb") as photo_file:
                files = {file_key: photo_file}
                data = {"chat_id": self.chat_id}
                if caption:
                    data["caption"] = caption

                response = requests.post(url, data=data, files=files, timeout=timeout)
                response.raise_for_status()

            self.logger.debug(
                f"Successfully sent photo: {photo_path.name} (as {'file' if send_as_file else 'photo'})"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to send photo {photo_path.name}: {str(e)}")
            return False

    def send_photos_batch(self, photo_items: List[dict], max_photos: int = 10) -> int:
        """
        Send multiple photos to Telegram

        Args:
            photo_items: List of dicts with 'path' and 'description' keys
            max_photos: Maximum number of photos to send (default: 10)

        Returns:
            Number of photos successfully sent
        """
        sent_count = 0
        photos_to_send = photo_items[:max_photos]

        self.logger.info(f"Sending {len(photos_to_send)} photos to Telegram")

        for item in photos_to_send:
            photo_path = item["path"]
            description = item.get("description", "")

            # Use only the description as caption (no filename)
            caption = None
            if description:
                # Telegram caption limit is 1024 characters
                if len(description) > 1024:
                    description = description[:1020] + "..."
                caption = description

            if self.send_photo(photo_path, caption):
                sent_count += 1

        if len(photo_items) > max_photos:
            remaining = len(photo_items) - max_photos
            self.send_message(
                f"_{remaining} more photos were downloaded but not sent to avoid spam._"
            )

        return sent_count

    def send_download_summary(
        self, downloaded_count: int, total_posts: int, photo_items: List[dict]
    ) -> bool:
        """
        Send a summary message with download statistics

        Args:
            downloaded_count: Number of new photos downloaded
            total_posts: Total number of posts found
            photo_items: List of dicts with 'path' and 'description' keys

        Returns:
            True if notification was sent successfully
        """
        try:
            if downloaded_count == 0:
                # Don't send any notification if no new photos
                self.logger.info(
                    "No new photos downloaded, skipping Telegram notification"
                )
                return True

            # Send summary message
            message = (
                f"✅ *Photo Sync Complete*\n\n"
                f"📸 New photos downloaded: *{downloaded_count}*\n"
                f"📋 Total posts scanned: {total_posts}\n\n"
            )

            if photo_items:
                message += f"Sending {min(len(photo_items), 10)} photos..."

            self.send_message(message)

            # Send photos if any
            if photo_items:
                sent = self.send_photos_batch(photo_items, max_photos=10)
                self.logger.info(f"Sent {sent}/{len(photo_items)} photos to Telegram")

            return True

        except Exception as e:
            self.logger.error(f"Failed to send download summary: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """
        Test the Telegram bot connection

        Returns:
            True if connection is successful
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            bot_info = response.json()

            if bot_info.get("ok"):
                bot_name = bot_info.get("result", {}).get("username", "Unknown")
                self.logger.info(f"Successfully connected to Telegram bot: @{bot_name}")
                self.logger.info(f"Will send notifications to chat ID: {self.chat_id}")

                # Test connection without sending a message
                # Just verify the bot API works
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {str(e)}")
            return False
