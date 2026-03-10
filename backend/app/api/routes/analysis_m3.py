from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis_m3 import (
    KruskalWallisRequest,
    MannWhitneyRequest,
    MultiWayAnovaRequest,
    OneWayAnovaRequest,
    TTestRequest,
    WelchAnovaRequest,
)
from app.schemas.analysis_run import AnalysisRunAcceptedResponse
from app.services.analysis_service import AnalysisService

__all__ = ["router"]

router = APIRouter(prefix="/analyses", tags=["analysis-m3"])


@router.post("/t-test", response_model=AnalysisRunAcceptedResponse)
def submit_ttest(
    body: TTestRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="t_test",
        params=body.model_dump(exclude={"revision_id"}),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/anova/one-way", response_model=AnalysisRunAcceptedResponse)
def submit_anova_one_way(
    body: OneWayAnovaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="anova_one_way",
        params=body.model_dump(exclude={"revision_id"}),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/anova/multi-way", response_model=AnalysisRunAcceptedResponse)
def submit_anova_multi_way(
    body: MultiWayAnovaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="anova_multi_way",
        params=body.model_dump(exclude={"revision_id"}),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/anova/welch", response_model=AnalysisRunAcceptedResponse)
def submit_anova_welch(
    body: WelchAnovaRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="anova_welch",
        params=body.model_dump(exclude={"revision_id"}),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/nonparametric/kruskal-wallis", response_model=AnalysisRunAcceptedResponse)
def submit_kruskal_wallis(
    body: KruskalWallisRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="kruskal_wallis",
        params=body.model_dump(exclude={"revision_id"}),
        revision_ids={"primary": body.revision_id},
    )


@router.post("/nonparametric/mann-whitney", response_model=AnalysisRunAcceptedResponse)
def submit_mann_whitney(
    body: MannWhitneyRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type="mann_whitney",
        params=body.model_dump(exclude={"revision_id"}),
        revision_ids={"primary": body.revision_id},
    )
