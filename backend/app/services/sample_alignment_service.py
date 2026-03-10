from __future__ import annotations

import logging

import pandas as pd

from app.core.errors import ValidationError

__all__ = ["SampleAlignmentService"]

logger = logging.getLogger(__name__)


class SampleAlignmentService:
    @staticmethod
    def validate_dual_matrix(
        response_df: pd.DataFrame,
        env_df: pd.DataFrame,
        sample_key: str,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if sample_key not in response_df.columns:
            raise ValidationError(f"Sample key '{sample_key}' not in response matrix")
        if sample_key not in env_df.columns:
            raise ValidationError(f"Sample key '{sample_key}' not in environment matrix")

        resp_ids = set(response_df[sample_key].astype(str))
        env_ids = set(env_df[sample_key].astype(str))
        common = resp_ids & env_ids

        if not common:
            raise ValidationError("No common sample IDs between matrices")

        missing_in_env = resp_ids - env_ids
        missing_in_resp = env_ids - resp_ids
        if missing_in_env:
            logger.warning(
                "Samples in response but not environment: %s", missing_in_env
            )
        if missing_in_resp:
            logger.warning(
                "Samples in environment but not response: %s", missing_in_resp
            )

        common_list = sorted(common)
        response_aligned = (
            response_df[response_df[sample_key].astype(str).isin(common_list)]
            .sort_values(sample_key)
            .reset_index(drop=True)
        )
        env_aligned = (
            env_df[env_df[sample_key].astype(str).isin(common_list)]
            .sort_values(sample_key)
            .reset_index(drop=True)
        )

        return response_aligned, env_aligned
