"""Note template model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import db


class NoteTemplate(db.Model):
    """HTML template for rendering notes."""

    __tablename__ = "note_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    template_html: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="template", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<NoteTemplate {self.name}>"
