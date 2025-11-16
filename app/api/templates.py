"""Note template API endpoints."""

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas import (
    NoteTemplateCreateSchema,
    NoteTemplateResponseSchema,
    NoteTemplateUpdateSchema,
)

templates_bp = Blueprint(
    "templates",
    __name__,
    url_prefix="/api/templates",
    description="Note template management",
)


@templates_bp.route("/")
class TemplateList(MethodView):
    """Template collection endpoint."""

    @templates_bp.response(200, NoteTemplateResponseSchema(many=True))
    def get(self):
        """List all note templates."""
        template_service = current_app.template_service
        templates = template_service.list_templates()
        return templates

    @templates_bp.arguments(NoteTemplateCreateSchema)
    @templates_bp.response(201, NoteTemplateResponseSchema)
    def post(self, data):
        """Create a new note template."""
        template_service = current_app.template_service
        try:
            template = template_service.create_template(**data)
            return template
        except ValueError as exc:
            abort(400, message=str(exc))


@templates_bp.route("/<int:template_id>")
class TemplateDetail(MethodView):
    """Template detail endpoint."""

    @templates_bp.response(200, NoteTemplateResponseSchema)
    def get(self, template_id):
        """Get a specific template."""
        template_service = current_app.template_service
        template = template_service.get_template(template_id)
        if not template:
            abort(404, message=f"Template {template_id} not found")
        return template

    @templates_bp.arguments(NoteTemplateUpdateSchema)
    @templates_bp.response(200, NoteTemplateResponseSchema)
    def put(self, data, template_id):
        """Update a template."""
        template_service = current_app.template_service
        try:
            template = template_service.update_template(template_id, **data)
            if not template:
                abort(404, message=f"Template {template_id} not found")
            return template
        except ValueError as exc:
            abort(400, message=str(exc))
