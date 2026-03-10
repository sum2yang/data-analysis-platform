import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["Export"]


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    export_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # figure, table
    format: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # png, svg, pdf, csv, xlsx
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )  # pending, ready, failed
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="exports")

    __table_args__ = (
        Index("ix_exports_run_id", "run_id"),
    )
