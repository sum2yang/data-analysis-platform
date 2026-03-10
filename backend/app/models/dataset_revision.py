import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

__all__ = ["DatasetRevision"]


class DatasetRevision(Base):
    __tablename__ = "dataset_revisions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    parent_revision_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dataset_revisions.id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    col_count: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="upload"
    )  # upload, join, transform
    source_detail: Mapped[str | None] = mapped_column(Text)  # JSON description of operation
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="revisions")
    parent: Mapped["DatasetRevision | None"] = relationship(
        "DatasetRevision", remote_side="DatasetRevision.id", uselist=False
    )
    columns: Mapped[list["DatasetColumn"]] = relationship(
        "DatasetColumn", back_populates="revision", cascade="all, delete-orphan"
    )
    operations: Mapped[list["DatasetOperation"]] = relationship(
        "DatasetOperation", back_populates="revision", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_dataset_revisions_dataset_id", "dataset_id"),
        Index("ix_dataset_revisions_parent_id", "parent_revision_id"),
    )
