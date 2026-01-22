"""Log commands"""

from pathlib import Path

import click


@click.command(name="logs:view")
def view_logs():
    """View application logs"""
    log_path = Path("logs/app.log")
    if not log_path.exists():
        click.echo("No logs found!")
        return

    with open(log_path) as f:
        click.echo(f.read())


@click.command(name="logs:clear")
def clear_logs():
    """Clear application logs"""
    log_path = Path("logs/app.log")
    if log_path.exists():
        log_path.write_text("")
        click.echo("Logs cleared successfully!")
    else:
        click.echo("No logs found!")
