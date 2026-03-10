from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_column import DatasetColumn
from app.models.dataset_revision import DatasetRevision

__all__ = ["DatasetRepository"]


class DatasetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_dataset(
        self,
        *,
        owner_id: str,
        name: str,
        original_filename: str,
        file_type: str,
        description: str | None = None,
    ) -> Dataset:
        ds = Dataset(
            owner_id=owner_id,
            name=name,
            original_filename=original_filename,
            file_type=file_type,
            description=description,
        )
        self.db.add(ds)
        self.db.flush()
        return ds

    def create_revision(
        self,
        *,
        dataset_id: str,
        version: int,
        storage_path: str,
        row_count: int,
        col_count: int,
        source_type: str = "upload",
        source_detail: str | None = None,
        parent_revision_id: str | None = None,
    ) -> DatasetRevision:
        rev = DatasetRevision(
            dataset_id=dataset_id,
            version=version,
            storage_path=storage_path,
            row_count=row_count,
            col_count=col_count,
            source_type=source_type,
            source_detail=source_detail,
            parent_revision_id=parent_revision_id,
        )
        self.db.add(rev)
        self.db.flush()
        return rev

    def create_columns(
        self, *, revision_id: str, columns: list[dict]
    ) -> list[DatasetColumn]:
        result = []
        for col_data in columns:
            col = DatasetColumn(revision_id=revision_id, **col_data)
            self.db.add(col)
            result.append(col)
        self.db.flush()
        return result

    def get_by_id(self, dataset_id: str) -> Dataset | None:
        return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def get_by_owner(self, owner_id: str) -> list[Dataset]:
        return (
            self.db.query(Dataset)
            .filter(Dataset.owner_id == owner_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )

    def get_revision(self, revision_id: str) -> DatasetRevision | None:
        return (
            self.db.query(DatasetRevision)
            .filter(DatasetRevision.id == revision_id)
            .first()
        )

    def get_latest_revision(self, dataset_id: str) -> DatasetRevision | None:
        return (
            self.db.query(DatasetRevision)
            .filter(DatasetRevision.dataset_id == dataset_id)
            .order_by(DatasetRevision.version.desc())
            .first()
        )

    def commit(self) -> None:
        self.db.commit()
