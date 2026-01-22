"""Schedule commands"""

import time

import click


@click.command(name="schedule:run")
def schedule_run():
    """Run the scheduled tasks (similar to Laravel's schedule:run)"""
    from app.console.kernel import schedule_tasks
    from app.core.scheduler import get_scheduler

    click.echo("Loading scheduled tasks...")

    # Define tasks
    schedule_tasks()

    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()

    click.echo("Scheduler started. Press Ctrl+C to stop.")

    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping scheduler...")
        scheduler.shutdown()
        click.echo("Scheduler stopped.")


@click.command(name="schedule:list")
def schedule_list():
    """List all scheduled tasks"""
    from app.console.kernel import schedule_tasks
    from app.core.scheduler import get_scheduler

    # Define tasks
    schedule_tasks()

    scheduler = get_scheduler()
    jobs = scheduler.get_jobs()

    if not jobs:
        click.echo("No scheduled tasks found.")
        return

    click.echo(f"\nFound {len(jobs)} scheduled task(s):\n")
    for job in jobs:
        click.echo(f"  - {job.id}")
        click.echo(f"    Trigger: {job.trigger}")
        click.echo(f"    Next run: {job.next_run_time}")
        click.echo()
