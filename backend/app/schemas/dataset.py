from datetime import datetime

from pydantic import BaseModel

__all__ = [
    "DatasetUploadResponse",
    "DatasetListItem",
    "DatasetDetailResponse",
    "DatasetRevisionResponse",
    "DatasetPreviewResponse",
    "DatasetProfileResponse",
    "DatasetColumnResponse",
]


class DatasetColumnResponse(BaseModel):
    id: str
    name: str
    dtype: str
    position: int
    null_count: int
    unique_count: int

    model_config = {"from_attributes": True}


class DatasetRevisionResponse(BaseModel):
    id: str
    version: int
    row_count: int
    col_count: int
    source_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetUploadResponse(BaseModel):
    id: str
    name: str
    revision_id: str
    row_count: int
    col_count: int
    columns: list[DatasetColumnResponse]


class DatasetListItem(BaseModel):
    id: str
    name: str
    original_filename: str
    file_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None
    original_filename: str
    file_type: str
    created_at: datetime
    updated_at: datetime
    revisions: list[DatasetRevisionResponse]

    model_config = {"from_attributes": True}


class DatasetPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[list]
    total_rows_shown: int


class DatasetProfileResponse(BaseModel):
    row_count: int
    col_count: int
    columns: dict
