import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["DatasetOperation"]


class DatasetOperation(Base):
    __tablename__ = "dataset_operations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    revision_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    op_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # join, fill_missing, drop_missing, scale, log_transform, cast_type, etc.
    op_params: Mapped[str | None] = mapped_column(Text)  # JSON params
    op_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    revision: Mapped["DatasetRevision"] = relationship(
        "DatasetRevision", back_populates="operations"
    )

    __table_args__ = (
        Index("ix_dataset_operations_revision_id", "revision_id"),
    )
