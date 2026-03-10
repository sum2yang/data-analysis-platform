from __future__ import annotations

import logging
from typing import Any

from app.workers.celery_worker import celery_app
from app.db.session import SessionLocal
from app.repositories.exports import ExportRepository
from app.services.export_service import ExportService
from app.schemas.chart_contract import ChartContract

__all__ = ["export_figure_task", "export_table_task"]

logger = logging.getLogger(__name__)


@celery_app.task(name="export_figure", bind=True, max_retries=0)
def export_figure_task(
    self,
    *,
    export_id: str,
    contract_dict: dict[str, Any],
    output_path: str,
    fmt: str = "png",
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        repo = ExportRepository(db)
        from pathlib import Path

        contract = ChartContract.model_validate(contract_dict)
        ExportService.render_figure(contract, Path(output_path), fmt=fmt)
        repo.update_status(export_id, "ready")
        return {"status": "ready", "path": output_path}
    except Exception as e:
        logger.exception("Export figure failed: %s", export_id)
        try:
            repo.update_status(export_id, "failed")
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="export_table", bind=True, max_retries=0)
def export_table_task(
    self,
    *,
    export_id: str,
    data: dict[str, Any],
    output_path: str,
    fmt: str = "xlsx",
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        repo = ExportRepository(db)
        from pathlib import Path

        ExportService.export_table(data, Path(output_path), fmt=fmt)
        repo.update_status(export_id, "ready")
        return {"status": "ready", "path": output_path}
    except Exception as e:
        logger.exception("Export table failed: %s", export_id)
        try:
            repo.update_status(export_id, "failed")
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        db.close()
