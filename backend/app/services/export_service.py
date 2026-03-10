from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.schemas.chart_contract import ChartContract
from app.services.matplotlib_theme_service import MatplotlibThemeService

__all__ = ["ExportService"]

logger = logging.getLogger(__name__)


class ExportService:
    @staticmethod
    def render_figure(
        contract: ChartContract,
        output_path: Path,
        *,
        fmt: str = "png",
    ) -> Path:
        MatplotlibThemeService.init()

        fig, ax = plt.subplots()

        if contract.chart_type == "bar_error_letters":
            ExportService._render_bar_error(ax, contract)
        elif contract.chart_type == "boxplot":
            ExportService._render_boxplot(ax, contract)
        elif contract.chart_type == "violin":
            ExportService._render_violin(ax, contract)
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
