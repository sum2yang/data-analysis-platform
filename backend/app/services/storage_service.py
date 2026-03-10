from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

__all__ = ["StorageService"]

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.settings = get_settings()

    def save_upload(
        self, *, user_id: str, dataset_id: str, revision_id: str, file: UploadFile
    ) -> Path:
        target_dir = (
            self.settings.UPLOAD_ROOT
            / user_id
            / dataset_id
            / revision_id
            / "original"
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file.filename
        with open(target_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return target_path

    def get_canonical_dir(
        self, *, user_id: str, dataset_id: str, revision_id: str
    ) -> Path:
        d = (
            self.settings.UPLOAD_ROOT
            / user_id
            / dataset_id
            / revision_id
        )
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_canonical_path(
        self, *, user_id: str, dataset_id: str, revision_id: str
    ) -> Path:
        return self.get_canonical_dir(
            user_id=user_id, dataset_id=dataset_id, revision_id=revision_id
        ) / "canonical.csv"
