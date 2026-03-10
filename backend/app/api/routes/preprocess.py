from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.user import User
from app.repositories.datasets import DatasetRepository
from app.schemas.preprocess import (
    JoinRequest,
    OperationResponse,
    PreprocessResultResponse,
    SchemaOverrideRequest,
    TransformRequest,
)
from app.services.dataset_version_service import DatasetVersionService
from app.services.join_service import JoinService
from app.services.operation_history_service import OperationHistoryService
from app.services.transform_service import TransformService

__all__ = ["router"]

router = APIRouter(prefix="/preprocess", tags=["preprocess"])


def _load_revision_df(repo: DatasetRepository, revision_id: str, user_id: str) -> pd.DataFrame:
    rev = repo.get_revision(revision_id)
    if not rev:
        raise NotFoundError(f"Revision not found: {revision_id}")
    ds = repo.get_by_id(rev.dataset_id)
    if not ds or ds.owner_id != user_id:
        raise NotFoundError("Dataset not found")
    return pd.read_csv(rev.storage_path), rev, ds


@router.post("/join", response_model=PreprocessResultResponse)
def join_datasets(
    body: JoinRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    left_df, left_rev, left_ds = _load_revision_df(repo, body.left_revision_id, user.id)
    right_df, right_rev, right_ds = _load_revision_df(repo, body.right_revision_id, user.id)

    if body.left_on not in left_df.columns:
        raise ValidationError(f"Column '{body.left_on}' not in left dataset")
    if body.right_on not in right_df.columns:
        raise ValidationError(f"Column '{body.right_on}' not in right dataset")

    result_df, report = JoinService.join_dataframes(
        left_df, right_df,
        left_on=body.left_on,
        right_on=body.right_on,
        how=body.how,
    )

    version_svc = DatasetVersionService(db)
    new_rev_id = version_svc.create_new_revision(
        dataset_id=left_ds.id,
        parent_revision_id=body.left_revision_id,
        df=result_df,
        source_type="join",
        source_detail={
            "right_dataset_id": right_ds.id,
            "right_revision_id": body.right_revision_id,
            **report,
        },
        user_id=user.id,
    )

    history = OperationHistoryService(db)
    history.record(
        revision_id=new_rev_id,
        op_type="join",
        op_params={
            "left_revision_id": body.left_revision_id,
            "right_revision_id": body.right_revision_id,
            "left_on": body.left_on,
            "right_on": body.right_on,
            "how": body.how,
        },
    )

    return PreprocessResultResponse(
        revision_id=new_rev_id,
        row_count=len(result_df),
        col_count=len(result_df.columns),
        report=report,
    )


@router.post("/transform", response_model=PreprocessResultResponse)
def transform_dataset(
    body: TransformRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    df, rev, ds = _load_revision_df(repo, body.revision_id, user.id)

    result_df = TransformService.apply(df, body.op_type, body.params)

    version_svc = DatasetVersionService(db)
    new_rev_id = version_svc.create_new_revision(
        dataset_id=ds.id,
        parent_revision_id=body.revision_id,
        df=result_df,
        source_type="transform",
        source_detail={"op_type": body.op_type, "params": body.params},
        user_id=user.id,
    )

    history = OperationHistoryService(db)
    history.record(
        revision_id=new_rev_id,
        op_type=body.op_type,
        op_params=body.params,
    )

    return PreprocessResultResponse(
        revision_id=new_rev_id,
        row_count=len(result_df),
        col_count=len(result_df.columns),
    )


@router.post("/schema-override", response_model=PreprocessResultResponse)
def schema_override(
    body: SchemaOverrideRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    transform_body = TransformRequest(
        revision_id=body.revision_id,
        op_type="cast_type",
        params={"column": body.column, "target_type": body.target_type},
    )
    return transform_dataset(transform_body, user=user, db=db)


@router.get("/operations/{revision_id}", response_model=list[OperationResponse])
def list_operations(
    revision_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    rev = repo.get_revision(revision_id)
    if not rev:
        raise NotFoundError("Revision not found")
    ds = repo.get_by_id(rev.dataset_id)
    if not ds or ds.owner_id != user.id:
        raise NotFoundError("Dataset not found")

    history = OperationHistoryService(db)
    ops = history.list_operations(revision_id)
    return [OperationResponse.model_validate(op) for op in ops]
