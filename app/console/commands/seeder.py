"""Seeder commands"""

from pathlib import Path

import click


@click.command(name="db:seed")
@click.option("--seeder", help="Run specific seeder")
def db_seed(seeder: str = None):
    """Run database seeders"""
    seeders_path = Path("database/seeders")
    if not seeders_path.exists():
        click.echo("No seeders found!")
        return

    if seeder:
        # Run specific seeder
        seeder_file = seeders_path / f"{seeder.lower()}.py"
        if not seeder_file.exists():
            click.echo(f"Seeder {seeder} not found!")
            return

        # Import and run the seeder
        seeder_module = f"database.seeders.{seeder.lower()}"
        seeder_class = seeder
        try:
            module = __import__(seeder_module, fromlist=[seeder_class])
            seeder_instance = getattr(module, seeder_class)()
            count = seeder_instance.run()
            click.echo(f"Seeder {seeder} ran successfully! Created {count} records.")
        except Exception as e:
            click.echo(f"Error running seeder {seeder}: {str(e)}")
    else:
        # Run all seeders
        for seeder_file in seeders_path.glob("*.py"):
            if seeder_file.name == "__init__.py":
                continue

            seeder_name = seeder_file.stem.capitalize()
            seeder_module = f"database.seeders.{seeder_file.stem}"
            try:
                module = __import__(seeder_module, fromlist=[seeder_name])
                seeder_instance = getattr(module, seeder_name)()
                count = seeder_instance.run()
                click.echo(
                    f"Seeder {seeder_name} ran successfully! Created {count} records."
                )
            except Exception as e:
                click.echo(f"Error running seeder {seeder_name}: {str(e)}")


@click.command(name="db:refresh")
def db_refresh():
    """Refresh database (migrate:fresh + seed)"""
    import os

    # Run fresh migrations
    os.system("alembic downgrade base")
    os.system("alembic upgrade head")

    # Run seeders
    os.system("./artisan db:seed")

    click.echo("Database refreshed successfully!")
