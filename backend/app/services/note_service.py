"""Note service."""

import logging
from datetime import date as date_type
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import select

from app.models import Category, Note, db
from app.services.note_renderer import NoteRendererService
from app.services.printer import BasePrinterService
from app.services.template_service import TemplateService

logger = logging.getLogger(__name__)


class NoteService:
    """Service for managing notes."""

    def __init__(
        self,
        printer_service: BasePrinterService,
        renderer_service: NoteRendererService,
        template_service: TemplateService,
        upload_folder: Path,
    ):
        self.printer_service = printer_service
        self.renderer_service = renderer_service
        self.template_service = template_service
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def create_note(
        self,
        category_id: int,
        text: str,
        date: Optional[date_type] = None,
        template_id: Optional[int] = None,
        should_print: bool = False,
        width: int = 384,
    ) -> Note:
        """Create and render a new note."""
        # Get category
        category = db.session.get(Category, category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Get template
        if template_id:
            template = self.template_service.get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
        else:
            template = self.template_service.get_default_template()

        # Use current date if not provided
        if not date:
            date = date_type.today()

        # Create database record first (without image/html) to get the ID
        note = Note(
            category_id=category_id,
            text=text,
            date=date,
            template_id=template.id,
            printed=False,
        )
        db.session.add(note)
        db.session.flush()  # Flush to get the ID without committing

        # Now we have note.id, generate ticket_id for display
        ticket_id = note.ticket_id

        # Format date for display
        date_str = date.strftime("%d %b %Y")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"note_{timestamp}.png"
        image_path = self.upload_folder / image_filename

        # Render note with the actual ID
        try:
            rendered_path, html_content = self.renderer_service.render_note(
                template_html=template.template_html,
                category_icon=category.icon,
                ticket_id=ticket_id,
                text=text,
                date=date_str,
                output_path=image_path,
                width=width,
            )
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to render note: {exc}")
            raise ValueError(f"Failed to render note: {exc}")

        # Update note with rendered content
        note.image_path = str(rendered_path)
        note.html_content = html_content
        db.session.commit()

        logger.info(f"Created note {note.id}: {ticket_id}")

        # Print if requested
        if should_print:
            self.print_note(note.id)

        return note

    def get_note(self, note_id: int) -> Optional[Note]:
        """Get a note by ID."""
        return db.session.get(Note, note_id)

    def list_notes(
        self,
        page: int = 1,
        per_page: int = 20,
        category_id: Optional[int] = None,
        printed: Optional[bool] = None,
    ) -> Pagination:
        """List notes with pagination and optional filters."""
        stmt = select(Note).order_by(Note.created_at.desc())

        if category_id:
            stmt = stmt.where(Note.category_id == category_id)
        if printed is not None:
            stmt = stmt.where(Note.printed == printed)

        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    def update_note(
        self,
        note_id: int,
        category_id: Optional[int] = None,
        text: Optional[str] = None,
    ) -> Optional[Note]:
        """Update a note's category or text."""
        note = self.get_note(note_id)
        if not note:
            return None

        # Validate category if provided
        if category_id is not None:
            category = db.session.get(Category, category_id)
            if not category:
                raise ValueError(f"Category {category_id} not found")
            note.category_id = category_id

        # Update text if provided
        if text is not None:
            note.text = text

        db.session.commit()
        logger.info(f"Updated note {note_id}")
        return note

    def delete_note(self, note_id: int) -> bool:
        """Delete a note."""
        note = self.get_note(note_id)
        if not note:
            return False

        # Delete image file if it exists
        if note.image_path:
            image_path = Path(note.image_path)
            if image_path.exists():
                try:
                    image_path.unlink()
                    logger.info(f"Deleted image file: {image_path}")
                except Exception as exc:
                    logger.warning(f"Failed to delete image file {image_path}: {exc}")

        db.session.delete(note)
        db.session.commit()
        logger.info(f"Deleted note {note_id}")
        return True

    def print_note(self, note_id: int) -> bool:
        """Print an existing note."""
        note = self.get_note(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        if not note.image_path:
            raise ValueError(f"Note {note_id} has no rendered image")

        image_path = Path(note.image_path)
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")

        # Print
        success = self.printer_service.print_image(image_path)

        # Update printed status
        if success:
            note.printed = True
            db.session.commit()
            logger.info(f"Printed note {note_id}")

        return success
