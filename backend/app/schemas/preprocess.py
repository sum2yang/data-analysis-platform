from datetime import datetime
from typing import Any

from pydantic import BaseModel

__all__ = [
    "JoinRequest",
    "TransformRequest",
    "SchemaOverrideRequest",
    "OperationResponse",
    "PreprocessResultResponse",
]


class JoinRequest(BaseModel):
    left_revision_id: str
    right_revision_id: str
    left_on: str
    right_on: str
    how: str = "inner"  # inner, left, right, outer


class TransformRequest(BaseModel):
    revision_id: str
    op_type: str
    params: dict[str, Any] = {}


class SchemaOverrideRequest(BaseModel):
    revision_id: str
    column: str
    target_type: str  # numeric, categorical, text


class OperationResponse(BaseModel):
    id: str
    revision_id: str
    op_type: str
    op_params: str | None
    op_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PreprocessResultResponse(BaseModel):
    revision_id: str
    row_count: int
    col_count: int
    report: dict[str, Any] | None = None
