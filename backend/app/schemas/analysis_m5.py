from pydantic import BaseModel, Field

__all__ = [
    "PcaRequest",
    "PcoaRequest",
    "NmdsRequest",
    "RdaRequest",
    "CcaRequest",
]


class PcaRequest(BaseModel):
    revision_id: str
    columns: list[str] = Field(min_length=2)
    n_components: int = Field(default=2, ge=2)
    scale: bool = True
    group_column: str | None = None


class PcoaRequest(BaseModel):
    revision_id: str
    columns: list[str] = Field(min_length=2)
    distance_method: str = "bray"  # bray, jaccard, euclidean
    n_components: int = Field(default=2, ge=2)
    group_column: str | None = None


class NmdsRequest(BaseModel):
    revision_id: str
    columns: list[str] = Field(min_length=2)
    distance_method: str = "bray"
    n_components: int = Field(default=2, ge=2)
    max_iter: int = 500
    group_column: str | None = None


class RdaRequest(BaseModel):
    revision_id: str
    response_columns: list[str] = Field(min_length=2)
    env_revision_id: str
    env_columns: list[str] = Field(min_length=1)
    sample_key: str
    group_column: str | None = None


class CcaRequest(BaseModel):
    revision_id: str
    response_columns: list[str] = Field(min_length=2)
    env_revision_id: str
    env_columns: list[str] = Field(min_length=1)
    sample_key: str
    group_column: str | None = None
