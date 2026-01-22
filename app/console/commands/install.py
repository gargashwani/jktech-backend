"""Install command"""

import os
import shutil
from pathlib import Path

import click


@click.command(name="install")
@click.option("--force", is_flag=True, help="Force the installation even if .env exists")
def install(force: bool):
    """Set up the application for the first time"""
    click.echo("🚀 Starting FastAPI Boilerplate installation...")

    # 1. Setup .env
    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if env_path.exists() and not force:
        click.echo("⚠️  .env file already exists. Use --force to overwrite.")
    else:
        if env_example_path.exists():
            shutil.copy(".env.example", ".env")
            click.echo("✅ Created .env from .env.example")
        else:
            click.echo("❌ .env.example not found. Skipping .env creation.")

    # 2. Generate App Key
    click.echo("🔑 Generating application key...")
    from app.console.commands.key_generate import generate_and_persist_key
    key = generate_and_persist_key()
    click.echo(f"✅ Application key generated and saved to .env")

    # 3. Run Migrations
    if click.confirm("Do you want to run database migrations?", default=True):
        click.echo("inst Running migrations...")
        os.system("alembic upgrade head")
        click.echo("✅ Migrations completed.")

    # 4. Create Storage Directories
    click.echo("📁 Creating storage directories...")
    Path("storage/app").mkdir(parents=True, exist_ok=True)
    Path("public/storage").mkdir(parents=True, exist_ok=True)
    click.echo("✅ Storage directories created.")

    click.echo("\n✨ Installation complete! You're ready to go.")
    click.echo("Run 'python artisan serve' to start the development server.")
