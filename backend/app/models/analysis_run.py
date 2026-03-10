import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["AnalysisRun"]


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    analysis_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # descriptive, anova_one_way, t_test, pca, rda, etc.
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="queued"
    )  # queued, running, succeeded, failed, cancelled
    celery_task_id: Mapped[str | None] = mapped_column(String(128))
    params: Mapped[str | None] = mapped_column(Text)  # JSON request params
    result: Mapped[str | None] = mapped_column(Text)  # JSON result envelope
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()

    user: Mapped["User"] = relationship("User", back_populates="analysis_runs")
    inputs: Mapped[list["AnalysisInput"]] = relationship(
        "AnalysisInput", back_populates="run", cascade="all, delete-orphan"
    )
    exports: Mapped[list["Export"]] = relationship(
        "Export", back_populates="run", cascade="all, delete-orphan"
    )
    events: Mapped[list["RunEvent"]] = relationship(
        "RunEvent", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_analysis_runs_user_id", "user_id"),
        Index("ix_analysis_runs_status", "status"),
    )
