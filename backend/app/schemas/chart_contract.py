from pydantic import BaseModel

__all__ = [
    "ChartContract",
    "AxisConfig",
    "SeriesConfig",
    "AnnotationConfig",
]


class AxisConfig(BaseModel):
    label: str
    type: str = "category"  # category, value
    data: list | None = None


class AnnotationConfig(BaseModel):
    type: str  # letter, line, band
    position: dict | None = None
    text: str | None = None
    style: dict | None = None


class SeriesConfig(BaseModel):
    name: str
    type: str  # bar, scatter, line, boxplot, violin
    data: list
    error_bars: list | None = None
    color: str | None = None


class ChartContract(BaseModel):
    chart_type: str  # bar_error_letters, boxplot, violin, heatmap, scatter, biplot
    title: str = ""
    x_axis: AxisConfig | None = None
    y_axis: AxisConfig | None = None
    series: list[SeriesConfig] = []
    annotations: list[AnnotationConfig] = []
    legend: list[str] = []
    metadata: dict = {}
