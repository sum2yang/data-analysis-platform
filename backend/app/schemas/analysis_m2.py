from pydantic import BaseModel, Field

__all__ = [
    "DescriptiveStatsRequest",
    "AssumptionCheckRequest",
]


class DescriptiveStatsRequest(BaseModel):
    revision_id: str
    response_columns: list[str] = Field(min_length=1)
    group_column: str | None = None


class AssumptionCheckRequest(BaseModel):
    revision_id: str
    response_columns: list[str] = Field(min_length=1)
    group_column: str | None = None
    tests: list[str] = Field(
        default=["shapiro", "levene"],
        description="shapiro, kolmogorov_smirnov, levene, bartlett",
    )
