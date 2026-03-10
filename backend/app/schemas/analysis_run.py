from datetime import datetime

from pydantic import BaseModel

__all__ = [
    "AnalysisRunAcceptedResponse",
    "AnalysisRunStatusResponse",
    "AnalysisRunDetailResponse",
    "AnalysisResultEnvelope",
]


class AnalysisRunAcceptedResponse(BaseModel):
    run_id: str
    status: str
    analysis_type: str


class AnalysisRunStatusResponse(BaseModel):
    id: str
    analysis_type: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class AnalysisResultEnvelope(BaseModel):
    analysis_type: str
    engine: str = "R"
    summary: dict | None = None
    tables: dict = {}
    assumptions: dict | None = None
    warnings: list[str] = []
    chart_contracts: list[dict] = []


class AnalysisRunDetailResponse(BaseModel):
    id: str
    analysis_type: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result: AnalysisResultEnvelope | None = None

    model_config = {"from_attributes": True}
