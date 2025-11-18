"""Flask application factory."""

import logging
import sys
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_smorest import Api

from app.config import Settings, get_settings


def setup_logging(debug: bool = False):
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )


def create_app(settings: Settings | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        settings: Optional settings override (mainly for testing)

    Returns:
        Configured Flask application
    """
    # Load settings
    if settings is None:
        settings = get_settings()

    # Create Flask app
    app = Flask(__name__)

    # Configure Flask
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    app.config["SQLALCHEMY_DATABASE_URI"] = str(settings.database_url)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length

    # Flask-Smorest (OpenAPI) configuration
    app.config["API_TITLE"] = settings.api_title
    app.config["API_VERSION"] = settings.api_version
    app.config["OPENAPI_VERSION"] = settings.openapi_version
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Setup logging
    setup_logging(debug=settings.debug)

    # Initialize extensions
    from app.models import db

    db.init_app(app)

    # Setup migrations
    migrate = Migrate(app, db)

    # Setup API with OpenAPI documentation
    api = Api(app)

    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": settings.get_cors_origins()}})

    # Initialize services
    from app.services import (
        NoteRendererService,
        NoteService,
        TemplateService,
        get_printer_service,
    )

    printer_service = get_printer_service(
        enabled=settings.printer_enabled,
        encoding=settings.printer_encoding,
        max_width=settings.max_thermal_width_px,
        bottom_margin_mm=settings.bottom_margin_mm,
        thermal_dpi=settings.thermal_dpi,
    )

    renderer_service = NoteRendererService(default_width=settings.max_thermal_width_px)

    template_service = TemplateService()

    note_service = NoteService(
        printer_service=printer_service,
        renderer_service=renderer_service,
        template_service=template_service,
        upload_folder=settings.upload_folder,
    )

    # Store services in app context for access in routes
    app.printer_service = printer_service
    app.renderer_service = renderer_service
    app.template_service = template_service
    app.note_service = note_service
    app.settings = settings

    # Register blueprints
    from app.api import categories_bp, health_bp, notes_bp, templates_bp

    api.register_blueprint(categories_bp)
    api.register_blueprint(notes_bp)
    api.register_blueprint(templates_bp)
    api.register_blueprint(health_bp)

    # Create upload folder
    Path(settings.upload_folder).mkdir(parents=True, exist_ok=True)

    # Register CLI commands
    from app.utils import cli

    cli.init_app(app)

    app.logger.info("Application initialized successfully")

    return app
