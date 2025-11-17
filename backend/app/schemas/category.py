"""Category schemas for request/response validation."""

from marshmallow import Schema, fields, validate


class CategorySchema(Schema):
    """Base category schema with all fields."""

    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50),
        metadata={"description": "Unique category identifier (e.g., 'trabalho', 'casa')"},
    )
    label = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Display label (e.g., 'Trabalho', 'Casa')"},
    )
    icon = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000),
        metadata={"description": "SVG icon markup"},
    )
    color = fields.Str(
        required=True,
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"),
        metadata={"description": "Hex color code (e.g., '#3B82F6')"},
    )
    is_active = fields.Bool(dump_default=True)
    created_at = fields.DateTime(dump_only=True)


class CategoryCreateSchema(Schema):
    """Schema for creating a new category."""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50),
        metadata={"description": "Unique category identifier"},
    )
    label = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Display label"},
    )
    icon = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000),
        metadata={"description": "SVG icon markup"},
    )
    color = fields.Str(
        required=True,
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"),
        metadata={"description": "Hex color code"},
    )
    is_active = fields.Bool(load_default=True)


class CategoryUpdateSchema(Schema):
    """Schema for updating an existing category."""

    label = fields.Str(
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Display label"},
    )
    icon = fields.Str(
        validate=validate.Length(min=1, max=2000),
        metadata={"description": "SVG icon markup"},
    )
    color = fields.Str(
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"),
        metadata={"description": "Hex color code"},
    )
    is_active = fields.Bool()


class CategoryResponseSchema(CategorySchema):
    """Schema for category responses."""

    pass
