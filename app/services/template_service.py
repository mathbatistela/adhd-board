"""Note template service."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import NoteTemplate, db

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing note templates."""

    def create_template(
        self, name: str, template_html: str, is_active: bool = True
    ) -> NoteTemplate:
        """Create a new note template."""
        template = NoteTemplate(
            name=name,
            template_html=template_html,
            is_active=is_active,
        )
        try:
            db.session.add(template)
            db.session.commit()
            logger.info(f"Created template: {name}")
            return template
        except IntegrityError as exc:
            db.session.rollback()
            logger.error(f"Template with name '{name}' already exists")
            raise ValueError(f"Template with name '{name}' already exists") from exc

    def get_template(self, template_id: int) -> Optional[NoteTemplate]:
        """Get a template by ID."""
        return db.session.get(NoteTemplate, template_id)

    def get_template_by_name(self, name: str) -> Optional[NoteTemplate]:
        """Get a template by name."""
        stmt = select(NoteTemplate).where(NoteTemplate.name == name)
        return db.session.execute(stmt).scalar_one_or_none()

    def list_templates(self, active_only: bool = False) -> list[NoteTemplate]:
        """List all templates."""
        stmt = select(NoteTemplate).order_by(NoteTemplate.created_at.desc())
        if active_only:
            stmt = stmt.where(NoteTemplate.is_active == True)
        return list(db.session.execute(stmt).scalars())

    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        template_html: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[NoteTemplate]:
        """Update a template."""
        template = self.get_template(template_id)
        if not template:
            return None

        if name is not None:
            template.name = name
        if template_html is not None:
            template.template_html = template_html
        if is_active is not None:
            template.is_active = is_active

        try:
            db.session.commit()
            logger.info(f"Updated template {template_id}")
            return template
        except IntegrityError as exc:
            db.session.rollback()
            logger.error(f"Failed to update template {template_id}: {exc}")
            raise ValueError(f"Failed to update template: {exc}") from exc

    def get_default_template(self) -> NoteTemplate:
        """Get the default template or raise error if none exists."""
        # Try to get template named "default"
        default = self.get_template_by_name("default")
        if default and default.is_active:
            return default

        # Get any active template
        stmt = select(NoteTemplate).where(NoteTemplate.is_active == True).limit(1)
        template = db.session.execute(stmt).scalar_one_or_none()
        if template:
            return template

        raise ValueError("No active templates available. Please create a template first.")
