"""
Cron scheduler for periodic photo downloads
Supports configurable download schedules and cron expressions
"""

import logging
import schedule
import time
from typing import Callable, Optional
from datetime import datetime
from croniter import croniter
from zoneinfo import ZoneInfo


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

    def start(self, schedule_spec: str = "daily", cron_expression: Optional[str] = None, run_immediately: bool = False, timezone: str = "UTC"):
        """
        Start the scheduler

        Args:
            schedule_spec: Schedule specification (e.g., "hourly", "daily", "weekly",
                          or cron-like "every 6 hours", "every day at 10:30")
            cron_expression: Optional cron expression (e.g., "0 2 * * *" for daily at 2am).
                           If provided, this takes precedence over schedule_spec.
            run_immediately: If True, run the job immediately on startup before waiting for schedule.
                           Default is False.
            timezone: Timezone for cron scheduling (e.g., "America/Chicago", "UTC").
                     Default is "UTC".
        """
        self.running = True
        self._timezone = timezone
        
        # If cron expression is provided, use it
        if cron_expression:
            if self._is_valid_cron(cron_expression):
                self.logger.info(f"Starting scheduler with cron expression: {cron_expression} (timezone: {timezone})")
                self._use_cron_expression = True
                self._cron_expression = cron_expression
                # Use timezone-aware datetime
                try:
                    tz = ZoneInfo(timezone)
                    now = datetime.now(tz)
                    self._cron_iter = croniter(cron_expression, now)
                except Exception as e:
                    self.logger.error(f"Invalid timezone '{timezone}': {e}, falling back to UTC")
                    now = datetime.now(ZoneInfo("UTC"))
                    self._cron_iter = croniter(cron_expression, now)
                    self._timezone = "UTC"
            else:
                self.logger.error(f"Invalid cron expression: {cron_expression}, falling back to schedule_spec")
                self._use_cron_expression = False
                self._setup_schedule_spec(schedule_spec)
        else:
            self.logger.info(f"Starting scheduler with schedule: {schedule_spec}")
            self._use_cron_expression = False
            self._setup_schedule_spec(schedule_spec)

        # Optionally run immediately on start
        if run_immediately:
            self.logger.info("Running immediate download on startup...")
            self.run_job()

        # Main scheduler loop - wait for first scheduled run
        self.logger.info("Scheduler started, waiting for scheduled runs...")
        if self._use_cron_expression:
            self._run_cron_loop()
        else:
            self._run_schedule_loop()

    def _run_schedule_loop(self):
        """Run the main loop for schedule-based scheduling"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _run_cron_loop(self):
        """Run the main loop for cron expression-based scheduling"""
        tz = ZoneInfo(self._timezone)
        while self.running:
            next_run = self._cron_iter.get_next(datetime)
            now = datetime.now(tz)
            sleep_seconds = (next_run - now).total_seconds()
            
            if sleep_seconds > 0:
                self.logger.info(f"Next run scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')} (sleeping for {sleep_seconds:.0f} seconds)")
                # Sleep in smaller intervals to allow for graceful shutdown
                while sleep_seconds > 0 and self.running:
                    sleep_time = min(60, sleep_seconds)
                    time.sleep(sleep_time)
                    sleep_seconds -= sleep_time
            
            if self.running:
                self.run_job()

    def _is_valid_cron(self, cron_expression: str) -> bool:
        """Validate a cron expression"""
        try:
            croniter(cron_expression)
            return True
        except (ValueError, KeyError):
            return False

    def _setup_schedule_spec(self, schedule_spec: str):
        """Setup schedule based on schedule specification"""
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
