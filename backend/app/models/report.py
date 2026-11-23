from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Report(Base):
    """
    Quality audit report metadata entity.
    Stores report lifecycle and metadata in SQLite.
    Physical report binary files (.pdf/.csv) are stored in backend/reports/.
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_name: Mapped[str] = mapped_column(String(150), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    report_status: Mapped[str] = mapped_column(
        String(50), default="PENDING_PHASE_5", nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Report id={self.id} name='{self.report_name}' status='{self.report_status}'>"

