"""Health check endpoint."""

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("/")
class HealthCheck(MethodView):
    """Health check endpoint."""

    def get(self):
        """Get service health status."""
        printer_service = current_app.printer_service
        db_healthy = True

        # Check database
        try:
            from app.models import db

            db.session.execute(db.text("SELECT 1"))
            db.session.commit()
        except Exception:
            db_healthy = False

        # Check printer
        printer_available = printer_service.is_available()

        status = "healthy" if db_healthy else "degraded"

        return {
            "status": status,
            "database": "up" if db_healthy else "down",
            "printer": "available" if printer_available else "unavailable",
        }, 200 if db_healthy else 503
