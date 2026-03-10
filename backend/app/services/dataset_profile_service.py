from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

__all__ = ["DatasetProfileService"]

logger = logging.getLogger(__name__)

PREVIEW_ROWS = 50


class DatasetProfileService:
    @staticmethod
    def build_preview(csv_path: Path, *, max_rows: int = PREVIEW_ROWS) -> dict[str, Any]:
        df = pd.read_csv(csv_path, nrows=max_rows)
        return {
            "columns": list(df.columns),
            "rows": df.fillna("").values.tolist(),
            "total_rows_shown": len(df),
        }

    @staticmethod
    def build_profile(csv_path: Path) -> dict[str, Any]:
        df = pd.read_csv(csv_path)
        profile: dict[str, Any] = {
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": {},
        }
        for col in df.columns:
            col_info: dict[str, Any] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique()),
            }
            if pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                col_info.update({
                    "mean": round(float(desc.get("mean", 0)), 4),
                    "std": round(float(desc.get("std", 0)), 4),
                    "min": round(float(desc.get("min", 0)), 4),
                    "max": round(float(desc.get("max", 0)), 4),
                    "median": round(float(df[col].median()), 4),
                })
            profile["columns"][str(col)] = col_info
        return profile
