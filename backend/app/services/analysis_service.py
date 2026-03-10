from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.dataset_revision import DatasetRevision
from app.repositories.analysis_runs import AnalysisRunRepository
from app.schemas.analysis_run import AnalysisRunAcceptedResponse

__all__ = ["AnalysisService"]

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.run_repo = AnalysisRunRepository(db)

    def submit(
        self,
        *,
        user_id: str,
        analysis_type: str,
        params: dict[str, Any],
        revision_ids: dict[str, str],
    ) -> AnalysisRunAcceptedResponse:
        for role, rev_id in revision_ids.items():
            rev = self.db.query(DatasetRevision).filter(DatasetRevision.id == rev_id).first()
            if not rev:
                raise NotFoundError(f"Revision not found: {rev_id}")

        run = self.run_repo.create(
            user_id=user_id,
            analysis_type=analysis_type,
            params=params,
            revision_ids=revision_ids,
        )

        revision_paths = {}
        for role, rev_id in revision_ids.items():
            rev = self.db.query(DatasetRevision).filter(DatasetRevision.id == rev_id).first()
            revision_paths[role] = rev.storage_path

        from app.tasks.analysis_tasks import run_analysis_task

        task = run_analysis_task.delay(
            run_id=run.id,
            analysis_type=analysis_type,
            params=params,
            revision_paths=revision_paths,
        )

        self.run_repo.update_status(run.id, "queued", celery_task_id=str(task.id) if task else None)

        return AnalysisRunAcceptedResponse(
            run_id=run.id,
            status="queued",
            analysis_type=analysis_type,
        )

    def get_run(self, run_id: str, user_id: str):
        run = self.run_repo.get_by_id(run_id)
        if not run or run.user_id != user_id:
            raise NotFoundError("Analysis run not found")
        return run

    def get_result(self, run_id: str, user_id: str) -> dict[str, Any] | None:
        run = self.get_run(run_id, user_id)
        if run.result:
            return json.loads(run.result)
        return None

    def cancel_run(self, run_id: str, user_id: str) -> None:
        run = self.get_run(run_id, user_id)
        if run.status in ("queued", "running"):
            self.run_repo.update_status(run.id, "cancelled")
