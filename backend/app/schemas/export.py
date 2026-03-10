from typing import Literal

from pydantic import BaseModel

__all__ = [
    "FigureExportRequest",
    "TableExportRequest",
    "ExportResponse",
]


class FigureExportRequest(BaseModel):
    run_id: str
    chart_index: int = 0
    format: Literal["png", "svg", "pdf"] = "png"


class TableExportRequest(BaseModel):
    run_id: str
    table_key: str | None = None  # specific table name, or None for all
    format: Literal["csv", "xlsx"] = "xlsx"


class ExportResponse(BaseModel):
    id: str
    export_type: str
    format: str
    status: str

    model_config = {"from_attributes": True}
