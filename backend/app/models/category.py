"""Category model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import db


class Category(db.Model):
    """Note category with display metadata."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(Text, nullable=False)  # SVG markup
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship
    notes: Mapped[list["Note"]] = relationship("Note", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}: {self.icon} {self.label}>"
