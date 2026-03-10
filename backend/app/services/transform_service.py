from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

__all__ = ["TransformService"]

logger = logging.getLogger(__name__)


class TransformService:
    VALID_OPS = {
        "fill_missing",
        "drop_missing",
        "scale",
        "log_transform",
        "cast_type",
        "drop_columns",
        "rename_column",
        "wide_to_long",
        "long_to_wide",
    }

    @staticmethod
    def apply(df: pd.DataFrame, op_type: str, params: dict[str, Any]) -> pd.DataFrame:
        if op_type not in TransformService.VALID_OPS:
            raise ValueError(f"Unknown transform: {op_type}")
        handler = getattr(TransformService, f"_op_{op_type}")
        return handler(df.copy(), params)

    @staticmethod
    def _op_fill_missing(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        columns = params.get("columns", df.columns.tolist())
        method = params.get("method", "mean")  # mean, median, zero, ffill, value
        for col in columns:
            if col not in df.columns:
                continue
            if method == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            elif method == "median" and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            elif method == "zero":
                df[col] = df[col].fillna(0)
            elif method == "ffill":
                df[col] = df[col].ffill()
            elif method == "value":
                df[col] = df[col].fillna(params.get("fill_value", ""))
        return df

    @staticmethod
    def _op_drop_missing(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        columns = params.get("columns")
        how = params.get("how", "any")  # any, all
        if columns:
            return df.dropna(subset=columns, how=how).reset_index(drop=True)
        return df.dropna(how=how).reset_index(drop=True)

    @staticmethod
    def _op_scale(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        columns = params.get("columns", [])
        method = params.get("method", "zscore")  # zscore, minmax
        for col in columns:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            if method == "zscore":
                mean, std = df[col].mean(), df[col].std()
                if std > 0:
                    df[col] = (df[col] - mean) / std
            elif method == "minmax":
                mn, mx = df[col].min(), df[col].max()
                if mx > mn:
                    df[col] = (df[col] - mn) / (mx - mn)
        return df

    @staticmethod
    def _op_log_transform(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        columns = params.get("columns", [])
        base = params.get("base", "natural")  # natural, log2, log10
        offset = params.get("offset", 0)
        for col in columns:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            vals = df[col] + offset
            if base == "log2":
                df[col] = np.log2(vals)
            elif base == "log10":
                df[col] = np.log10(vals)
            else:
                df[col] = np.log(vals)
        return df

    @staticmethod
    def _op_cast_type(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        column = params["column"]
        target_type = params["target_type"]  # numeric, categorical, text
        if column not in df.columns:
            return df
        if target_type == "numeric":
            df[column] = pd.to_numeric(df[column], errors="coerce")
        elif target_type == "categorical":
            df[column] = df[column].astype(str)
        elif target_type == "text":
            df[column] = df[column].astype(str)
        return df

    @staticmethod
    def _op_drop_columns(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        columns = params.get("columns", [])
        return df.drop(columns=[c for c in columns if c in df.columns])

    @staticmethod
    def _op_rename_column(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        old_name = params["old_name"]
        new_name = params["new_name"]
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
        return df

    @staticmethod
    def _op_wide_to_long(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        id_vars = params.get("id_vars", [])
        value_vars = params.get("value_vars")
        var_name = params.get("var_name", "variable")
        value_name = params.get("value_name", "value")
        return pd.melt(
            df,
            id_vars=id_vars,
            value_vars=value_vars,
            var_name=var_name,
            value_name=value_name,
        )

    @staticmethod
    def _op_long_to_wide(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        index = params["index"]
        columns = params["columns"]
        values = params["values"]
        return df.pivot_table(
            index=index, columns=columns, values=values, aggfunc="first"
        ).reset_index()
