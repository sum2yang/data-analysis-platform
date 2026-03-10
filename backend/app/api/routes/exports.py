import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.api.deps.auth import get_current_user
from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.analysis_runs import AnalysisRunRepository
from app.repositories.exports import ExportRepository
from app.schemas.chart_contract import ChartContract
from app.schemas.export import (
    ExportResponse,
    FigureExportRequest,
    TableExportRequest,
)
from app.services.chart_contract_service import ChartContractService
from app.tasks.export_tasks import export_figure_task, export_table_task

__all__ = ["router"]

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/figures", response_model=ExportResponse)
def export_figure(
    body: FigureExportRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    run_repo = AnalysisRunRepository(db)
    run = run_repo.get_by_id(body.run_id)
    if not run or run.user_id != user.id:
        raise NotFoundError("Analysis run not found")
    if run.status != "succeeded" or not run.result:
        raise NotFoundError("Result not available")

    result = json.loads(run.result)
    chart_contracts = result.get("chart_contracts", [])

    if body.chart_index >= len(chart_contracts):
        contract_obj = ChartContractService.build_bar_error_letters(result)
        if not contract_obj:
            raise NotFoundError("No chart available for this result")
    else:
        contract_obj = ChartContract.model_validate(chart_contracts[body.chart_index])

    settings = get_settings()
    file_id = str(uuid.uuid4())
    output_path = settings.ARTIFACT_ROOT / "exports" / f"{file_id}.{body.format}"

    export_repo = ExportRepository(db)
    export = export_repo.create(
        run_id=body.run_id,
        export_type="figure",
        format=body.format,
        file_path=str(output_path),
        status="pending",
    )

    export_figure_task.delay(
        export_id=export.id,
        contract_dict=contract_obj.model_dump(),
        output_path=str(output_path),
        fmt=body.format,
    )

    return ExportResponse.model_validate(export)


@router.post("/tables", response_model=ExportResponse)
def export_table(
    body: TableExportRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    run_repo = AnalysisRunRepository(db)
    run = run_repo.get_by_id(body.run_id)
    if not run or run.user_id != user.id:
        raise NotFoundError("Analysis run not found")
    if run.status != "succeeded" or not run.result:
        raise NotFoundError("Result not available")

    result = json.loads(run.result)
    tables = result.get("tables", {})

    if body.table_key:
        if body.table_key not in tables:
            raise NotFoundError(f"Table '{body.table_key}' not found")
        data = {body.table_key: tables[body.table_key]}
    else:
        data = tables

    settings = get_settings()
    file_id = str(uuid.uuid4())
    output_path = settings.ARTIFACT_ROOT / "exports" / f"{file_id}.{body.format}"

    export_repo = ExportRepository(db)
    export = export_repo.create(
        run_id=body.run_id,
        export_type="table",
        format=body.format,
        file_path=str(output_path),
        status="pending",
    )

    export_table_task.delay(
        export_id=export.id,
        data=data,
        output_path=str(output_path),
        fmt=body.format,
    )

    return ExportResponse.model_validate(export)


@router.get("/{export_id}", response_model=ExportResponse)
def get_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    export_repo = ExportRepository(db)
    export = export_repo.get_by_id(export_id)
    if not export:
        raise NotFoundError("Export not found")
    run_repo = AnalysisRunRepository(db)
    run = run_repo.get_by_id(export.run_id)
    if not run or run.user_id != user.id:
        raise NotFoundError("Export not found")
    return ExportResponse.model_validate(export)


@router.get("/{export_id}/download")
def download_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    export_repo = ExportRepository(db)
    export = export_repo.get_by_id(export_id)
    if not export:
        raise NotFoundError("Export not found")
    run_repo = AnalysisRunRepository(db)
    run = run_repo.get_by_id(export.run_id)
    if not run or run.user_id != user.id:
        raise NotFoundError("Export not found")
    if export.status != "ready":
        raise NotFoundError("Export not ready")
    path = Path(export.file_path)
    if not path.exists():
        raise NotFoundError("Export file not found on disk")
    return FileResponse(
        path,
        filename=f"{run.analysis_type}_{export.id[:8]}.{export.format}",
    )
