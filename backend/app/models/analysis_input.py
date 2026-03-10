import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["AnalysisInput"]


class AnalysisInput(Base):
    __tablename__ = "analysis_inputs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    revision_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="primary"
    )  # primary, environment (for RDA/CCA dual-matrix)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="inputs")

    __table_args__ = (
        Index("ix_analysis_inputs_run_id", "run_id"),
    )
