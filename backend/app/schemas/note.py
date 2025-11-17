"""Note schemas."""

from marshmallow import Schema, fields, validate

from app.schemas.category import CategoryResponseSchema


class NoteCreateSchema(Schema):
    """Schema for creating a note."""

    category_id = fields.Int(
        required=True,
        metadata={"description": "Category ID"},
    )
    text = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Main note text content"},
    )
    date = fields.Date(
        allow_none=True,
        metadata={"description": "Note date (defaults to current date if omitted)"},
    )
    template_id = fields.Int(
        allow_none=True,
        metadata={"description": "Template ID to use (uses default if omitted)"},
    )
    should_print = fields.Bool(
        load_default=False,
        metadata={"description": "Whether to send note to printer immediately"},
    )
    width = fields.Int(
        load_default=384,
        validate=validate.Range(min=100, max=800),
        metadata={"description": "Rendered image width in pixels"},
    )


class NoteUpdateSchema(Schema):
    """Schema for updating a note."""

    category_id = fields.Int(metadata={"description": "Category ID"})
    text = fields.Str(
        validate=validate.Length(min=1),
        metadata={"description": "Main note text content"},
    )


class NoteQuerySchema(Schema):
    """Schema for querying notes."""

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    category_id = fields.Int(metadata={"description": "Filter by category ID"})
    printed = fields.Bool()


class PreviewQuerySchema(Schema):
    """Schema for preview format query parameter."""

    format = fields.Str(
        load_default="image",
        validate=validate.OneOf(["html", "image"]),
        metadata={"description": "Preview format: html or image"},
    )


class NoteResponseSchema(Schema):
    """Schema for note responses."""

    id = fields.Int(required=True)
    ticket_id = fields.Str(required=True)
    category_id = fields.Int(required=True)
    category = fields.Nested(CategoryResponseSchema, required=True)
    text = fields.Str(required=True)
    date = fields.Date(required=True)
    image_path = fields.Str(allow_none=True)
    html_content = fields.Str(allow_none=True)
    template_id = fields.Int(allow_none=True)
    printed = fields.Bool(required=True)
    created_at = fields.DateTime(required=True)
