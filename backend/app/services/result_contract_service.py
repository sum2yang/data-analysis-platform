from __future__ import annotations

import logging
from typing import Any

__all__ = ["ResultContractService"]

logger = logging.getLogger(__name__)


class ResultContractService:
    @staticmethod
    def validate_envelope(raw: dict[str, Any]) -> dict[str, Any]:
        required = {"analysis_type", "engine"}
        missing = required - set(raw.keys())
        if missing:
            logger.warning("Result envelope missing keys: %s", missing)

        return {
            "analysis_type": raw.get("analysis_type", "unknown"),
            "engine": raw.get("engine", "R"),
            "summary": raw.get("summary"),
            "tables": raw.get("tables", {}),
            "assumptions": raw.get("assumptions"),
            "warnings": raw.get("warnings", []),
            "chart_contracts": raw.get("chart_contracts", []),
        }
