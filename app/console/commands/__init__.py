"""
Console Commands
Laravel-like command structure for FastAPI Boilerplate
"""

import click

from app.console.commands.cache import clear_cache
from app.console.commands.database import db_create, db_drop
from app.console.commands.key_generate import key_generate
from app.console.commands.install import install
from app.console.commands.logs import clear_logs, view_logs
from app.console.commands.make import (
    make_controller,
    make_exception,
    make_middleware,
    make_model,
    make_repository,
    make_schema,
    make_seeder,
    make_service,
    make_validator,
)
from app.console.commands.migration import (
    make_migration,
    migrate,
    migrate_refresh,
    migrate_reset,
    migrate_rollback,
    migrate_status,
)
from app.console.commands.schedule import schedule_list, schedule_run
from app.console.commands.seeder import db_refresh, db_seed
from app.console.commands.serve import serve
from app.console.commands.test import test
from app.console.commands.user import list_users, promote_user


@click.group()
def app():
    """FastAPI Boilerplate CLI"""
    pass


# Register all commands
app.add_command(serve)
app.add_command(install)
app.add_command(key_generate)
app.add_command(make_migration)
app.add_command(migrate)
app.add_command(migrate_status)
app.add_command(migrate_rollback)
app.add_command(migrate_reset)
app.add_command(migrate_refresh)
app.add_command(make_model)
app.add_command(make_controller)
app.add_command(make_service)
app.add_command(make_schema)
app.add_command(test)
app.add_command(clear_cache)
app.add_command(view_logs)
app.add_command(clear_logs)
app.add_command(make_middleware)
app.add_command(make_exception)
app.add_command(make_validator)
app.add_command(make_repository)
app.add_command(make_seeder)
app.add_command(db_seed)
app.add_command(db_refresh)
app.add_command(db_create)
app.add_command(db_drop)
app.add_command(schedule_run)
app.add_command(schedule_list)
app.add_command(promote_user)
app.add_command(list_users)

__all__ = ["app"]
