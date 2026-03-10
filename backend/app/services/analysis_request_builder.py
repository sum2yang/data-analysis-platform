from __future__ import annotations

import csv
import json
import logging
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import get_settings

__all__ = ["AnalysisRequestBuilder"]

logger = logging.getLogger(__name__)

MAX_INLINE_ROWS = 500


class AnalysisRequestBuilder:
    @staticmethod
    def build_bundle(
        *,
        analysis_type: str,
        params: dict[str, Any],
        revision_paths: dict[str, str],
    ) -> dict[str, Any]:
        bundle: dict[str, Any] = {
            "analysis_type": analysis_type,
            "params": params,
            "data": {},
        }

        for role, csv_path in revision_paths.items():
            df = pd.read_csv(csv_path)
            if len(df) <= MAX_INLINE_ROWS:
                bundle["data"][role] = df.to_dict(orient="list")
            else:
                manifest_id = str(uuid.uuid4())
                settings = get_settings()
                manifest_dir = settings.ARTIFACT_ROOT / "manifests"
                manifest_dir.mkdir(parents=True, exist_ok=True)
                manifest_path = manifest_dir / f"{manifest_id}.csv"
                df.to_csv(manifest_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
                bundle["data"][role] = {
                    "manifest": True,
                    "path": str(manifest_path),
                    "rows": len(df),
                }

        return bundle
