"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from app import create_app
from app.config import Settings
from app.models import Note, NoteTemplate, db
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
        .category-icon svg { width: 24px; height: 24px; }
        .main-text { font-size: 16px; margin: 10px 0; }
        .date { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="note">
        <div class="ticket-id">{{ ticket_id }}</div>
        <div class="category-icon">{{ category_icon_svg }}</div>
        <div class="category-label">{{ category_label }}</div>
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
def sample_note(app, sample_template):
    """Create a sample note for testing."""
    from datetime import date

    note = Note(
        category="trabalho",
        text="Test note content",
        date=date.today(),
        template_id=sample_template.id,
        printed=False,
    )
    db.session.add(note)
    db.session.commit()
    return note
