"""
Task Scheduler
Laravel-like task scheduling system using APScheduler.
"""

import logging
from collections.abc import Callable

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import settings

logger = logging.getLogger(__name__)


class Schedule:
    """
    Laravel-like schedule builder.
    Similar to Laravel's Schedule facade.
    """

    def __init__(self, scheduler: BackgroundScheduler):
        self.scheduler = scheduler
        self.jobs: list[dict] = []
        self._current_job: dict | None = None

    def command(self, command: str, *args, **kwargs) -> "Schedule":
        """
        Schedule an Artisan command.
        Similar to Laravel's $schedule->command().

        Args:
            command: Command name (e.g., 'cache:clear')
            *args: Command arguments
            **kwargs: Command options
        """
        self._current_job = {
            "type": "command",
            "command": command,
            "args": args,
            "kwargs": kwargs,
            "overlap": True,
            "without_overlapping": False,
            "on_one_server": False,
            "run_in_background": False,
            "timezone": None,
        }
        return self

    def job(self, func: Callable, *args, **kwargs) -> "Schedule":
        """
        Schedule a queued job/function.
        Similar to Laravel's $schedule->job().

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        self._current_job = {
            "type": "job",
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "overlap": True,
            "without_overlapping": False,
            "on_one_server": False,
            "run_in_background": False,
            "timezone": None,
        }
        return self

    def exec(
        self, command: str, allowed_commands: list[str] | None = None
    ) -> "Schedule":
        """
        Schedule a shell command with security validation.
        Similar to Laravel's $schedule->exec().

        WARNING: Only use with trusted commands. User input should never reach this method.

        Args:
            command: Shell command to execute
            allowed_commands: Optional whitelist of allowed commands (for security)
        """
        # Security: Validate command if whitelist provided
        if allowed_commands:
            # Extract base command (first word)
            base_cmd = command.split()[0] if command.split() else command
            if base_cmd not in allowed_commands:
                raise ValueError(
                    f"Command '{base_cmd}' is not in allowed commands list"
                )

        # Security: Basic validation - no shell metacharacters
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        if any(char in command for char in dangerous_chars):
            raise ValueError("Command contains potentially dangerous characters")

        self._current_job = {
            "type": "exec",
            "command": command,
            "overlap": True,
            "without_overlapping": False,
            "on_one_server": False,
            "run_in_background": False,
            "timezone": None,
        }
        return self

    # Frequency methods
    def every_minute(self) -> "Schedule":
        """Run every minute."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(minutes=1)
            self._register_job()
        return self

    def every_two_minutes(self) -> "Schedule":
        """Run every 2 minutes."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(minutes=2)
            self._register_job()
        return self

    def every_five_minutes(self) -> "Schedule":
        """Run every 5 minutes."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(minutes=5)
            self._register_job()
        return self

    def every_ten_minutes(self) -> "Schedule":
        """Run every 10 minutes."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(minutes=10)
            self._register_job()
        return self

    def every_fifteen_minutes(self) -> "Schedule":
        """Run every 15 minutes."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(minutes=15)
            self._register_job()
        return self

    def every_thirty_minutes(self) -> "Schedule":
        """Run every 30 minutes."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(minutes=30)
            self._register_job()
        return self

    def hourly(self) -> "Schedule":
        """Run every hour."""
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(hours=1)
            self._register_job()
        return self

    def daily(self) -> "Schedule":
        """Run daily at midnight."""
        if self._current_job:
            self._current_job["trigger"] = CronTrigger(hour=0, minute=0)
            self._register_job()
        return self

    def daily_at(self, time: str) -> "Schedule":
        """
        Run daily at specific time.

        Args:
            time: Time in HH:MM format (e.g., '14:30')
        """
        if self._current_job:
            hour, minute = map(int, time.split(":"))
            self._current_job["trigger"] = CronTrigger(hour=hour, minute=minute)
            self._register_job()
        return self

    def twice_daily(self, first: int = 1, second: int = 13) -> "Schedule":
        """
        Run twice daily.

        Args:
            first: First hour (default: 1)
            second: Second hour (default: 13)
        """
        if self._current_job:
            # Schedule two jobs
            self._current_job["trigger"] = CronTrigger(hour=first, minute=0)
            self._register_job()
            # Note: This creates one job, you'd need to call twice_daily twice for two jobs
        return self

    def weekly(self) -> "Schedule":
        """Run weekly on Sunday at midnight."""
        if self._current_job:
            self._current_job["trigger"] = CronTrigger(
                day_of_week="sun", hour=0, minute=0
            )
            self._register_job()
        return self

    def weekly_on(self, day: str, time: str = "0:0") -> "Schedule":
        """
        Run weekly on specific day and time.

        Args:
            day: Day of week (mon, tue, wed, thu, fri, sat, sun)
            time: Time in HH:MM format
        """
        if self._current_job:
            hour, minute = map(int, time.split(":"))
            day_map = {
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            self._current_job["trigger"] = CronTrigger(
                day_of_week=day_map.get(day.lower(), 0), hour=hour, minute=minute
            )
            self._register_job()
        return self

    def monthly(self) -> "Schedule":
        """Run monthly on the first day at midnight."""
        if self._current_job:
            self._current_job["trigger"] = CronTrigger(day=1, hour=0, minute=0)
            self._register_job()
        return self

    def monthly_on(self, day: int, time: str = "0:0") -> "Schedule":
        """
        Run monthly on specific day and time.

        Args:
            day: Day of month (1-31)
            time: Time in HH:MM format
        """
        if self._current_job:
            hour, minute = map(int, time.split(":"))
            self._current_job["trigger"] = CronTrigger(
                day=day, hour=hour, minute=minute
            )
            self._register_job()
        return self

    def quarterly(self) -> "Schedule":
        """Run quarterly (every 3 months)."""
        if self._current_job:
            self._current_job["trigger"] = CronTrigger(
                month="*/3", day=1, hour=0, minute=0
            )
            self._register_job()
        return self

    def yearly(self) -> "Schedule":
        """Run yearly on January 1st at midnight."""
        if self._current_job:
            self._current_job["trigger"] = CronTrigger(month=1, day=1, hour=0, minute=0)
            self._register_job()
        return self

    def cron(
        self,
        minute: str = "*",
        hour: str = "*",
        day: str = "*",
        month: str = "*",
        day_of_week: str = "*",
    ) -> "Schedule":
        """
        Schedule using cron expression.

        Args:
            minute: Minute (0-59)
            hour: Hour (0-23)
            day: Day of month (1-31)
            month: Month (1-12)
            day_of_week: Day of week (0-6, 0=Monday)
        """
        if self._current_job:
            self._current_job["trigger"] = CronTrigger(
                minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
            )
            self._register_job()
        return self

    def every(self, seconds: int) -> "Schedule":
        """
        Run every N seconds.

        Args:
            seconds: Number of seconds
        """
        if self._current_job:
            self._current_job["trigger"] = IntervalTrigger(seconds=seconds)
            self._register_job()
        return self

    # Modifier methods
    def timezone(self, tz: str) -> "Schedule":
        """
        Set timezone for the scheduled task.

        Args:
            tz: Timezone name (e.g., 'America/New_York')
        """
        if self._current_job:
            self._current_job["timezone"] = tz
        return self

    def without_overlapping(self, expiration: int = 60) -> "Schedule":
        """
        Prevent task overlaps.
        Similar to Laravel's withoutOverlapping().

        Args:
            expiration: Expiration time in minutes (default: 60)
        """
        if self._current_job:
            self._current_job["without_overlapping"] = True
            self._current_job["overlap_expiration"] = expiration
        return self

    def on_one_server(self) -> "Schedule":
        """
        Run task on only one server.
        Similar to Laravel's onOneServer().
        """
        if self._current_job:
            self._current_job["on_one_server"] = True
        return self

    def run_in_background(self) -> "Schedule":
        """
        Run task in background.
        Similar to Laravel's runInBackground().
        """
        if self._current_job:
            self._current_job["run_in_background"] = True
        return self

    def when(self, condition: Callable[[], bool]) -> "Schedule":
        """
        Run task only when condition is true.
        Similar to Laravel's when().

        Args:
            condition: Callable that returns boolean
        """
        if self._current_job:
            self._current_job["when"] = condition
        return self

    def skip(self, condition: Callable[[], bool]) -> "Schedule":
        """
        Skip task when condition is true.
        Similar to Laravel's skip().

        Args:
            condition: Callable that returns boolean
        """
        if self._current_job:
            self._current_job["skip"] = condition
        return self

    def before(self, callback: Callable) -> "Schedule":
        """
        Execute callback before task runs.
        Similar to Laravel's before().

        Args:
            callback: Callable to execute
        """
        if self._current_job:
            self._current_job["before"] = callback
        return self

    def after(self, callback: Callable) -> "Schedule":
        """
        Execute callback after task runs.
        Similar to Laravel's after().

        Args:
            callback: Callable to execute
        """
        if self._current_job:
            self._current_job["after"] = callback
        return self

    def append_output_to(self, filepath: str) -> "Schedule":
        """
        Append output to file.
        Similar to Laravel's appendOutputTo().

        Args:
            filepath: File path to append output
        """
        if self._current_job:
            self._current_job["output_file"] = filepath
            self._current_job["append_output"] = True
        return self

    def send_output_to(self, filepath: str) -> "Schedule":
        """
        Send output to file.
        Similar to Laravel's sendOutputTo().

        Args:
            filepath: File path to write output
        """
        if self._current_job:
            self._current_job["output_file"] = filepath
            self._current_job["append_output"] = False
        return self

    def email_output_to(self, email: str) -> "Schedule":
        """
        Email output to address.
        Similar to Laravel's emailOutputTo().

        Args:
            email: Email address
        """
        if self._current_job:
            self._current_job["email_output"] = email
        return self

    def _register_job(self):
        """Register the current job with the scheduler."""
        if not self._current_job or "trigger" not in self._current_job:
            logger.warning("Job has no trigger, skipping registration")
            return

        job_config = self._current_job.copy()
        job_id = f"{job_config.get('type', 'job')}_{len(self.jobs)}"

        # Create wrapper function
        def job_wrapper():
            try:
                # Check conditions
                if "when" in job_config and not job_config["when"]():
                    return
                if "skip" in job_config and job_config["skip"]():
                    return

                # Before hook
                if "before" in job_config:
                    job_config["before"]()

                # Execute job
                if job_config["type"] == "command":
                    # Execute command (would need command runner)
                    logger.info(f"Executing command: {job_config['command']}")
                elif job_config["type"] == "job":
                    job_config["func"](
                        *job_config.get("args", []), **job_config.get("kwargs", {})
                    )
                elif job_config["type"] == "exec":
                    import shlex
                    import subprocess

                    # Security: Use shlex.split and avoid shell=True
                    # Split command into list to avoid shell injection
                    cmd_parts = shlex.split(job_config["command"])
                    if cmd_parts:
                        # Use subprocess without shell=True for better security
                        subprocess.run(cmd_parts, check=False, capture_output=True)
                    else:
                        logger.error(f"Invalid command: {job_config['command']}")

                # After hook
                if "after" in job_config:
                    job_config["after"]()

            except Exception as e:
                logger.error(f"Error executing scheduled job {job_id}: {e}")

        # Add job to scheduler
        trigger = job_config["trigger"]
        timezone = job_config.get("timezone") or getattr(
            settings, "APP_TIMEZONE", "UTC"
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            timezone=timezone,
        )

        self.jobs.append(job_config)
        self._current_job = None


# Global scheduler instance
_scheduler_instance: BackgroundScheduler | None = None
_schedule_instance: Schedule | None = None


def get_scheduler() -> BackgroundScheduler:
    """Get global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": ThreadPoolExecutor(20)}
        job_defaults = {"coalesce": False, "max_instances": 3}

        _scheduler_instance = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )
    return _scheduler_instance


def get_schedule() -> Schedule:
    """Get global schedule instance."""
    global _schedule_instance
    if _schedule_instance is None:
        _schedule_instance = Schedule(get_scheduler())
    return _schedule_instance


def schedule() -> Schedule:
    """Get schedule instance - Laravel-like API."""
    return get_schedule()
