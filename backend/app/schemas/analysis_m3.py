from pydantic import BaseModel, Field

__all__ = [
    "TTestRequest",
    "OneWayAnovaRequest",
    "MultiWayAnovaRequest",
    "WelchAnovaRequest",
    "KruskalWallisRequest",
    "MannWhitneyRequest",
]


class TTestRequest(BaseModel):
    revision_id: str
    response_column: str
    group_column: str | None = None
    test_type: str = "independent"  # independent, paired, one_sample
    mu: float = 0.0
    alternative: str = "two-sided"  # two-sided, less, greater


class OneWayAnovaRequest(BaseModel):
    revision_id: str
    response_column: str
    group_column: str
    posthoc_method: str = "tukey"  # tukey, duncan, lsd
    alpha: float = Field(default=0.05, gt=0, lt=1)


class MultiWayAnovaRequest(BaseModel):
    revision_id: str
    response_column: str
    factor_columns: list[str] = Field(min_length=2)
    anova_type: int = Field(default=2, ge=1, le=3)  # Type II or III


class WelchAnovaRequest(BaseModel):
    revision_id: str
    response_column: str
    group_column: str
    posthoc_method: str = "games_howell"


class KruskalWallisRequest(BaseModel):
    revision_id: str
    response_column: str
    group_column: str
    alpha: float = Field(default=0.05, gt=0, lt=1)


class MannWhitneyRequest(BaseModel):
    revision_id: str
    response_column: str
    group_column: str
    alternative: str = "two-sided"
