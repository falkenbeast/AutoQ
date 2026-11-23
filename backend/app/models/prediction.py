from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Prediction(Base):
    """
    Machine learning defect prediction record.
    Persists only genuine model inference results (never fabricated values).
    """

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("components.component_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    inspection_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("inspections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    predicted_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    defect_probability: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    model_version: Mapped[str] = mapped_column(
        String(50), default="1.0.0", nullable=False
    )
    model_status: Mapped[str] = mapped_column(
        String(50), default="MODEL_NOT_TRAINED", nullable=False
    )
    contributing_factors: Mapped[Optional[Any]] = mapped_column(
        JSON, nullable=True
    )
    recommendation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    component: Mapped[Optional["Component"]] = relationship(
        "Component",
        back_populates="predictions",
    )
    inspection: Mapped[Optional["Inspection"]] = relationship(
        "Inspection",
        back_populates="predictions",
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} component_id='{self.component_id}' "
            f"predicted_status='{self.predicted_status}' probability={self.defect_probability}>"
        )

