from pydantic import BaseModel, Field

__all__ = [
    "CorrelationRequest",
    "LinearRegressionRequest",
    "GlmRequest",
]


class CorrelationRequest(BaseModel):
    revision_id: str
    columns: list[str] = Field(min_length=2)
    method: str = "pearson"  # pearson, spearman
    missing_strategy: str = "pairwise"  # pairwise, listwise


class LinearRegressionRequest(BaseModel):
    revision_id: str
    response_column: str
    predictor_columns: list[str] = Field(min_length=1)


class GlmRequest(BaseModel):
    revision_id: str
    response_column: str
    predictor_columns: list[str] = Field(min_length=1)
    family: str = "poisson"  # poisson, binomial
    link: str | None = None
