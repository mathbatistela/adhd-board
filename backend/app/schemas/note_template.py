"""Note template schemas."""

from marshmallow import Schema, fields, validate


class NoteTemplateCreateSchema(Schema):
    """Schema for creating a note template."""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Unique template name"},
    )
    template_html = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "HTML template with placeholders"},
    )
    is_active = fields.Bool(
        load_default=True,
        metadata={"description": "Whether template is active"},
    )


class NoteTemplateUpdateSchema(Schema):
    """Schema for updating a note template."""

    name = fields.Str(
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Unique template name"},
    )
    template_html = fields.Str(
        validate=validate.Length(min=1),
        metadata={"description": "HTML template with placeholders"},
    )
    is_active = fields.Bool(
        metadata={"description": "Whether template is active"},
    )


class NoteTemplateResponseSchema(Schema):
    """Schema for note template responses."""

    id = fields.Int(required=True)
    name = fields.Str(required=True)
    template_html = fields.Str(required=True)
    is_active = fields.Bool(required=True)
    created_at = fields.DateTime(required=True)
