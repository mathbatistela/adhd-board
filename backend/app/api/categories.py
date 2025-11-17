"""Category API endpoints."""

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from app.models import Category, db
from app.schemas.category import (
    CategoryCreateSchema,
    CategoryResponseSchema,
    CategoryUpdateSchema,
)

categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/api/categories",
    description="Category management endpoints",
)


@categories_bp.route("/")
class CategoriesView(MethodView):
    """Category collection endpoint."""

    @categories_bp.response(200, CategoryResponseSchema(many=True))
    def get(self):
        """List all categories.

        Returns all active and inactive categories.
        """
        categories = Category.query.order_by(Category.name).all()
        return categories

    @categories_bp.arguments(CategoryCreateSchema)
    @categories_bp.response(201, CategoryResponseSchema)
    def post(self, data):
        """Create a new category.

        Creates a new category with the provided data.
        """
        try:
            category = Category(**data)
            db.session.add(category)
            db.session.commit()
            return category
        except IntegrityError:
            db.session.rollback()
            abort(409, message=f"Category with name '{data['name']}' already exists")


@categories_bp.route("/<int:category_id>")
class CategoryView(MethodView):
    """Single category endpoint."""

    @categories_bp.response(200, CategoryResponseSchema)
    def get(self, category_id):
        """Get a specific category by ID."""
        category = Category.query.get(category_id)
        if not category:
            abort(404, message=f"Category with id {category_id} not found")
        return category

    @categories_bp.arguments(CategoryUpdateSchema)
    @categories_bp.response(200, CategoryResponseSchema)
    def put(self, data, category_id):
        """Update a category.

        Updates the specified fields of a category.
        Note: The 'name' field cannot be updated to prevent breaking references.
        """
        category = Category.query.get(category_id)
        if not category:
            abort(404, message=f"Category with id {category_id} not found")

        # Update only provided fields
        for key, value in data.items():
            setattr(category, key, value)

        db.session.commit()
        return category

    @categories_bp.response(204)
    def delete(self, category_id):
        """Delete a category.

        Note: This will fail if there are notes associated with this category.
        Consider using PUT to set is_active=false instead of deleting.
        """
        category = Category.query.get(category_id)
        if not category:
            abort(404, message=f"Category with id {category_id} not found")

        try:
            db.session.delete(category)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                409,
                message="Cannot delete category with existing notes. Set is_active=false instead.",
            )
