import json

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis_run import (
    AnalysisRunDetailResponse,
    AnalysisRunStatusResponse,
    AnalysisResultEnvelope,
)
from app.services.analysis_service import AnalysisService

__all__ = ["router"]

router = APIRouter(prefix="/analysis-runs", tags=["analysis-runs"])


@router.get("", response_model=list[AnalysisRunStatusResponse])
def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    runs, _total = svc.run_repo.get_by_user(user.id, page=page, page_size=page_size)
    return [AnalysisRunStatusResponse.model_validate(r) for r in runs]


@router.get("/{run_id}", response_model=AnalysisRunStatusResponse)
def get_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    run = svc.get_run(run_id, user.id)
    return AnalysisRunStatusResponse.model_validate(run)


@router.get("/{run_id}/result", response_model=AnalysisResultEnvelope)
def get_result(
    run_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    run = svc.get_run(run_id, user.id)
    if run.status != "succeeded" or not run.result:
        raise NotFoundError("Result not available")
    return AnalysisResultEnvelope.model_validate(json.loads(run.result))


@router.post("/{run_id}/cancel", status_code=204)
def cancel_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    svc.cancel_run(run_id, user.id)
