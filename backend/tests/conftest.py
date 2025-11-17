"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from app import create_app
from app.config import Settings
from app.models import Category, Note, NoteTemplate, db
from app.services import MockPrinterService


@pytest.fixture(scope="session")
def test_settings():
    """Create test settings with SQLite database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_folder = Path(tmpdir) / "uploads"
        upload_folder.mkdir(exist_ok=True)

        settings = Settings(
            flask_env="testing",
            secret_key="test-secret-key",
            debug=True,
            database_url="sqlite:///:memory:",
            printer_enabled=False,  # Use mock printer for tests
            upload_folder=upload_folder,
        )
        yield settings


@pytest.fixture(scope="function")
def app(test_settings):
    """Create Flask application for testing."""
    app = create_app(test_settings)
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # Close all database connections


@pytest.fixture(scope="function")
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def mock_printer(app):
    """Get mock printer service."""
    return app.printer_service


@pytest.fixture(scope="function")
def sample_category(app):
    """Create a sample category for testing."""
    category = Category(
        name="trabalho",
        label="Trabalho",
        icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9h18v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9zm7-6h4v2h-4V3zm-1 4h6a1 1 0 011 1v1H8V8a1 1 0 011-1z"/></svg>',
        color="#3B82F6",
        is_active=True,
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture(scope="function")
def sample_categories(app):
    """Create multiple sample categories for testing."""
    categories = [
        Category(
            name="trabalho",
            label="Trabalho",
            icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9h18v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9zm7-6h4v2h-4V3zm-1 4h6a1 1 0 011 1v1H8V8a1 1 0 011-1z"/></svg>',
            color="#3B82F6",
            is_active=True,
        ),
        Category(
            name="casa",
            label="Casa",
            icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
            color="#10B981",
            is_active=True,
        ),
        Category(
            name="estudos",
            label="Estudos",
            icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/></svg>',
            color="#8B5CF6",
            is_active=True,
        ),
    ]
    db.session.add_all(categories)
    db.session.commit()
    return categories


@pytest.fixture(scope="function")
def sample_template(app):
    """Create a sample template for testing."""
    template_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <style>
        body { width: {{ width }}px; font-family: Arial; }
        .note { padding: 10px; text-align: center; }
        .ticket-id { font-size: 24px; font-weight: bold; }
        .category-icon { width: 32px; height: 32px; display: inline-flex; }
        .category-icon svg { width: 100%; height: 100%; }
        .main-text { font-size: 16px; margin: 10px 0; }
        .date { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="note">
        <div class="ticket-id">{{ ticket_id }}</div>
        <div class="category-icon">{{ category_icon|safe }}</div>
        <div class="main-text">{{ text }}</div>
        <div class="date">{{ date }}</div>
    </div>
</body>
</html>"""

    from app.services import TemplateService

    service = TemplateService()
    template = service.create_template(
        name="test-template", template_html=template_html, is_active=True
    )
    return template


@pytest.fixture(scope="function")
def sample_note(app, sample_template, sample_category):
    """Create a sample note for testing."""
    from datetime import date

    note = Note(
        category_id=sample_category.id,
        text="Test note content",
        date=date.today(),
        template_id=sample_template.id,
        printed=False,
    )
    db.session.add(note)
    db.session.commit()
    return note
