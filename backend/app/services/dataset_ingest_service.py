from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import pandas as pd

__all__ = ["DatasetIngestService"]

logger = logging.getLogger(__name__)

ENCODING_CANDIDATES = ["utf-8", "gbk", "gb2312", "latin-1"]


class DatasetIngestService:
    @staticmethod
    def parse_file(file_path: Path, file_type: str) -> pd.DataFrame:
        if file_type in ("xlsx", "xls"):
            return pd.read_excel(file_path, sheet_name=0)
        return DatasetIngestService._read_csv_with_encoding(file_path)

    @staticmethod
    def _read_csv_with_encoding(file_path: Path) -> pd.DataFrame:
        for enc in ENCODING_CANDIDATES:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return pd.read_csv(file_path, encoding="utf-8", errors="replace")

    @staticmethod
    def materialize_canonical_csv(df: pd.DataFrame, target_path: Path) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target_path, index=False, encoding="utf-8", quoting=csv.QUOTE_NONNUMERIC)

    @staticmethod
    def infer_columns(df: pd.DataFrame) -> list[dict[str, Any]]:
        columns = []
        for i, col in enumerate(df.columns):
            dtype = DatasetIngestService._infer_dtype(df[col])
            columns.append({
                "name": str(col),
                "dtype": dtype,
                "position": i,
                "null_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique()),
            })
        return columns

    @staticmethod
    def _infer_dtype(series: pd.Series) -> str:
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        nunique = series.nunique()
        total = len(series)
        if total > 0 and nunique / total < 0.5:
            return "categorical"
        return "text"
