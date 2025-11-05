"""
Main entry point for Transparent Classroom Photos Grabber
Supports both CLI mode and cron scheduled mode
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

from .config import Config
from .client import TransparentClassroomClient
from .scheduler import Scheduler
from .telegram_notifier import TelegramNotifier
from .telegram_bot import TelegramBotHandler


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def download_photos(config: Config, telegram_notifier: Optional[TelegramNotifier] = None) -> int:
    """
    Download photos using the provided configuration

    Args:
        config: Configuration object
        telegram_notifier: Optional Telegram notifier for sending updates

    Returns:
        Number of photos downloaded
    """
    logger = logging.getLogger('Main')

    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration. Please check your settings.")
        logger.error(f"Email: {'✓' if config.email else '✗'}")
        logger.error(f"Password: {'✓' if config.password else '✗'}")
        logger.error(f"School ID: {'✓' if config.school_id > 0 else '✗'}")
        logger.error(f"Child ID: {'✓' if config.child_id > 0 else '✗'}")
        sys.exit(1)

    logger.info("Starting Transparent Classroom Photos Grabber")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info(f"Cache directory: {config.cache_dir}")

    # Create client and download photos
    try:
        client = TransparentClassroomClient(config)
        result = client.download_all_photos()
        
        downloaded_count = result['downloaded_count']
        total_posts = result['total_posts']
        photo_items = result['downloaded_items']
        
        logger.info(f"Successfully downloaded {downloaded_count} new photos")
        
        # Send Telegram notification if configured
        if telegram_notifier:
            logger.info("Sending Telegram notification...")
            telegram_notifier.send_download_summary(downloaded_count, total_posts, photo_items)
        
        return downloaded_count
    except Exception as e:
        logger.error(f"Failed to download photos: {str(e)}", exc_info=True)
        
        # Send error notification to Telegram if configured
        if telegram_notifier:
            telegram_notifier.send_message(f"❌ *Photo Sync Failed*\n\nError: {str(e)}")
        
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Download photos from Transparent Classroom',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once in CLI mode
  tc-photo-grabber

  # Run with custom output directory
  tc-photo-grabber --output /path/to/photos

  # Run in cron mode with daily schedule
  tc-photo-grabber --cron --schedule daily

  # Run in cron mode with custom schedule
  tc-photo-grabber --cron --schedule "every 6 hours"
  tc-photo-grabber --cron --schedule "every day at 10:30"

  # Run in cron mode with cron expression
  tc-photo-grabber --cron --cron-expression "0 2 * * *"
  tc-photo-grabber --cron --cron-expression "*/30 * * * *"

  # Run in cron mode and execute immediately on startup
  tc-photo-grabber --cron --cron-expression "0 2 * * *" --run-immediately

  # Show current configuration
  tc-photo-grabber --show-config

  # Verbose output for debugging
  tc-photo-grabber --verbose
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for downloaded photos (default: ./photos)'
    )

    parser.add_argument(
        '--cache-dir',
        type=str,
        help='Cache directory for API responses (default: ./cache)'
    )

    parser.add_argument(
        '--cron',
        action='store_true',
        help='Run in cron mode with scheduled downloads'
    )

    parser.add_argument(
        '--schedule',
        type=str,
        default='daily',
        help='Schedule for cron mode (default: daily). '
             'Options: hourly, daily, weekly, "every X hours", "every day at HH:MM"'
    )

    parser.add_argument(
        '--cron-expression',
        type=str,
        help='Cron expression for scheduling (e.g., "0 2 * * *" for daily at 2am). '
             'Takes precedence over --schedule. Can also be set via CRON_EXPRESSION env var.'
    )

    parser.add_argument(
        '--run-immediately',
        action='store_true',
        help='In cron mode, run the job immediately on startup before waiting for schedule. '
             'Can also be set via RUN_IMMEDIATELY env var (true/1/yes)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file (YAML format)'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current configuration and exit'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output for debugging'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - show what would be downloaded without downloading'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger('Main')

    # Load environment variables from .env file
    load_dotenv()

    # Load configuration
    try:
        if args.config:
            config = Config.from_file(Path(args.config))
        else:
            config = Config.load()
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        logger.info("Please set environment variables or create a config file.")
        logger.info("Required variables: TC_EMAIL, TC_PASSWORD, SCHOOL, CHILD")
        sys.exit(1)

    # Override config with command-line arguments
    if args.output:
        config.output_dir = args.output
    if args.cache_dir:
        config.cache_dir = args.cache_dir

    # Show config if requested
    if args.show_config:
        print("\n=== Current Configuration ===")
        print(f"Email: {config.email}")
        print(f"School ID: {config.school_id}")
        print(f"Child ID: {config.child_id}")
        print(f"School Location: {config.school_lat}, {config.school_lng}")
        print(f"School Keywords: {config.school_keywords}")
        print(f"Output Directory: {config.output_dir}")
        print(f"Cache Directory: {config.cache_dir}")
        print(f"Cache Timeout: {config.cache_timeout}s")
        print()
        sys.exit(0)

    # Dry run mode
    if args.dry_run:
        logger.info("DRY RUN MODE - No photos will be downloaded")
        
        # If in cron mode, show scheduling info
        if args.cron:
            from croniter import croniter
            from datetime import datetime
            
            cron_expr = args.cron_expression or config.cron_expression
            print(f"\n=== Cron Schedule Information ===")
            
            if cron_expr:
                print(f"Cron Expression: {cron_expr}")
                try:
                    cron = croniter(cron_expr, datetime.now())
                    print(f"Next 5 scheduled runs:")
                    for i in range(5):
                        next_run = cron.get_next(datetime)
                        print(f"  {i+1}. {next_run.strftime('%Y-%m-%d %H:%M:%S %A')}")
                except Exception as e:
                    print(f"Error parsing cron expression: {e}")
            else:
                print(f"Schedule: {args.schedule}")
                print(f"(Simple schedules don't support dry-run preview)")
            print()
        
        # Run the actual dry-run check
        client = TransparentClassroomClient(config)
        photos = client.crawl_all_posts()
        print(f"\n=== Dry Run Results ===")
        print(f"Found {len(photos)} posts")
        print(f"Would save to: {config.output_dir}")
        print()
        sys.exit(0)

    # Initialize Telegram bot and notifier if configured
    telegram_notifier = None
    telegram_bot = None
    if config.telegram_bot_token and config.telegram_chat_id:
        logger.info("Initializing Telegram bot and notifier...")
        
        # Initialize bot handler for commands
        telegram_bot = TelegramBotHandler(
            config.telegram_bot_token, 
            config.telegram_chat_id, 
            config.cache_dir
        )
        
        # Initialize notifier for sending messages/photos
        telegram_notifier = TelegramNotifier(
            config.telegram_bot_token, 
            config.telegram_chat_id,
            telegram_bot
        )
        
        # Test connection
        if telegram_notifier.test_connection():
            logger.info("Telegram initialized successfully")
        else:
            logger.warning("Telegram connection test failed, notifications may not work")
    
    # Run in cron mode or CLI mode
    if args.cron:
        # Determine cron expression from CLI arg, env var, or config
        cron_expr = args.cron_expression or config.cron_expression
        
        if cron_expr:
            logger.info(f"Starting in cron mode with cron expression: {cron_expr}")
        else:
            logger.info(f"Starting in cron mode with schedule: {args.schedule}")

        def download_job():
            """Wrapper for scheduler"""
            download_photos(config, telegram_notifier)

        scheduler = Scheduler(download_job, telegram_bot)
        try:
            # Use CLI arg if provided, otherwise use config value
            run_now = args.run_immediately or config.run_immediately
            scheduler.start(
                schedule_spec=args.schedule, 
                cron_expression=cron_expr,
                run_immediately=run_now,
                timezone=config.timezone
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            scheduler.stop()
            sys.exit(0)
    else:
        # CLI mode - run once
        download_photos(config, telegram_notifier)


if __name__ == '__main__':
    main()
