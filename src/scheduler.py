"""
Cron scheduler for periodic photo downloads
Supports configurable download schedules
"""

import logging
import schedule
import time
from typing import Callable
from datetime import datetime


class Scheduler:
    """Scheduler for running downloads on a schedule"""

    def __init__(self, download_func: Callable[[], None]):
        """
        Initialize the scheduler

        Args:
            download_func: Function to call on each scheduled run
        """
        self.logger = logging.getLogger('Scheduler')
        self.download_func = download_func
        self.running = False

    def run_job(self):
        """Run the download job with error handling"""
        try:
            self.logger.info(f"Starting scheduled download at {datetime.now()}")
            self.download_func()
            self.logger.info(f"Completed scheduled download at {datetime.now()}")
        except Exception as e:
            self.logger.error(f"Error during scheduled download: {str(e)}", exc_info=True)

    def start(self, schedule_spec: str = "daily"):
        """
        Start the scheduler

        Args:
            schedule_spec: Schedule specification (e.g., "hourly", "daily", "weekly",
                          or cron-like "every 6 hours", "every day at 10:30")
        """
        self.running = True
        self.logger.info(f"Starting scheduler with schedule: {schedule_spec}")

        # Parse schedule specification and set up schedule
        if schedule_spec == "hourly":
            schedule.every().hour.do(self.run_job)
        elif schedule_spec == "daily":
            schedule.every().day.at("02:00").do(self.run_job)
        elif schedule_spec == "weekly":
            schedule.every().week.do(self.run_job)
        elif "every" in schedule_spec.lower():
            # Parse custom schedule like "every 6 hours" or "every day at 10:30"
            self._parse_custom_schedule(schedule_spec)
        else:
            self.logger.warning(f"Unknown schedule spec: {schedule_spec}, defaulting to daily")
            schedule.every().day.at("02:00").do(self.run_job)

        # Run immediately on start
        self.logger.info("Running initial download...")
        self.run_job()

        # Main scheduler loop
        self.logger.info("Scheduler started, waiting for scheduled runs...")
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _parse_custom_schedule(self, schedule_spec: str):
        """Parse custom schedule specifications"""
        spec_lower = schedule_spec.lower()

        # Handle "every X hours"
        if "hour" in spec_lower:
            try:
                hours = int(''.join(filter(str.isdigit, spec_lower.split("hour")[0])))
                schedule.every(hours).hours.do(self.run_job)
                self.logger.info(f"Scheduled to run every {hours} hours")
            except ValueError:
                self.logger.error(f"Could not parse hours from: {schedule_spec}")
                schedule.every().hour.do(self.run_job)

        # Handle "every X minutes"
        elif "minute" in spec_lower:
            try:
                minutes = int(''.join(filter(str.isdigit, spec_lower.split("minute")[0])))
                schedule.every(minutes).minutes.do(self.run_job)
                self.logger.info(f"Scheduled to run every {minutes} minutes")
            except ValueError:
                self.logger.error(f"Could not parse minutes from: {schedule_spec}")
                schedule.every().hour.do(self.run_job)

        # Handle "every day at HH:MM"
        elif "day at" in spec_lower:
            try:
                time_str = spec_lower.split("at")[-1].strip()
                schedule.every().day.at(time_str).do(self.run_job)
                self.logger.info(f"Scheduled to run every day at {time_str}")
            except Exception as e:
                self.logger.error(f"Could not parse time from: {schedule_spec}, error: {e}")
                schedule.every().day.at("02:00").do(self.run_job)

        else:
            self.logger.warning(f"Unknown custom schedule: {schedule_spec}, defaulting to daily")
            schedule.every().day.at("02:00").do(self.run_job)

    def stop(self):
        """Stop the scheduler"""
        self.logger.info("Stopping scheduler...")
        self.running = False
        schedule.clear()
