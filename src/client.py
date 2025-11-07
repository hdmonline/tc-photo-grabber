"""
HTTP client for Transparent Classroom API
Manages authentication and requests to the API

This module uses the same authentication and session management logic
as the original get_photos.py implementation.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import filetype
import requests
from bs4 import BeautifulSoup

from .config import Config


class TransparentClassroomClient:
    """Client for interacting with Transparent Classroom API"""

    def __init__(self, config: Config):
        """
        Initialize the Transparent Classroom client

        Args:
            config: Configuration object
        """
        self.logger = logging.getLogger("TransparentClassroom")
        self.config = config
        self.session = requests.Session()

        # Create necessary directories
        os.makedirs(config.cache_dir, exist_ok=True)
        os.makedirs(config.output_dir, exist_ok=True)

        # Initialize session
        self._login(config.email, config.password)

    def _login(self, email: str, password: str) -> bool:
        """
        Login to Transparent Classroom
        Uses the same authentication flow as the original implementation
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            # Get CSRF token
            login_url = "https://www.transparentclassroom.com/souls/sign_in"
            response = self.session.get(login_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_token = soup.find("meta", {"name": "csrf-token"})

            if not csrf_token:
                raise ValueError("Could not find CSRF token")

            login_data = {
                "authenticity_token": csrf_token["content"],
                "soul[login]": email,
                "soul[password]": password,
                "soul[remember_me]": "0",
                "commit": "Sign in",
            }

            # Perform login
            response = self.session.post(login_url, data=login_data, headers=headers)
            response.raise_for_status()

            if "You need to sign in" in response.text:
                raise ValueError("Invalid credentials")

            self.logger.info("Login successful")
            return True

        except (requests.exceptions.RequestException, ValueError) as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise

    def _get_cached_data(self, cache_file: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        cache_path = Path(cache_file)
        if cache_path.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(
                cache_path.stat().st_mtime
            )
            if cache_age.total_seconds() <= self.config.cache_timeout:
                self.logger.info(f"Loading cached data from {cache_file}")
                with open(cache_file, "r") as file:
                    return json.load(file)
            else:
                self.logger.info(f"Cache expired, removing {cache_file}")
                cache_path.unlink()
        return None

    def get_posts(self, page: int = 1) -> Optional[List[Dict[str, Any]]]:
        """Get posts for the specified page"""
        cache_file = f"{self.config.cache_dir}/cache_page_{page}.json"

        # Try cache first
        cached_data = self._get_cached_data(cache_file)
        if cached_data:
            return cached_data

        # Make API request
        url = (
            f"https://www.transparentclassroom.com/s/{self.config.school_id}"
            f"/children/{self.config.child_id}/posts.json"
        )

        try:
            response = self.session.get(url, params={"locale": "en", "page": page})
            response.raise_for_status()

            # Cache response
            with open(cache_file, "w") as file:
                json.dump(response.json(), file, indent=4, sort_keys=True)

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get posts: {str(e)}")
            return None

    def crawl_all_posts(self) -> List[Dict[str, Any]]:
        """Crawl all photos from all pages"""
        photos = []
        page = 0

        self.logger.info("Starting to crawl all posts from Transparent Classroom")

        while True:
            page += 1
            posts = self.get_posts(page=page)

            if not posts:
                break

            photos.extend(posts)
            self.logger.info(f"Retrieved page {page} with {len(posts)} posts")

        self.logger.info(
            f"Crawling complete. Found {len(photos)} total posts across {page} pages"
        )
        return photos

    def set_metadata(
        self, image_path: str, title: str, creator: str, created_at: datetime
    ) -> None:
        """Set metadata using exiftool - compatible with Synology Photos and all image formats"""
        try:
            command = [
                "exiftool",
                "-overwrite_original",  # Don't create backup files
                "-ignoreMinorErrors",  # Don't fail on minor issues
                # EXIF tags (widely supported)
                f"-EXIF:ImageDescription={title}",
                f"-EXIF:Artist={creator}",
                f'-EXIF:DateTimeOriginal={created_at.strftime("%Y:%m:%d %H:%M:%S")}',
                # GPS data (works for all formats via EXIF/XMP)
                f"-EXIF:GPSLatitude={abs(self.config.school_lat)}",
                f'-EXIF:GPSLatitudeRef={"N" if self.config.school_lat >= 0 else "S"}',
                f"-EXIF:GPSLongitude={abs(self.config.school_lng)}",
                f'-EXIF:GPSLongitudeRef={"E" if self.config.school_lng >= 0 else "W"}',
                # IPTC tags (for JPEG/TIFF - will be ignored for PNG)
                f"-IPTC:Caption-Abstract={title}",
                f"-IPTC:ObjectName={title}",
                f"-IPTC:By-line={creator}",
                f"-IPTC:Keywords={self.config.school_keywords}",
                # XMP tags (universal - works for PNG, JPEG, TIFF, etc.)
                f"-XMP:Description={title}",
                f"-XMP:Title={title}",
                f"-XMP:Creator={creator}",
                f"-XMP:Subject={self.config.school_keywords}",
                image_path,
            ]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if result.stderr:
                self.logger.debug(f"Exiftool output: {result.stderr}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(
                f"Failed to set metadata: {e.stderr if e.stderr else str(e)}"
            )
            # Don't raise - metadata is optional

    def download_and_embed_metadata(self, photo_data: Dict[str, Any]) -> Optional[Path]:
        """
        Download photo and embed metadata
        Returns the path to the downloaded photo or None if it already exists
        """
        try:
            photo_url = photo_data["original_photo_url"]
            description = BeautifulSoup(photo_data["html"], "html.parser").get_text()
            creator = BeautifulSoup(photo_data["author"], "html.parser").get_text()
            created_at = datetime.fromisoformat(photo_data["created_at"].rstrip("Z"))
            photo_id = photo_data["id"]

            # Determine file extension from URL
            # Extract extension from URL path (before query parameters)
            url_path = photo_url.split("?")[0]  # Remove query parameters
            url_ext = url_path.split(".")[-1].lower() if "." in url_path else "jpg"
            self.logger.debug(
                f"Photo {photo_id}: URL={photo_url}, detected extension={url_ext}"
            )
            # Validate extension
            valid_extensions = [
                "jpg",
                "jpeg",
                "png",
                "gif",
                "tiff",
                "tif",
                "bmp",
                "webp",
            ]
            if url_ext not in valid_extensions:
                self.logger.warning(
                    f"Photo {photo_id}: Unrecognized file extension '{url_ext}', defaulting to 'jpg'"
                )
                url_ext = "jpg"

            # Format filename with date and ID
            date_str = created_at.strftime("%Y-%m-%d")
            image_path = (
                Path(self.config.output_dir) / f"{date_str}_{photo_id}.{url_ext}"
            )

            # Check if photo already exists
            if image_path.exists():
                self.logger.info(f"Photo {photo_id} already exists, skipping")
                return None

            # Download photo
            response = self.session.get(photo_url)
            response.raise_for_status()

            # Detect actual image format from content
            kind = filetype.guess(response.content)
            if kind is None or not kind.mime.startswith("image/"):
                self.logger.warning(
                    f"Skipping photo {photo_id}: not a valid image file"
                )
                return None

            # Get the correct extension from the actual file content
            actual_ext = kind.extension
            self.logger.debug(
                f"Photo {photo_id}: URL extension={url_ext}, actual format={actual_ext}"
            )

            # Normalize extensions (jpeg and jpg are the same, tiff and tif are the same)
            def normalize_ext(ext):
                if ext in ["jpeg", "jpg"]:
                    return "jpg"
                elif ext in ["tiff", "tif"]:
                    return "tif"
                return ext

            url_ext_normalized = normalize_ext(url_ext)
            actual_ext_normalized = normalize_ext(actual_ext)

            # If the actual format differs from URL extension, use the actual one
            if actual_ext_normalized != url_ext_normalized:
                self.logger.warning(
                    f"Photo {photo_id}: URL extension '{url_ext}' doesn't match "
                    f"actual format '{actual_ext}', using '{actual_ext}'"
                )
                image_path = (
                    Path(self.config.output_dir) / f"{date_str}_{photo_id}.{actual_ext}"
                )

                # Check again if photo with correct extension exists
                if image_path.exists():
                    self.logger.info(
                        f"Photo {photo_id} already exists with correct extension, skipping"
                    )
                    return None

            with open(image_path, "wb") as file:
                file.write(response.content)

            # Set all metadata (description, creator, GPS, date) for all formats using exiftool
            self.set_metadata(str(image_path), description, creator, created_at)

            # Set file timestamps
            timestamp = created_at.timestamp()
            os.utime(image_path, (timestamp, timestamp))

            self.logger.info(f"Successfully downloaded and processed photo {photo_id}")
            return image_path

        except Exception as e:
            self.logger.error(
                f"Failed to process photo {photo_data.get('id', 'unknown')}: {str(e)}"
            )
            raise

    def download_all_photos(self) -> Dict[str, Any]:
        """
        Download all available photos
        Returns a dict with download statistics, photo paths, and metadata
        """
        photos = self.crawl_all_posts()
        downloaded_items = []

        self.logger.info(f"Processing {len(photos)} posts")

        for photo_data in photos:
            try:
                result = self.download_and_embed_metadata(photo_data)
                if result:
                    # Extract description from HTML
                    description = (
                        BeautifulSoup(photo_data["html"], "html.parser")
                        .get_text()
                        .strip()
                    )
                    downloaded_items.append(
                        {"path": result, "description": description}
                    )
            except Exception as e:
                self.logger.error(f"Failed to download photo: {str(e)}")
                # Continue with other photos

        downloaded_count = len(downloaded_items)
        self.logger.info(f"Downloaded {downloaded_count} new photos")

        return {
            "downloaded_count": downloaded_count,
            "total_posts": len(photos),
            "downloaded_items": downloaded_items,
        }
