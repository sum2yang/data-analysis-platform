from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.datasets import DatasetRepository
from app.services.dataset_ingest_service import DatasetIngestService

__all__ = ["DatasetVersionService"]

logger = logging.getLogger(__name__)


class DatasetVersionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DatasetRepository(db)

    def create_new_revision(
        self,
        *,
        dataset_id: str,
        parent_revision_id: str,
        df: pd.DataFrame,
        source_type: str,
        source_detail: dict | None = None,
        user_id: str,
    ) -> str:
        from app.services.storage_service import StorageService

        parent = self.repo.get_revision(parent_revision_id)
        if not parent:
            raise ValueError(f"Parent revision not found: {parent_revision_id}")

        new_version = parent.version + 1
        import uuid
        revision_id = str(uuid.uuid4())

        storage = StorageService()
        canonical_path = storage.get_canonical_path(
            user_id=user_id,
            dataset_id=dataset_id,
            revision_id=revision_id,
        )
        DatasetIngestService.materialize_canonical_csv(df, canonical_path)

        rev = self.repo.create_revision(
            dataset_id=dataset_id,
            version=new_version,
            storage_path=str(canonical_path),
            row_count=len(df),
            col_count=len(df.columns),
            source_type=source_type,
            source_detail=json.dumps(source_detail) if source_detail else None,
            parent_revision_id=parent_revision_id,
        )
        rev.id = revision_id
        self.db.flush()

        col_defs = DatasetIngestService.infer_columns(df)
        self.repo.create_columns(revision_id=rev.id, columns=col_defs)
        self.repo.commit()

        return rev.id
