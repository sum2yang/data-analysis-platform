from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import ExternalServiceError

__all__ = ["RPlumberClient"]

logger = logging.getLogger(__name__)


class RPlumberClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._base_url = (base_url or settings.R_PLUMBER_BASE_URL).rstrip("/")
        self._timeout = timeout or settings.R_PLUMBER_TIMEOUT

    def call(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{endpoint}"
        try:
            resp = httpx.post(url, json=payload, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            raise ExternalServiceError(f"R Plumber timeout: {endpoint}")
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:500] if e.response else str(e)
            raise ExternalServiceError(f"R Plumber error ({e.response.status_code}): {detail}")
        except httpx.ConnectError:
            raise ExternalServiceError("R Plumber service unavailable")

    def health(self) -> bool:
        try:
            resp = httpx.get(f"{self._base_url}/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
