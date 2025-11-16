"""Marshmallow schemas for request/response validation."""

from app.schemas.note import (
    NoteCreateSchema,
    NoteQuerySchema,
    NoteResponseSchema,
    PreviewQuerySchema,
)
from app.schemas.note_template import (
    NoteTemplateCreateSchema,
    NoteTemplateResponseSchema,
    NoteTemplateUpdateSchema,
)
from app.schemas.pagination import PaginationSchema

__all__ = [
    "NoteCreateSchema",
    "NoteQuerySchema",
    "NoteResponseSchema",
    "PreviewQuerySchema",
    "NoteTemplateCreateSchema",
    "NoteTemplateResponseSchema",
    "NoteTemplateUpdateSchema",
    "PaginationSchema",
]
