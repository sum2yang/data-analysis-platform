from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.dataset_operation import DatasetOperation

__all__ = ["OperationHistoryService"]

logger = logging.getLogger(__name__)


class OperationHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        revision_id: str,
        op_type: str,
        op_params: dict[str, Any],
        op_order: int | None = None,
    ) -> DatasetOperation:
        if op_order is None:
            count = (
                self.db.query(DatasetOperation)
                .filter(DatasetOperation.revision_id == revision_id)
                .count()
            )
            op_order = count

        op = DatasetOperation(
            revision_id=revision_id,
            op_type=op_type,
            op_params=json.dumps(op_params),
            op_order=op_order,
        )
        self.db.add(op)
        self.db.commit()
        self.db.refresh(op)
        return op

    def list_operations(self, revision_id: str) -> list[DatasetOperation]:
        return (
            self.db.query(DatasetOperation)
            .filter(DatasetOperation.revision_id == revision_id)
            .order_by(DatasetOperation.op_order)
            .all()
        )
