"""CLI commands for database initialization and management."""

import click
from flask import Flask
from flask.cli import with_appcontext

from app.models import db


def init_app(app: Flask):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_default_template_command)
    app.cli.add_command(seed_categories_command)
    app.cli.add_command(seed_defaults_command)


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


@click.command("seed-categories")
@click.option(
    "--force",
    "force_update",
    is_flag=True,
    default=False,
    help="Update existing categories if they already exist.",
)
@with_appcontext
def seed_categories_command(force_update: bool):
    """Seed default categories into the database."""
    from app.models import Category

    default_categories = [
        {
            "name": "trabalho",
            "label": "Trabalho",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9h18v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9zm7-6h4v2h-4V3zm-1 4h6a1 1 0 011 1v1H8V8a1 1 0 011-1z"/></svg>',
            "color": "#3B82F6",
            "is_active": True,
        },
        {
            "name": "casa",
            "label": "Casa",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
            "color": "#10B981",
            "is_active": True,
        },
        {
            "name": "estudos",
            "label": "Estudos",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/></svg>',
            "color": "#8B5CF6",
            "is_active": True,
        },
        {
            "name": "saude",
            "label": "Saúde",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 9h-4v4h-4v-4H6v-4h4V8h4v4h4v4z"/></svg>',
            "color": "#EF4444",
            "is_active": True,
        },
        {
            "name": "lazer",
            "label": "Lazer",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M21 6H3c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-10 7H8v3H6v-3H3v-2h3V8h2v3h3v2zm4.5 2c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm4-3c-.83 0-1.5-.67-1.5-1.5S18.67 9 19.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>',
            "color": "#EC4899",
            "is_active": True,
        },
        {
            "name": "pessoas",
            "label": "Pessoas",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>',
            "color": "#F59E0B",
            "is_active": True,
        },
        {
            "name": "financas",
            "label": "Finanças",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>',
            "color": "#059669",
            "is_active": True,
        },
    ]

    created = 0
    updated = 0
    skipped = 0

    for cat_data in default_categories:
        existing = Category.query.filter_by(name=cat_data["name"]).first()

        if existing:
            if force_update:
                for key, value in cat_data.items():
                    if key != "name":  # Don't update name
                        setattr(existing, key, value)
                updated += 1
            else:
                skipped += 1
        else:
            category = Category(**cat_data)
            db.session.add(category)
            created += 1

    db.session.commit()

    click.echo(f"Categories seeded: {created} created, {updated} updated, {skipped} skipped")


@click.command("seed-defaults")
@click.option(
    "--force",
    "force_update",
    is_flag=True,
    default=False,
    help="Update existing data if it already exists.",
)
@with_appcontext
def seed_defaults_command(force_update: bool):
    """Seed default categories and template."""
    from flask import current_app

    # Invoke seed-categories
    current_app.logger.info("Seeding categories...")
    seed_categories_command.callback(force_update)

    # Invoke seed-default-template
    current_app.logger.info("Seeding default template...")
    seed_default_template_command.callback(force_update)

    click.echo("All defaults seeded successfully!")
