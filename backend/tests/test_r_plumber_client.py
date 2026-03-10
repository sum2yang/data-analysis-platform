from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.errors import ExternalServiceError
from app.services.r_plumber_client import RPlumberClient


def test_call_returns_parsed_json_on_success():
    client = RPlumberClient(base_url="http://r-plumber", timeout=1.0)
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"result": 123}

    with patch("app.services.r_plumber_client.httpx.post", return_value=mock_resp) as mock_post:
        result = client.call("/run", {"x": 1})

    assert result == {"result": 123}
    mock_post.assert_called_once_with(
        "http://r-plumber/run",
        json={"x": 1},
        timeout=1.0,
    )
    mock_resp.raise_for_status.assert_called_once()


def test_call_raises_external_service_error_on_timeout():
    client = RPlumberClient(base_url="http://r-plumber", timeout=1.0)

    with patch(
        "app.services.r_plumber_client.httpx.post",
        side_effect=httpx.TimeoutException("timeout"),
    ):
        with pytest.raises(ExternalServiceError) as exc:
            client.call("/run", {"x": 1})

    assert exc.value.error == "external_service_error"
    assert "timeout" in str(exc.value).lower()


def test_call_raises_external_service_error_on_http_error():
    client = RPlumberClient(base_url="http://r-plumber", timeout=1.0)
    request = httpx.Request("POST", "http://r-plumber/run")
    response = httpx.Response(500, request=request, text="boom")
    err = httpx.HTTPStatusError("server error", request=request, response=response)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = err

    with patch("app.services.r_plumber_client.httpx.post", return_value=mock_resp):
        with pytest.raises(ExternalServiceError) as exc:
            client.call("/run", {"x": 1})

    assert exc.value.error == "external_service_error"
    assert "500" in str(exc.value)


def test_call_raises_external_service_error_on_connection_error():
    client = RPlumberClient(base_url="http://r-plumber", timeout=1.0)

    with patch(
        "app.services.r_plumber_client.httpx.post",
        side_effect=httpx.ConnectError("connect"),
    ):
        with pytest.raises(ExternalServiceError) as exc:
            client.call("/run", {"x": 1})

    assert exc.value.error == "external_service_error"
    assert "unavailable" in str(exc.value).lower()


def test_health_returns_true_on_200():
    client = RPlumberClient(base_url="http://r-plumber", timeout=1.0)
    mock_resp = MagicMock(status_code=200)

    with patch("app.services.r_plumber_client.httpx.get", return_value=mock_resp):
        ok = client.health()

    assert ok is True


def test_health_returns_false_on_exception():
    client = RPlumberClient(base_url="http://r-plumber", timeout=1.0)

    with patch("app.services.r_plumber_client.httpx.get", side_effect=Exception("boom")):
        ok = client.health()

    assert ok is False
