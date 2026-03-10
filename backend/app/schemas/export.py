from pydantic import BaseModel

__all__ = [
    "FigureExportRequest",
    "TableExportRequest",
    "ExportResponse",
]


class FigureExportRequest(BaseModel):
    run_id: str
    chart_index: int = 0
    format: str = "png"  # png, svg, pdf


class TableExportRequest(BaseModel):
    run_id: str
    table_key: str | None = None  # specific table name, or None for all
    format: str = "xlsx"  # csv, xlsx


class ExportResponse(BaseModel):
    id: str
    export_type: str
    format: str
    status: str
    file_path: str | None = None

    model_config = {"from_attributes": True}
