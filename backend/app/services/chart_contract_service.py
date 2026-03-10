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
    """Builds ChartContract objects from R Plumber analysis results."""

    @staticmethod
    def auto_generate(analysis_type: str, result: dict[str, Any]) -> list[ChartContract]:
        """Auto-generate chart contracts based on analysis type and R result."""
        BUILDERS: dict[str, list] = {
            "anova_one_way": [ChartContractService.build_bar_error_letters],
            "one_way_anova": [ChartContractService.build_bar_error_letters],
            "anova_welch": [ChartContractService.build_bar_error_letters],
            "welch_anova": [ChartContractService.build_bar_error_letters],
            "kruskal_wallis": [ChartContractService.build_bar_error_letters],
            "correlation": [ChartContractService.build_heatmap],
            "pca": [ChartContractService.build_ordination_scatter],
            "pcoa": [ChartContractService.build_ordination_scatter],
            "nmds": [ChartContractService.build_ordination_scatter],
            "rda": [ChartContractService.build_rda_biplot],
            "cca": [ChartContractService.build_rda_biplot],
            "regression_linear": [ChartContractService.build_regression_plot],
            "linear_regression": [ChartContractService.build_regression_plot],
        }
        builders = BUILDERS.get(analysis_type, [])
        contracts: list[ChartContract] = []
        for builder in builders:
            try:
                c = builder(result)
                if c:
                    contracts.append(c)
            except Exception as e:
                logger.warning("Chart contract build failed for %s: %s", analysis_type, e)
        return contracts

    @staticmethod
    def build_bar_error_letters(result: dict[str, Any]) -> ChartContract | None:
        """Build bar+error+letters chart from ANOVA/Kruskal-Wallis group_summary.

        R returns tables.group_summary as list of:
          {group, n, mean, sd, se, median, min, max, letters?}
        Letters are attached directly to each row by R's attach_letters_to_summary().
        Falls back to tables.descriptive if group_summary is absent.
        """
        tables = result.get("tables", {})
        summary = tables.get("group_summary") or tables.get("descriptive")
        if not summary:
            return None

        groups = [row.get("group", str(i)) for i, row in enumerate(summary)]
        means = [row.get("mean", 0) for row in summary]
        sds = [row.get("sd", 0) for row in summary]

        annotations = []
        for i, row in enumerate(summary):
            letter = row.get("letters", "") or row.get("letter", "")
            if letter:
                mean_val = means[i] if i < len(means) else 0
                sd_val = sds[i] if i < len(sds) else 0
                annotations.append(
                    AnnotationConfig(
                        type="letter",
                        position={"x": i, "y": mean_val + sd_val},
                        text=str(letter),
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
        """Build correlation heatmap from R's pairwise correlation output.

        R correlation returns multiple table formats. We accept:
          - tables.pairwise_stats: [{var1, var2, n, correlation, p_value}]
          - tables.pairwise: same shape, alternate key name
          - tables.correlation_long: [{var1, var2, value}]
        We reconstruct a symmetric matrix from these pairs.
        """
        tables = result.get("tables", {})
        pairwise = (
            tables.get("pairwise")
            or tables.get("pairwise_stats")
            or tables.get("correlation_long")
        )
        if not pairwise:
            return None

        # Collect unique variables in order
        seen: set[str] = set()
        variables: list[str] = []
        for pair in pairwise:
            for key in ("var1", "var2"):
                v = pair.get(key, "")
                if v and v not in seen:
                    seen.add(v)
                    variables.append(v)

        if len(variables) < 2:
            return None

        # Build index lookup
        var_idx = {v: i for i, v in enumerate(variables)}
        n = len(variables)

        # Initialize matrix with 1.0 on diagonal
        matrix = [[1.0 if r == c else 0.0 for c in range(n)] for r in range(n)]

        # Fill from pairwise data (symmetric)
        for pair in pairwise:
            v1 = pair.get("var1", "")
            v2 = pair.get("var2", "")
            corr = pair.get("correlation", pair.get("r", pair.get("value", 0.0)))
            if v1 in var_idx and v2 in var_idx:
                i, j = var_idx[v1], var_idx[v2]
                matrix[i][j] = corr
                matrix[j][i] = corr

        # Build [row, col, value] series data for ECharts heatmap
        series_data = []
        for r in range(n):
            for c in range(n):
                series_data.append([r, c, matrix[r][c]])

        return ChartContract(
            chart_type="heatmap",
            x_axis=AxisConfig(label="Variable", type="category", data=variables),
            y_axis=AxisConfig(label="Variable", type="category", data=variables),
            series=[SeriesConfig(name="Correlation", type="heatmap", data=series_data)],
            metadata={"variables": variables, "value_range": [-1, 1]},
        )

    @staticmethod
    def build_ordination_scatter(result: dict[str, Any]) -> ChartContract | None:
        """Build ordination scatter plot from R PCA/PCoA/NMDS output.

        R returns:
          tables.eigenvalues: [{axis:"PC1", eigenvalue, explained_variance, cumulative}]
          tables.scores: [{sample_id, PC1, PC2, ..., group?}]
        Axis names are dynamic: PC (PCA), PCoA (PCoA), NMDS (NMDS).
        """
        tables = result.get("tables", {})
        scores = tables.get("scores")
        if not scores:
            return None

        # Detect axis prefix from eigenvalues or score keys
        eigenvalues = tables.get("eigenvalues", [])
        axis1_name, axis2_name = _detect_axis_names(scores, eigenvalues)

        # Extract explained variance from eigenvalue table
        explained: list[float] = []
        for eig in eigenvalues:
            pct = eig.get("explained_variance", 0)
            explained.append(round(pct * 100, 1) if pct <= 1 else round(pct, 1))

        x_label = f"{axis1_name} ({explained[0]}%)" if len(explained) > 0 else axis1_name
        y_label = f"{axis2_name} ({explained[1]}%)" if len(explained) > 1 else axis2_name

        # Group points by group field
        groups: dict[str, list] = {}
        for row in scores:
            g = row.get("group", "default")
            x = row.get(axis1_name, 0)
            y = row.get(axis2_name, 0)
            groups.setdefault(g, []).append([x, y])

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
        """Build regression plot from R linear regression output.

        R returns:
          tables.coefficients: [{term, estimate, std_error, t_value, p_value}]
          summary: {r_squared, adj_r_squared, formula, ...}
        Note: R does NOT return fitted_values table. We build the equation
        from coefficients and let the frontend render the regression line.
        """
        tables = result.get("tables", {})
        summary = result.get("summary", {})
        coefficients = tables.get("coefficients", [])
        if not coefficients:
            return None

        # Build equation string from coefficients
        equation = summary.get("formula", "")
        if not equation:
            terms = []
            for coef in coefficients:
                term = coef.get("term", "")
                est = coef.get("estimate", "")
                if term and est != "":
                    terms.append(f"{term}={est}")
            equation = ", ".join(terms)

        # Build series data from coefficients (intercept + slope info)
        coef_data = []
        for coef in coefficients:
            coef_data.append({
                "term": coef.get("term", ""),
                "estimate": coef.get("estimate", 0),
                "std_error": coef.get("std_error", 0),
                "p_value": coef.get("p_value", None),
            })

        return ChartContract(
            chart_type="regression_plot",
            x_axis=AxisConfig(label="X", type="value"),
            y_axis=AxisConfig(label="Y", type="value"),
            series=[
                SeriesConfig(name="Coefficients", type="bar", data=coef_data),
            ],
            metadata={
                "r_squared": summary.get("r_squared"),
                "adj_r_squared": summary.get("adj_r_squared"),
                "p_value": summary.get("p_value"),
                "equation": equation,
                "coefficients": coef_data,
            },
        )

    @staticmethod
    def build_rda_biplot(result: dict[str, Any]) -> ChartContract | None:
        """Build RDA/CCA biplot from R output.

        R returns:
          tables.biplot_scores: [{variable, RDA1, RDA2, ...}] (NOT biplot_arrows)
          tables.site_scores: [{sample_id, RDA1, RDA2, ..., group?}]
          tables.eigenvalues: [{axis, eigenvalue, explained_variance, cumulative}]
        Axis prefix: RDA (for RDA), CCA (for CCA).
        """
        tables = result.get("tables", {})
        site_scores = tables.get("site_scores")
        biplot_scores = tables.get("biplot_scores")
        if not site_scores:
            return None

        eigenvalues = tables.get("eigenvalues", [])
        axis1_name, axis2_name = _detect_axis_names(site_scores, eigenvalues)

        # Extract explained variance from eigenvalue table
        explained: list[float] = []
        for eig in eigenvalues:
            pct = eig.get("explained_variance", 0)
            explained.append(round(pct * 100, 1) if pct <= 1 else round(pct, 1))

        x_label = f"{axis1_name} ({explained[0]}%)" if len(explained) > 0 else axis1_name
        y_label = f"{axis2_name} ({explained[1]}%)" if len(explained) > 1 else axis2_name

        # Group site scores by group field
        groups: dict[str, list] = {}
        for row in site_scores:
            g = row.get("group", "default")
            x = row.get(axis1_name, 0)
            y = row.get(axis2_name, 0)
            groups.setdefault(g, []).append([x, y])

        series = [
            SeriesConfig(name=g, type="scatter", data=pts)
            for g, pts in groups.items()
        ]

        # Build arrow annotations from biplot_scores
        annotations = []
        if biplot_scores:
            for bp in biplot_scores:
                annotations.append(
                    AnnotationConfig(
                        type="arrow",
                        position={
                            "from": {"x": 0, "y": 0},
                            "to": {
                                "x": bp.get(axis1_name, 0),
                                "y": bp.get(axis2_name, 0),
                            },
                        },
                        text=bp.get("variable", ""),
                    )
                )

        metadata: dict[str, Any] = {"explained_variance": explained}
        ellipses = tables.get("ellipses")
        if ellipses:
            metadata["ellipses"] = ellipses

        return ChartContract(
            chart_type="rda_biplot",
            x_axis=AxisConfig(label=x_label, type="value"),
            y_axis=AxisConfig(label=y_label, type="value"),
            series=series,
            annotations=annotations,
            legend=list(groups.keys()),
            metadata=metadata,
        )


def _detect_axis_names(
    scores: list[dict[str, Any]], eigenvalues: list[dict[str, Any]]
) -> tuple[str, str]:
    """Detect axis names (e.g. PC1/PC2, PCoA1/PCoA2, RDA1/RDA2) from R output.

    Checks eigenvalue table first (axis field), then falls back to score row keys.
    """
    # Try eigenvalue table axis names
    if len(eigenvalues) >= 2:
        a1 = eigenvalues[0].get("axis", "")
        a2 = eigenvalues[1].get("axis", "")
        if a1 and a2:
            return a1, a2

    # Fall back to score row keys - find first axis-like key pair
    if scores:
        row = scores[0]
        skip_keys = {"sample_id", "group", "species", "variable"}
        axis_keys = [k for k in row.keys() if k not in skip_keys]
        if len(axis_keys) >= 2:
            return axis_keys[0], axis_keys[1]

    return "Axis1", "Axis2"
