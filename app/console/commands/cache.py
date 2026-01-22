"""Cache commands"""

import click


@click.command(name="cache:clear")
def clear_cache():
    """Clear the application cache"""
    from app.core.cache import cache

    try:
        # Clear all cache (if using Redis)
        cache().flush()
        click.echo("Cache cleared successfully!")
    except Exception as e:
        click.echo(f"Error clearing cache: {str(e)}")
