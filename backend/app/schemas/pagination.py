"""Pagination schemas."""

from marshmallow import Schema, fields


class PaginationSchema(Schema):
    """Schema for pagination metadata."""

    page = fields.Int(dump_default=1)
    per_page = fields.Int(dump_default=20)
    total = fields.Int(required=True)
    pages = fields.Int(required=True)
    has_next = fields.Bool(required=True)
    has_prev = fields.Bool(required=True)


class PaginatedResponseSchema(Schema):
    """Base schema for paginated responses."""

    items = fields.List(fields.Dict(), required=True)
    pagination = fields.Nested(PaginationSchema, required=True)
