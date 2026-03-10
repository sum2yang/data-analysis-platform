from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.analysis_input import AnalysisInput
from app.models.analysis_run import AnalysisRun
from app.models.run_event import RunEvent

__all__ = ["AnalysisRunRepository"]


class AnalysisRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: str,
        analysis_type: str,
        params: dict | None = None,
        revision_ids: dict[str, str] | None = None,
    ) -> AnalysisRun:
        run = AnalysisRun(
            user_id=user_id,
            analysis_type=analysis_type,
            status="queued",
            params=json.dumps(params) if params else None,
        )
        self.db.add(run)
        self.db.flush()

        if revision_ids:
            for role, rev_id in revision_ids.items():
                inp = AnalysisInput(run_id=run.id, revision_id=rev_id, role=role)
                self.db.add(inp)

        self._add_event(run.id, "created")
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: str) -> AnalysisRun | None:
        return self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()

    def get_by_user(
        self, user_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[AnalysisRun], int]:
        q = self.db.query(AnalysisRun).filter(AnalysisRun.user_id == user_id)
        total = q.count()
        items = (
            q.order_by(AnalysisRun.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def update_status(
        self,
        run_id: str,
        status: str,
        *,
        error_message: str | None = None,
        result: dict | None = None,
        celery_task_id: str | None = None,
    ) -> AnalysisRun | None:
        run = self.get_by_id(run_id)
        if not run:
            return None

        run.status = status
        if status == "running" and not run.started_at:
            run.started_at = datetime.utcnow()
        if status in ("succeeded", "failed", "cancelled"):
            run.completed_at = datetime.utcnow()
        if error_message:
            run.error_message = error_message
        if result:
            run.result = json.dumps(result)
        if celery_task_id:
            run.celery_task_id = celery_task_id

        self._add_event(run.id, status, payload=error_message)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _add_event(
        self, run_id: str, event_type: str, *, payload: str | None = None
    ) -> None:
        event = RunEvent(run_id=run_id, event_type=event_type, payload=payload)
        self.db.add(event)
