"""Migration commands"""

import os

import click


@click.command(name="make:migration")
@click.argument("message", required=False)
def make_migration(message: str = None):
    """Create a new database migration"""
    if not message:
        message = click.prompt("Enter migration message")
    os.system(f'alembic revision --autogenerate -m "{message}"')


@click.command(name="migrate")
def migrate():
    """Run database migrations"""
    os.system("alembic upgrade head")


@click.command(name="migrate:status")
def migrate_status():
    """Show the status of database migrations"""
    os.system("alembic current")


@click.command(name="migrate:rollback")
def migrate_rollback():
    """Rollback the last database migration"""
    os.system("alembic downgrade -1")


@click.command(name="migrate:reset")
def migrate_reset():
    """Reset database (rollback all migrations)"""
    os.system("alembic downgrade base")
    click.echo("Database reset successfully!")


@click.command(name="migrate:refresh")
def migrate_refresh():
    """Refresh database (rollback + migrate)"""
    os.system("alembic downgrade base")
    os.system("alembic upgrade head")
    click.echo("Database refreshed successfully!")
