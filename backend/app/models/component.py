from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Component(Base):
    """
    Automotive component master model.
    Represents discrete automotive parts (e.g. Brake Caliper, Crankshaft, Turbo Housing).
    """

    __tablename__ = "components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    component_name: Mapped[str] = mapped_column(String(150), nullable=False)
    component_category: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    inspections: Mapped[List["Inspection"]] = relationship(
        "Inspection",
        back_populates="component",
        passive_deletes=True,
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="component",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Component id={self.id} component_id='{self.component_id}' name='{self.component_name}'>"

