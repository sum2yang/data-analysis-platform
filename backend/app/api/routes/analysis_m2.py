from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis_m2 import AssumptionCheckRequest, DescriptiveStatsRequest
from app.schemas.analysis_run import AnalysisRunAcceptedResponse
from app.services.analysis_service import AnalysisService

__all__ = ["router"]

router = APIRouter(prefix="/analyses", tags=["analysis-m2"])


@router.post("/descriptive", response_model=AnalysisRunAcceptedResponse)
def submit_descriptive(
    body: DescriptiveStatsRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="descriptive",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/assumptions", response_model=AnalysisRunAcceptedResponse)
def submit_assumptions(
    body: AssumptionCheckRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="assumptions",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )
