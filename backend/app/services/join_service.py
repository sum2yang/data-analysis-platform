from __future__ import annotations

import logging
from typing import Any

import pandas as pd

__all__ = ["JoinService"]

logger = logging.getLogger(__name__)


class JoinService:
    VALID_METHODS = {"inner", "left", "right", "outer"}

    @staticmethod
    def join_dataframes(
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        *,
        left_on: str,
        right_on: str,
        how: str = "inner",
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        if how not in JoinService.VALID_METHODS:
            raise ValueError(f"Invalid join method: {how}")

        left_count = len(left_df)
        right_count = len(right_df)

        result = pd.merge(
            left_df,
            right_df,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffixes=("", "_right"),
        )

        matched = len(result)
        report = {
            "left_rows": left_count,
            "right_rows": right_count,
            "result_rows": matched,
            "method": how,
            "left_key": left_on,
            "right_key": right_on,
            "match_rate_left": round(matched / left_count * 100, 1) if left_count else 0,
            "match_rate_right": round(matched / right_count * 100, 1) if right_count else 0,
        }
        return result, report
