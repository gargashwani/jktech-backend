"""
Database Management Commands
Similar to Laravel's database commands.
"""

import sys

import click

from config import settings


@click.command()
@click.option(
    "--database", default=None, help="Database name (defaults to DB_DATABASE from .env)"
)
def db_create(database):
    """Create the database if it doesn't exist."""
    db_name = database or settings.DB_DATABASE
    connection = settings.DB_CONNECTION.lower()

    if connection in ["postgresql", "postgres"]:
        try:
            import psycopg2
            from psycopg2 import sql

            # Connect to PostgreSQL server (not to a specific database)
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
                database="postgres",  # Connect to default database
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()

            if exists:
                click.echo(f"✓ Database '{db_name}' already exists")
            else:
                # Create database
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                )
                click.echo(f"✓ Database '{db_name}' created successfully")

            cursor.close()
            conn.close()

        except ImportError:
            click.echo(
                "✗ psycopg2 is required for PostgreSQL. Install with: pip install psycopg2-binary"
            )
            sys.exit(1)
        except psycopg2.OperationalError as e:
            click.echo(f"✗ Error connecting to PostgreSQL: {e}")
            click.echo("\nPlease ensure:")
            click.echo("  1. PostgreSQL is running")
            click.echo("  2. Connection settings in .env are correct")
            sys.exit(1)
        except Exception as e:
            click.echo(f"✗ Error: {e}")
            sys.exit(1)

    elif connection in ["mysql", "mysql+pymysql"]:
        try:
            import pymysql

            # Connect to MySQL server (not to a specific database)
            conn = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
            )
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            exists = cursor.fetchone()

            if exists:
                click.echo(f"✓ Database '{db_name}' already exists")
            else:
                # Create database
                cursor.execute(f"CREATE DATABASE `{db_name}`")
                click.echo(f"✓ Database '{db_name}' created successfully")

            cursor.close()
            conn.close()

        except ImportError:
            click.echo(
                "✗ pymysql is required for MySQL. Install with: pip install pymysql"
            )
            sys.exit(1)
        except Exception as e:
            click.echo(f"✗ Error: {e}")
            sys.exit(1)

    else:
        click.echo(f"✗ Unsupported database connection: {connection}")
        click.echo("Supported: postgresql, mysql")
        sys.exit(1)


@click.command(name="db:drop")
@click.option(
    "--database", default=None, help="Database name (defaults to DB_DATABASE from .env)"
)
@click.confirmation_option(prompt="Are you sure you want to drop the database?")
def db_drop(database):
    """Drop the database."""
    db_name = database or settings.DB_DATABASE
    connection = settings.DB_CONNECTION.lower()

    if connection in ["postgresql", "postgres"]:
        try:
            import psycopg2
            from psycopg2 import sql

            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
                database="postgres",
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Drop database
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
            )
            click.echo(f"✓ Database '{db_name}' dropped successfully")

            cursor.close()
            conn.close()

        except Exception as e:
            click.echo(f"✗ Error: {e}")
            sys.exit(1)

    elif connection in ["mysql", "mysql+pymysql"]:
        try:
            import pymysql

            conn = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
            )
            cursor = conn.cursor()

            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            click.echo(f"✓ Database '{db_name}' dropped successfully")

            cursor.close()
            conn.close()

        except Exception as e:
            click.echo(f"✗ Error: {e}")
            sys.exit(1)

    else:
        click.echo(f"✗ Unsupported database connection: {connection}")
        sys.exit(1)
