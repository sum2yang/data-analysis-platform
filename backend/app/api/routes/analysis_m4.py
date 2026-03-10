from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis_m4 import (
    CorrelationRequest,
    GlmRequest,
    LinearRegressionRequest,
)
from app.schemas.analysis_run import AnalysisRunAcceptedResponse
from app.services.analysis_service import AnalysisService

__all__ = ["router"]

router = APIRouter(prefix="/analyses", tags=["analysis-m4"])


@router.post("/correlation", response_model=AnalysisRunAcceptedResponse)
def submit_correlation(
    body: CorrelationRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="correlation",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/regression/linear", response_model=AnalysisRunAcceptedResponse)
def submit_linear_regression(
    body: LinearRegressionRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="regression_linear",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/regression/glm", response_model=AnalysisRunAcceptedResponse)
def submit_glm(
    body: GlmRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="regression_glm",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )
