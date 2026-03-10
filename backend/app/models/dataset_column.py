import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["DatasetColumn"]


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    revision_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dtype: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # numeric, categorical, datetime, text
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    null_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    revision: Mapped["DatasetRevision"] = relationship(
        "DatasetRevision", back_populates="columns"
    )

    __table_args__ = (
        Index("ix_dataset_columns_revision_id", "revision_id"),
    )
