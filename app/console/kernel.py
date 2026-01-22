"""
Task Scheduler Kernel
Define your scheduled tasks here, similar to Laravel's app/Console/Kernel.php
"""

import logging

from app.core.scheduler import schedule

logger = logging.getLogger(__name__)


def schedule_tasks():
    """
    Define all scheduled tasks here.
    Similar to Laravel's schedule() method in Kernel.php

    Example:
        schedule().command('cache:clear').daily()
        schedule().job(cleanup_old_files).hourly()
        schedule().exec('php artisan backup:run').daily()
    """

    # Example: Run every minute
    # schedule().job(example_task).every_minute()

    # Example: Run daily at midnight
    # schedule().job(cleanup_old_files).daily()

    # Example: Run hourly
    # schedule().job(process_queue).hourly()

    # Example: Run every 5 minutes
    # schedule().job(check_system_health).every_five_minutes()

    # Example: Run daily at specific time
    # schedule().job(send_daily_report).daily_at('09:00')

    # Example: Run weekly on Monday
    # schedule().job(weekly_backup).weekly_on('mon', '02:00')

    # Example: Run monthly
    # schedule().job(monthly_cleanup).monthly()

    # Example: With timezone
    # schedule().job(send_report).daily_at('09:00').timezone('America/New_York')

    # Example: Without overlapping
    # schedule().job(long_running_task).hourly().without_overlapping()

    # Example: On one server only (for multi-server deployments)
    # schedule().job(send_notification).daily().on_one_server()

    # Example: With conditions
    # schedule().job(send_email).daily().when(lambda: some_condition())

    # Example: Skip under conditions
    # schedule().job(backup).daily().skip(lambda: maintenance_mode())

    # Example: With output
    # schedule().job(generate_report).daily().append_output_to('logs/reports.log')

    logger.info(f"Scheduled {len(schedule().jobs)} tasks")


def example_task():
    """Example scheduled task."""
    logger.info("Running example scheduled task")


def cleanup_old_files():
    """Clean up old files."""
    logger.info("Cleaning up old files")
    # Your cleanup logic here


def process_queue():
    """Process queued items."""
    logger.info("Processing queue")
    # Your queue processing logic here


def check_system_health():
    """Check system health."""
    logger.info("Checking system health")
    # Your health check logic here


def send_daily_report():
    """Send daily report."""
    logger.info("Sending daily report")
    # Your report sending logic here


def weekly_backup():
    """Weekly backup."""
    logger.info("Running weekly backup")
    # Your backup logic here


def monthly_cleanup():
    """Monthly cleanup."""
    logger.info("Running monthly cleanup")
    # Your cleanup logic here


def long_running_task():
    """Long running task."""
    logger.info("Running long running task")
    # Your long running task logic here


def send_notification():
    """Send notification."""
    logger.info("Sending notification")
    # Your notification logic here


def send_email():
    """Send email."""
    logger.info("Sending email")
    # Your email sending logic here


def backup():
    """Backup task."""
    logger.info("Running backup")
    # Your backup logic here


def generate_report():
    """Generate report."""
    logger.info("Generating report")
    # Your report generation logic here
