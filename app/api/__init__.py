"""API blueprints."""

from app.api.health import health_bp
from app.api.notes import notes_bp
from app.api.templates import templates_bp

__all__ = ["notes_bp", "templates_bp", "health_bp"]
