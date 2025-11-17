"""Database models."""

from app.models.base import db
from app.models.category import Category
from app.models.note import Note
from app.models.note_template import NoteTemplate

__all__ = ["db", "Category", "Note", "NoteTemplate"]
