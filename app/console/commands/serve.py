"""Serve command - Start the development server"""

import os

import click


@click.command(name="serve")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(reload: bool):
    """Start the development server"""
    reload_flag = "--reload" if reload else ""
    os.system(f"uvicorn main:app {reload_flag}")
