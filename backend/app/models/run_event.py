import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["RunEvent"]


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # created, started, progress, succeeded, failed, cancelled
    payload: Mapped[str | None] = mapped_column(Text)  # JSON event data
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="events")

    __table_args__ = (
        Index("ix_run_events_run_id", "run_id"),
    )
