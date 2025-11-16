"""Note API endpoints."""

from pathlib import Path

from flask import current_app, send_file
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas import (
    NoteCreateSchema,
    NoteQuerySchema,
    NoteResponseSchema,
    PreviewQuerySchema,
)

notes_bp = Blueprint(
    "notes",
    __name__,
    url_prefix="/api/notes",
    description="Note management and printing",
)


@notes_bp.route("/")
class NoteList(MethodView):
    """Note collection endpoint."""

    @notes_bp.arguments(NoteQuerySchema, location="query")
    @notes_bp.response(200)
    def get(self, query_args):
        """List notes with pagination."""
        note_service = current_app.note_service
        pagination = note_service.list_notes(**query_args)

        # Serialize notes
        schema = NoteResponseSchema()
        items = [schema.dump(note) for note in pagination.items]

        return {
            "items": items,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }

    @notes_bp.arguments(NoteCreateSchema)
    @notes_bp.response(201, NoteResponseSchema)
    def post(self, data):
        """Create a new note."""
        note_service = current_app.note_service
        try:
            note = note_service.create_note(**data)
            return note
        except ValueError as exc:
            abort(400, message=str(exc))
        except Exception as exc:
            current_app.logger.error(f"Failed to create note: {exc}")
            abort(500, message="Failed to create note")


@notes_bp.route("/<int:note_id>")
class NoteDetail(MethodView):
    """Note detail endpoint."""

    @notes_bp.response(200, NoteResponseSchema)
    def get(self, note_id):
        """Get a specific note."""
        note_service = current_app.note_service
        note = note_service.get_note(note_id)
        if not note:
            abort(404, message=f"Note {note_id} not found")
        return note


@notes_bp.route("/<int:note_id>/preview")
class NotePreview(MethodView):
    """Note preview endpoint."""

    @notes_bp.arguments(PreviewQuerySchema, location="query")
    def get(self, query_args, note_id):
        """Preview note as HTML or image."""
        note_service = current_app.note_service
        note = note_service.get_note(note_id)
        if not note:
            abort(404, message=f"Note {note_id} not found")

        format_type = query_args.get("format", "image")

        if format_type == "html":
            # Return HTML content
            if not note.html_content:
                abort(404, message="HTML content not available for this note")
            return note.html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

        else:  # image
            # Return image file
            if not note.image_path:
                abort(404, message="Image not available for this note")

            image_path = Path(note.image_path)
            if not image_path.exists():
                abort(404, message="Image file not found")

            return send_file(image_path, mimetype="image/png")


@notes_bp.route("/<int:note_id>/print")
class NotePrint(MethodView):
    """Note printing endpoint."""

    @notes_bp.response(200)
    def post(self, note_id):
        """Print an existing note."""
        note_service = current_app.note_service
        try:
            success = note_service.print_note(note_id)
            if success:
                return {"message": f"Note {note_id} sent to printer successfully"}
            else:
                abort(503, message="Printer unavailable or print failed")
        except ValueError as exc:
            abort(404, message=str(exc))
        except Exception as exc:
            current_app.logger.error(f"Failed to print note {note_id}: {exc}")
            abort(500, message="Failed to print note")
