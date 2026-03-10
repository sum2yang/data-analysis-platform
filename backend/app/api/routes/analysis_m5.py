from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis_m5 import (
    CcaRequest,
    NmdsRequest,
    PcaRequest,
    PcoaRequest,
    RdaRequest,
)
from app.schemas.analysis_run import AnalysisRunAcceptedResponse
from app.services.analysis_service import AnalysisService

__all__ = ["router"]

router = APIRouter(prefix="/analyses/ordination", tags=["analysis-m5"])


@router.post("/pca", response_model=AnalysisRunAcceptedResponse)
def submit_pca(
    body: PcaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="pca",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/pcoa", response_model=AnalysisRunAcceptedResponse)
def submit_pcoa(
    body: PcoaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="pcoa",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/nmds", response_model=AnalysisRunAcceptedResponse)
def submit_nmds(
    body: NmdsRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="nmds",
        params=body.model_dump(),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/rda", response_model=AnalysisRunAcceptedResponse)
def submit_rda(
    body: RdaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="rda",
        params=body.model_dump(),
        revision_ids={
            "primary": body.revision_id,
            "environment": body.env_revision_id,
        },
    )


@router.post("/cca", response_model=AnalysisRunAcceptedResponse)
def submit_cca(
    body: CcaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="cca",
        params=body.model_dump(),
        revision_ids={
            "primary": body.revision_id,
            "environment": body.env_revision_id,
        },
    )
