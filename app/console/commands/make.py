"""Make commands - Generate various files"""

import os
from pathlib import Path

import click

from app.console.templates.controller import (
    API_CONTROLLER_TEMPLATE,
    BASIC_CONTROLLER_TEMPLATE,
    RESOURCE_CONTROLLER_TEMPLATE,
)
from app.console.templates.model import MODEL_TEMPLATE
from app.console.templates.seeder import SEEDER_TEMPLATE
from app.console.templates.service import (
    SERVICE_TEMPLATE,
    SERVICE_WITH_INTERFACE_TEMPLATE,
)


@click.command(name="make:model")
@click.argument("name")
@click.option("--migration", is_flag=True, help="Create a migration for the model")
@click.option("--controller", is_flag=True, help="Create a controller for the model")
@click.option(
    "--all",
    is_flag=True,
    help="Create all components (model, migration, controller, service, schema)",
)
def make_model(name: str, migration: bool, controller: bool, all: bool):
    """Create a new model file"""
    model_name = name.lower()
    model_class = name.capitalize()

    # Create models directory if it doesn't exist
    model_path = Path("app/models") / f"{model_name}.py"
    if model_path.exists():
        click.echo(f"Model {name} already exists!")
        return

    model_path.parent.mkdir(parents=True, exist_ok=True)

    # Create model file
    model_content = MODEL_TEMPLATE.format(
        model_name=model_name, model_class=model_class
    )
    model_path.write_text(model_content)
    click.echo(f"Model {name} created successfully!")
    click.echo(f"Model: file://{model_path.absolute()}")

    # Create migration if requested
    if migration or all:
        os.system(f'alembic revision --autogenerate -m "create {model_name} model"')
        migration_path = Path("alembic/versions")
        latest_migration = (
            sorted(migration_path.glob("*.py"))[-1] if migration_path.exists() else None
        )
        if latest_migration:
            click.echo(f"Migration: file://{latest_migration.absolute()}")

    # Create controller if requested
    if controller or all:
        os.system(f"./artisan make:controller {model_class}Controller --resource")

    # Create all components if requested
    if all:
        # Create service
        os.system(f"./artisan make:service {model_class}Service --interface")

        # Create schema
        os.system(f"./artisan make:schema {model_class}")


@click.command(name="make:controller")
@click.argument("name")
@click.option("--resource", is_flag=True, help="Create a resource controller")
@click.option("--api", is_flag=True, help="Create an API controller")
def make_controller(name: str, resource: bool, api: bool):
    """Create a new controller file"""
    # Remove 'Controller' suffix if present
    model_name = name.lower().replace("controller", "")
    model_class = name.replace("Controller", "")
    controller_class = name

    controller_path = Path("app/api/v1/controllers") / f"{name.lower()}.py"
    if controller_path.exists():
        click.echo(f"Controller {name} already exists!")
        return

    # Create controllers directory if it doesn't exist
    controller_path.parent.mkdir(parents=True, exist_ok=True)

    # Choose template based on flags
    if api:
        template = API_CONTROLLER_TEMPLATE
    elif resource:
        template = RESOURCE_CONTROLLER_TEMPLATE
    else:
        template = BASIC_CONTROLLER_TEMPLATE

    # Format template with variables
    controller_content = template.format(
        model_name=model_name,
        model_class=model_class,
        controller_class=controller_class,
    )

    controller_path.write_text(controller_content)
    click.echo(f"Controller {name} created successfully!")
    click.echo(f"Controller: file://{controller_path.absolute()}")


@click.command(name="make:service")
@click.argument("name")
@click.option("--interface", is_flag=True, help="Create service with interface")
def make_service(name: str, interface: bool):
    """Create a new service file"""
    # Remove 'Service' suffix if present
    model_name = name.lower().replace("service", "")
    model_class = name.replace("Service", "")
    service_class = name

    service_path = Path("app/services") / f"{name.lower()}.py"
    if service_path.exists():
        click.echo(f"Service {name} already exists!")
        return

    # Create services directory if it doesn't exist
    service_path.parent.mkdir(parents=True, exist_ok=True)

    # Choose template based on interface flag
    template = SERVICE_WITH_INTERFACE_TEMPLATE if interface else SERVICE_TEMPLATE

    # Format template with variables
    service_content = template.format(
        model_name=model_name, model_class=model_class, service_class=service_class
    )

    service_path.write_text(service_content)
    click.echo(f"Service {name} created successfully!")
    click.echo(f"Service: file://{service_path.absolute()}")


@click.command(name="make:schema")
@click.argument("name")
def make_schema(name: str):
    """Create a new schema file"""
    schema_path = Path("app/schemas") / f"{name.lower()}.py"
    if schema_path.exists():
        click.echo(f"Schema {name} already exists!")
        return

    schema_content = f"""from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class {name.capitalize()}Base(BaseModel):
    pass

class {name.capitalize()}Create({name.capitalize()}Base):
    pass

class {name.capitalize()}Response({name.capitalize()}Base):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
"""
    schema_path.write_text(schema_content)
    click.echo(f"Schema {name} created successfully!")


@click.command(name="make:middleware")
@click.argument("name")
def make_middleware(name: str):
    """Create a new middleware file"""
    middleware_path = Path("app/http/middleware") / f"{name.lower()}.py"
    if middleware_path.exists():
        click.echo(f"Middleware {name} already exists!")
        return

    middleware_path.parent.mkdir(parents=True, exist_ok=True)

    middleware_content = f"""from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class {name.capitalize()}Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Process request
        response = await call_next(request)
        # Process response
        return response
"""
    middleware_path.write_text(middleware_content)
    click.echo(f"Middleware {name} created successfully!")


@click.command(name="make:exception")
@click.argument("name")
def make_exception(name: str):
    """Create a new exception file"""
    exception_path = Path("app/exceptions") / f"{name.lower()}.py"
    if exception_path.exists():
        click.echo(f"Exception {name} already exists!")
        return

    exception_path.parent.mkdir(parents=True, exist_ok=True)

    exception_content = f"""from fastapi import HTTPException, status

class {name.capitalize()}Exception(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail or "An error occurred"
        )
"""
    exception_path.write_text(exception_content)
    click.echo(f"Exception {name} created successfully!")


@click.command(name="make:validator")
@click.argument("name")
def make_validator(name: str):
    """Create a new validator file"""
    validator_path = Path("app/validators") / f"{name.lower()}.py"
    if validator_path.exists():
        click.echo(f"Validator {name} already exists!")
        return

    validator_path.parent.mkdir(parents=True, exist_ok=True)

    validator_content = f"""from pydantic import BaseModel, field_validator

class {name.capitalize()}Validator(BaseModel):
    @field_validator('*')
    @classmethod
    def validate_fields(cls, v):
        # Add your validation logic here
        return v
"""
    validator_path.write_text(validator_content)
    click.echo(f"Validator {name} created successfully!")


@click.command(name="make:repository")
@click.argument("name")
def make_repository(name: str):
    """Create a new repository file"""
    repository_path = Path("app/repositories") / f"{name.lower()}.py"
    if repository_path.exists():
        click.echo(f"Repository {name} already exists!")
        return

    repository_path.parent.mkdir(parents=True, exist_ok=True)

    repository_content = f"""from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.{name.lower()} import {name.capitalize()}
from app.schemas.{name.lower()} import {name.capitalize()}Create, {name.capitalize()}Update

class {name.capitalize()}Repository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[{name.capitalize()}]:
        return self.db.query({name.capitalize()}).all()

    def get_by_id(self, id: int) -> Optional[{name.capitalize()}]:
        return self.db.query({name.capitalize()}).filter({name.capitalize()}.id == id).first()

    def create(self, obj_in: {name.capitalize()}Create) -> {name.capitalize()}:
        db_obj = {name.capitalize()}(**obj_in.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: {name.capitalize()}, obj_in: {name.capitalize()}Update) -> {name.capitalize()}:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: {name.capitalize()}) -> None:
        self.db.delete(db_obj)
        self.db.commit()
"""
    repository_path.write_text(repository_content)
    click.echo(f"Repository {name} created successfully!")


@click.command(name="make:seeder")
@click.argument("name")
def make_seeder(name: str):
    """Create a new seeder file"""
    # Remove 'Seeder' suffix if present
    model_name = name.lower().replace("seeder", "")
    model_class = name.replace("Seeder", "")
    seeder_class = name

    seeder_path = Path("database/seeders") / f"{name.lower()}.py"
    if seeder_path.exists():
        click.echo(f"Seeder {name} already exists!")
        return

    # Create seeders directory if it doesn't exist
    seeder_path.parent.mkdir(parents=True, exist_ok=True)

    # Create seeder file
    seeder_content = SEEDER_TEMPLATE.format(
        model_name=model_name, model_class=model_class, seeder_class=seeder_class
    )
    seeder_path.write_text(seeder_content)
    click.echo(f"Seeder {name} created successfully!")
    click.echo(f"Seeder: file://{seeder_path.absolute()}")
