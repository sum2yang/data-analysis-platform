from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.dataset_revision import DatasetRevision
from app.models.user import User
from app.schemas.analysis_run import AnalysisRunAcceptedResponse
from app.services.analysis_service import AnalysisService
from app.tasks.analysis_tasks import ANALYSIS_TYPE_TO_ENDPOINT

__all__ = ["router"]

router = APIRouter(prefix="/analyses", tags=["analysis-dispatch"])


class UnifiedAnalysisRequest(BaseModel):
    dataset_id: str
    analysis_type: str
    params: dict[str, Any] = {}


# Map frontend shorthand names to backend internal analysis_type keys.
# None means the value is resolved dynamically from params.
ANALYSIS_TYPE_ALIASES: dict[str, str | None] = {
    "anova": "anova_one_way",
    "nonparametric": None,
    "regression": None,
    "rda_cca": None,
}

# Param keys used only for routing, not passed to the R backend.
_ROUTING_KEYS = frozenset({"test", "method"})


def resolve_analysis_type(raw_type: str, params: dict[str, Any]) -> str:
    """Resolve a frontend analysis type name to a backend internal key."""
    if raw_type not in ANALYSIS_TYPE_ALIASES:
        return raw_type

    alias = ANALYSIS_TYPE_ALIASES[raw_type]
    if alias is not None:
        return alias

    if raw_type == "nonparametric":
        return params.get("test", "kruskal_wallis")
    if raw_type == "regression":
        method = params.get("method", "lm")
        return "regression_linear" if method == "lm" else "regression_glm"
    if raw_type == "rda_cca":
        return params.get("method", "rda")

    return raw_type


@router.post("/run", response_model=AnalysisRunAcceptedResponse)
def unified_submit(
    body: UnifiedAnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Resolve dataset_id to the latest revision
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == body.dataset_id, Dataset.owner_id == user.id)
        .first()
    )
    if not dataset:
        raise NotFoundError("Dataset not found")

    revision = (
        db.query(DatasetRevision)
        .filter(DatasetRevision.dataset_id == body.dataset_id)
        .order_by(DatasetRevision.created_at.desc())
        .first()
    )
    if not revision:
        raise NotFoundError("No revision found for dataset")

    analysis_type = resolve_analysis_type(body.analysis_type, body.params)

    # Validate that the resolved type is actually supported
    if analysis_type not in ANALYSIS_TYPE_TO_ENDPOINT:
        raise ValidationError(f"Unsupported analysis type: {analysis_type}")

    # Strip routing-only keys so they don't leak into R params
    clean_params = {
        k: v for k, v in body.params.items() if k not in _ROUTING_KEYS
    }

    svc = AnalysisService(db)
    return svc.submit(
        user_id=user.id,
        analysis_type=analysis_type,
        params=clean_params,
        revision_ids={"primary": revision.id},
    )
