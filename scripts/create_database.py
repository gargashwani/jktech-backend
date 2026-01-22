#!/usr/bin/env python3
"""
Create database if it doesn't exist.
Similar to Laravel's database creation.
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2 import sql

from config import settings


def create_database():
    """Create the database if it doesn't exist."""
    # Connect to PostgreSQL server (not to a specific database)
    try:
        # Connect to default 'postgres' database
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
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_DATABASE,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"✓ Database '{settings.DB_DATABASE}' already exists")
        else:
            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings.DB_DATABASE)
                )
            )
            print(f"✓ Database '{settings.DB_DATABASE}' created successfully")

        cursor.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        print(f"✗ Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Connection settings in .env are correct:")
        print(f"     DB_HOST={settings.DB_HOST}")
        print(f"     DB_PORT={settings.DB_PORT}")
        print(f"     DB_USERNAME={settings.DB_USERNAME}")
        print(f"     DB_DATABASE={settings.DB_DATABASE}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
