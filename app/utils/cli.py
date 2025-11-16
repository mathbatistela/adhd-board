"""CLI commands for database initialization and management."""

import click
from flask import Flask
from flask.cli import with_appcontext

from app.models import db


def init_app(app: Flask):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_default_template_command)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database."""
    db.create_all()
    click.echo("Initialized the database.")


@click.command("seed-default-template")
@click.option(
    "--force",
    "force_update",
    is_flag=True,
    default=False,
    help="Overwrite the existing default template HTML if it already exists.",
)
@with_appcontext
def seed_default_template_command(force_update: bool):
    """Create the default note template from app/templates/default_note.html."""
    from pathlib import Path

    from app.services import TemplateService

    template_path = Path("app/templates/default_note.html")
    if not template_path.exists():
        click.echo("Error: app/templates/default_note.html not found", err=True)
        return

    template_html = template_path.read_text(encoding="utf-8")

    template_service = TemplateService()
    try:
        existing = template_service.get_template_by_name("default")
        if existing:
            if force_update:
                existing.template_html = template_html
                existing.is_active = True
                db.session.commit()
                click.echo("Updated default template HTML.")
            else:
                click.echo("Default template already exists. Use --force to overwrite.")
            return

        template = template_service.create_template(
            name="default",
            template_html=template_html,
            is_active=True,
        )
        click.echo(f"Created default template (ID: {template.id})")
    except Exception as exc:
        click.echo(f"Error creating template: {exc}", err=True)
