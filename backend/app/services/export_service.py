from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd

from app.schemas.chart_contract import ChartContract
from app.services.matplotlib_theme_service import MatplotlibThemeService

__all__ = ["ExportService"]

logger = logging.getLogger(__name__)

# Colour palette for multi-group scatter / biplot series
_PALETTE = [
    "#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B",
    "#EECA3B", "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC",
]


class ExportService:
    @staticmethod
    def render_figure(
        contract: ChartContract,
        output_path: Path,
        *,
        fmt: str = "png",
    ) -> Path:
        MatplotlibThemeService.init()

        # Heatmap needs the figure handle for colorbar
        if contract.chart_type == "heatmap":
            fig, ax = plt.subplots()
            ExportService._render_heatmap(fig, ax, contract)
        else:
            fig, ax = plt.subplots()
            _RENDERERS = {
                "bar_error_letters": ExportService._render_bar_error,
                "boxplot": ExportService._render_boxplot,
                "violin": ExportService._render_violin,
                "ordination_scatter": ExportService._render_ordination_scatter,
                "regression_plot": ExportService._render_regression_plot,
                "rda_biplot": ExportService._render_rda_biplot,
            }
            renderer = _RENDERERS.get(contract.chart_type)
            if renderer:
                renderer(ax, contract)
            else:
                ax.text(0.5, 0.5, f"Unsupported: {contract.chart_type}", ha="center")

        if contract.title:
            ax.set_title(contract.title)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, format=fmt)
        plt.close(fig)
        return output_path

    @staticmethod
    def _render_bar_error(ax, contract: ChartContract) -> None:
        if not contract.series:
            return

        series = contract.series[0]
        x_labels = contract.x_axis.data if contract.x_axis else list(range(len(series.data)))
        x = np.arange(len(series.data))

        bars = ax.bar(x, series.data, yerr=series.error_bars, capsize=5, color="#4C78A8")
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels)

        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)

        for ann in contract.annotations:
            if ann.type == "letter" and ann.position and ann.text:
                ax.text(
                    ann.position["x"],
                    ann.position["y"] * 1.05,
                    ann.text,
                    ha="center",
                    va="bottom",
                    fontsize=11,
                    fontweight="bold",
                )

    @staticmethod
    def _render_boxplot(ax, contract: ChartContract) -> None:
        if not contract.series:
            return
        data = contract.series[0].data
        labels = contract.x_axis.data if contract.x_axis else None
        ax.boxplot(data, labels=labels)
        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)

    @staticmethod
    def _render_violin(ax, contract: ChartContract) -> None:
        if not contract.series:
            return
        data = contract.series[0].data
        labels = contract.x_axis.data if contract.x_axis else None
        parts = ax.violinplot(data, showmeans=True, showmedians=True)
        if labels:
            ax.set_xticks(range(1, len(labels) + 1))
            ax.set_xticklabels(labels)
        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)

    @staticmethod
    def _render_heatmap(fig, ax, contract: ChartContract) -> None:
        """Render correlation heatmap.

        series[0].data = [[row, col, value], ...]
        x_axis.data / y_axis.data = variable names
        """
        if not contract.series:
            return

        variables = contract.x_axis.data if contract.x_axis else []
        n = len(variables)
        if n == 0:
            return

        # Rebuild NxN matrix from [row, col, value] triples
        matrix = np.zeros((n, n))
        for point in contract.series[0].data:
            r, c, v = int(point[0]), int(point[1]), float(point[2])
            if r < n and c < n:
                matrix[r][c] = v

        vmin, vmax = -1, 1
        value_range = contract.metadata.get("value_range")
        if value_range and len(value_range) == 2:
            vmin, vmax = value_range

        im = ax.imshow(matrix, cmap="RdBu_r", vmin=vmin, vmax=vmax, aspect="equal")
        fig.colorbar(im, ax=ax, shrink=0.8)

        # Axis labels
        ax.set_xticks(range(n))
        ax.set_xticklabels(variables, rotation=45, ha="right")
        ax.set_yticks(range(n))
        ax.set_yticklabels(variables)

        # Text annotations with correlation values
        for r in range(n):
            for c in range(n):
                val = matrix[r][c]
                color = "white" if abs(val) > 0.7 else "black"
                ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                        fontsize=8, color=color)

        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)

    @staticmethod
    def _render_ordination_scatter(ax, contract: ChartContract) -> None:
        """Render PCA/PCoA/NMDS ordination scatter plot.

        Each series = one group, series.data = [[x, y], ...]
        metadata.ellipses = optional 95% confidence ellipses per group.
        """
        if not contract.series:
            return

        for i, s in enumerate(contract.series):
            color = _PALETTE[i % len(_PALETTE)]
            xs = [p[0] for p in s.data]
            ys = [p[1] for p in s.data]
            ax.scatter(xs, ys, label=s.name, color=color, s=30, alpha=0.8)

        # Draw 95% confidence ellipses if available
        ellipses = contract.metadata.get("ellipses")
        if ellipses:
            for i, ell in enumerate(ellipses):
                color = _PALETTE[i % len(_PALETTE)]
                cx = ell.get("center_x", 0)
                cy = ell.get("center_y", 0)
                w = ell.get("width", 0)
                h = ell.get("height", 0)
                angle = ell.get("angle", 0)
                patch = Ellipse(
                    (cx, cy), width=w, height=h, angle=angle,
                    facecolor=color, alpha=0.15, edgecolor=color, linewidth=1,
                )
                ax.add_patch(patch)

        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)
        if contract.legend:
            ax.legend()

    @staticmethod
    def _render_regression_plot(ax, contract: ChartContract) -> None:
        """Render regression plot with observed data and fitted line.

        metadata.coefficients = [{term, estimate, ...}, ...]
        metadata.r_squared, metadata.equation = model summary
        The contract builds from coefficients; we render a coefficient-based
        scatter + regression line when observed data is available in series,
        or fall back to a coefficient bar chart.
        """
        meta = contract.metadata
        coefficients = meta.get("coefficients", [])

        # If series have scatter + line data, plot them directly
        has_scatter = any(s.type == "scatter" for s in contract.series)
        if has_scatter:
            for s in contract.series:
                if s.type == "scatter":
                    xs = [p[0] for p in s.data]
                    ys = [p[1] for p in s.data]
                    ax.scatter(xs, ys, color="#4C78A8", s=20, alpha=0.6, label="Observed")
                elif s.type == "line":
                    xs = [p[0] for p in s.data]
                    ys = [p[1] for p in s.data]
                    ax.plot(xs, ys, color="#E45756", linewidth=2, label="Fitted")
        elif coefficients:
            # Fall back: bar chart of coefficient estimates
            terms = [c.get("term", "") for c in coefficients]
            estimates = [c.get("estimate", 0) for c in coefficients]
            x = np.arange(len(terms))
            ax.bar(x, estimates, color="#4C78A8")
            ax.set_xticks(x)
            ax.set_xticklabels(terms, rotation=45, ha="right")
            ax.set_ylabel("Estimate")

        # Annotate with R-squared and equation
        r_sq = meta.get("r_squared")
        equation = meta.get("equation", "")
        text_parts = []
        if r_sq is not None:
            text_parts.append(f"R² = {r_sq:.4f}")
        if equation:
            text_parts.append(equation)
        if text_parts:
            ax.text(
                0.05, 0.95, "\n".join(text_parts),
                transform=ax.transAxes, va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.5),
            )

        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)
        if has_scatter:
            ax.legend()

    @staticmethod
    def _render_rda_biplot(ax, contract: ChartContract) -> None:
        """Render RDA/CCA biplot with site scores and variable arrows.

        Each series = one group of site scores, series.data = [[x, y], ...]
        annotations with type='arrow': position.from (origin) -> position.to (endpoint)
        """
        if not contract.series:
            return

        # Plot site scores grouped by series
        for i, s in enumerate(contract.series):
            color = _PALETTE[i % len(_PALETTE)]
            xs = [p[0] for p in s.data]
            ys = [p[1] for p in s.data]
            ax.scatter(xs, ys, label=s.name, color=color, s=30, alpha=0.8)

        # Draw origin crosshairs
        ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")
        ax.axvline(0, color="grey", linewidth=0.5, linestyle="--")

        # Draw variable arrows from annotations
        for ann in contract.annotations:
            if ann.type != "arrow" or not ann.position:
                continue
            to_pos = ann.position.get("to", {})
            tx = to_pos.get("x", 0)
            ty = to_pos.get("y", 0)
            ax.annotate(
                "",
                xy=(tx, ty),
                xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="red", linewidth=1.2),
            )
            # Label at arrow tip
            if ann.text:
                ax.text(
                    tx * 1.08, ty * 1.08, ann.text,
                    fontsize=8, color="red", ha="center", va="center",
                )

        # Draw 95% confidence ellipses if available
        ellipses = contract.metadata.get("ellipses")
        if ellipses:
            for i, ell in enumerate(ellipses):
                color = _PALETTE[i % len(_PALETTE)]
                cx = ell.get("center_x", 0)
                cy = ell.get("center_y", 0)
                w = ell.get("width", 0)
                h = ell.get("height", 0)
                angle = ell.get("angle", 0)
                patch = Ellipse(
                    (cx, cy), width=w, height=h, angle=angle,
                    facecolor=color, alpha=0.15, edgecolor=color, linewidth=1,
                )
                ax.add_patch(patch)

        if contract.x_axis:
            ax.set_xlabel(contract.x_axis.label)
        if contract.y_axis:
            ax.set_ylabel(contract.y_axis.label)
        if contract.legend:
            ax.legend()

    @staticmethod
    def export_table(
        data: dict[str, Any],
        output_path: Path,
        *,
        fmt: str = "xlsx",
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "csv":
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame()
            df.to_csv(output_path, index=False)
        else:  # xlsx
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                if isinstance(data, dict):
                    for sheet_name, table_data in data.items():
                        if isinstance(table_data, list):
                            df = pd.DataFrame(table_data)
                        elif isinstance(table_data, dict):
                            df = pd.DataFrame(table_data)
                        else:
                            continue
                        safe_name = str(sheet_name)[:31]
                        df.to_excel(writer, sheet_name=safe_name, index=False)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name="Results", index=False)

        return output_path
