"""Key Generate command"""

import secrets
from pathlib import Path

import click


def generate_and_persist_key() -> str:
    """Generate a new application key and save it to .env"""
    key = secrets.token_hex(32)
    env_path = Path(".env")
    
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        # Check if APP_KEY already exists
        key_exists = False
        new_lines = []
        for line in lines:
            if line.startswith("APP_KEY="):
                new_lines.append(f"APP_KEY={key}\n")
                key_exists = True
            else:
                new_lines.append(line)
        
        if not key_exists:
            new_lines.append(f"\nAPP_KEY={key}\n")
            
        with open(env_path, "w") as f:
            f.writelines(new_lines)
            
    return key


@click.command(name="key:generate")
def key_generate():
    """Generate a new application key"""
    key = generate_and_persist_key()
    click.echo(f"Application key: {key}")
    click.echo("Key has been saved to your .env file.")
