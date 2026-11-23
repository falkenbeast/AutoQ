from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Inspection(Base):
    """
    Automotive component physical quality inspection record.
    Captures manufacturing temperatures, pressure, batch numbers, and audit outcomes.
    """

    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("components.component_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    manufacturing_temperature: Mapped[float] = mapped_column(Float, nullable=False)
    pressure: Mapped[float] = mapped_column(Float, nullable=False)
    production_batch: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    inspection_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    inspection_result: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    defect_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    component: Mapped["Component"] = relationship(
        "Component",
        back_populates="inspections",
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="inspection",
        passive_deletes=True,
    )

    @property
    def component_name(self) -> str:
        return self.component.component_name if self.component else ""

    @property
    def component_category(self) -> str:
        return self.component.component_category if self.component else ""

    def __repr__(self) -> str:
        return (
            f"<Inspection id={self.id} component_id='{self.component_id}' "
            f"result='{self.inspection_result}' batch='{self.production_batch}'>"
        )

