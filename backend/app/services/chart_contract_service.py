from __future__ import annotations

import logging
from typing import Any

from app.schemas.chart_contract import (
    AnnotationConfig,
    AxisConfig,
    ChartContract,
    SeriesConfig,
)

__all__ = ["ChartContractService"]

logger = logging.getLogger(__name__)


class ChartContractService:
    @staticmethod
    def build_bar_error_letters(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        summary = tables.get("descriptive") or tables.get("summary")
        posthoc = tables.get("posthoc") or tables.get("letters")
        if not summary:
            return None

        groups = [row.get("group", str(i)) for i, row in enumerate(summary)]
        means = [row.get("mean", 0) for row in summary]
        sds = [row.get("sd", 0) for row in summary]

        annotations = []
        if posthoc:
            for i, row in enumerate(posthoc):
                letter = row.get("letter", "")
                if letter:
                    annotations.append(
                        AnnotationConfig(
                            type="letter",
                            position={"x": i, "y": means[i] + sds[i]},
                            text=letter,
                        )
                    )

        return ChartContract(
            chart_type="bar_error_letters",
            title=result.get("analysis_type", ""),
            x_axis=AxisConfig(label="Group", type="category", data=groups),
            y_axis=AxisConfig(label="Value", type="value"),
            series=[
                SeriesConfig(
                    name="Mean",
                    type="bar",
                    data=means,
                    error_bars=sds,
                )
            ],
            annotations=annotations,
        )

    @staticmethod
    def build_boxplot(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        boxplot_data = tables.get("boxplot")
        if not boxplot_data:
            return None

        groups = [row.get("group", "") for row in boxplot_data]
        data = [
            [
                row.get("min", 0),
                row.get("q1", 0),
                row.get("median", 0),
                row.get("q3", 0),
                row.get("max", 0),
            ]
            for row in boxplot_data
        ]

        return ChartContract(
            chart_type="boxplot",
            x_axis=AxisConfig(label="Group", type="category", data=groups),
            y_axis=AxisConfig(label="Value", type="value"),
            series=[SeriesConfig(name="Distribution", type="boxplot", data=data)],
        )

    @staticmethod
    def build_violin(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        violin_data = tables.get("violin")
        if not violin_data:
            return None

        groups = [row.get("group", "") for row in violin_data]
        data = [row.get("values", []) for row in violin_data]

        return ChartContract(
            chart_type="violin",
            x_axis=AxisConfig(label="Group", type="category", data=groups),
            y_axis=AxisConfig(label="Value", type="value"),
            series=[SeriesConfig(name="Distribution", type="violin", data=data)],
        )

    @staticmethod
    def build_heatmap(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        matrix = tables.get("correlation_matrix")
        if not matrix:
            return None

        variables = [row.get("variable", str(i)) for i, row in enumerate(matrix)]
        series_data = []
        for r, row in enumerate(matrix):
            values = row.get("values", [])
            for c, val in enumerate(values):
                series_data.append([r, c, val])

        return ChartContract(
            chart_type="heatmap",
            x_axis=AxisConfig(label="Variable", type="category", data=variables),
            y_axis=AxisConfig(label="Variable", type="category", data=variables),
            series=[SeriesConfig(name="Correlation", type="heatmap", data=series_data)],
            metadata={"variables": variables, "value_range": [-1, 1]},
        )

    @staticmethod
    def build_ordination_scatter(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        scores = tables.get("scores")
        if not scores:
            return None

        summary = result.get("summary", {})
        explained = summary.get("explained_variance", [])
        x_label = f"PC1 ({explained[0]}%)" if len(explained) > 0 else "Axis1"
        y_label = f"PC2 ({explained[1]}%)" if len(explained) > 1 else "Axis2"

        groups: dict[str, list] = {}
        for row in scores:
            g = row.get("group", "default")
            groups.setdefault(g, []).append([row.get("Axis1", 0), row.get("Axis2", 0)])

        series = [
            SeriesConfig(name=g, type="scatter", data=pts)
            for g, pts in groups.items()
        ]

        metadata: dict[str, Any] = {"explained_variance": explained}
        ellipses = tables.get("ellipses")
        if ellipses:
            metadata["ellipses"] = ellipses

        return ChartContract(
            chart_type="ordination_scatter",
            x_axis=AxisConfig(label=x_label, type="value"),
            y_axis=AxisConfig(label=y_label, type="value"),
            series=series,
            legend=list(groups.keys()),
            metadata=metadata,
        )

    @staticmethod
    def build_regression_plot(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        summary = result.get("summary", {})
        fitted = tables.get("fitted_values")
        if not fitted:
            return None

        observed = [[row.get("x", 0), row.get("y", 0)] for row in fitted]
        line = [[row.get("x", 0), row.get("y_hat", 0)] for row in fitted]

        coefficients = tables.get("coefficients", [])
        equation = summary.get("equation", "")
        if not equation and coefficients:
            terms = []
            for coef in coefficients:
                terms.append(f"{coef.get('term', '')}={coef.get('estimate', '')}")
            equation = ", ".join(terms)

        return ChartContract(
            chart_type="regression_plot",
            x_axis=AxisConfig(label="X", type="value"),
            y_axis=AxisConfig(label="Y", type="value"),
            series=[
                SeriesConfig(name="Observed", type="scatter", data=observed),
                SeriesConfig(name="Fitted", type="line", data=line),
            ],
            metadata={
                "r_squared": summary.get("r_squared"),
                "p_value": summary.get("p_value"),
                "equation": equation,
            },
        )

    @staticmethod
    def build_rda_biplot(result: dict[str, Any]) -> ChartContract | None:
        tables = result.get("tables", {})
        site_scores = tables.get("site_scores")
        arrows = tables.get("biplot_arrows")
        if not site_scores or not arrows:
            return None

        summary = result.get("summary", {})
        explained = summary.get("explained_variance", [])
        x_label = f"RDA1 ({explained[0]}%)" if len(explained) > 0 else "RDA1"
        y_label = f"RDA2 ({explained[1]}%)" if len(explained) > 1 else "RDA2"

        groups: dict[str, list] = {}
        for row in site_scores:
            g = row.get("group", "default")
            groups.setdefault(g, []).append([row.get("Axis1", 0), row.get("Axis2", 0)])

        series = [
            SeriesConfig(name=g, type="scatter", data=pts)
            for g, pts in groups.items()
        ]

        annotations = [
            AnnotationConfig(
                type="arrow",
                position={
                    "from": {"x": 0, "y": 0},
                    "to": {"x": a.get("Axis1", 0), "y": a.get("Axis2", 0)},
                },
                text=a.get("variable", ""),
            )
            for a in arrows
        ]

        return ChartContract(
            chart_type="rda_biplot",
            x_axis=AxisConfig(label=x_label, type="value"),
            y_axis=AxisConfig(label=y_label, type="value"),
            series=series,
            annotations=annotations,
            legend=list(groups.keys()),
            metadata={"explained_variance": explained},
        )
