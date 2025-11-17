"""Note model."""

from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import db


class Note(db.Model):
    """Generated note record."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("note_templates.id"), nullable=True
    )
    printed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="notes")
    template: Mapped["NoteTemplate"] = relationship("NoteTemplate", back_populates="notes")

    @property
    def ticket_id(self) -> str:
        """Ticket identifier derived from database id."""
        return f"#{self.id}"

    def __repr__(self) -> str:
        return f"<Note #{self.id}: {self.text[:30]}>"
