"""End-to-end integration tests for the analysis pipeline.

Full flow: auth -> dataset upload -> analysis submit -> celery task -> result retrieval

Two modes:
  * Default (CI): Celery eager + mocked R Plumber responses
  * Live:         Celery eager + real R Plumber at localhost:8787
                  Run with ``pytest --live-r``
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Mock R Plumber response factories
# ---------------------------------------------------------------------------


def _base_envelope(analysis_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "analysis_type": analysis_type,
        "engine": "R",
        "summary": extra.get("summary", {}),
        "tables": extra.get("tables", {}),
        "assumptions": extra.get("assumptions"),
        "warnings": extra.get("warnings", []),
        "chart_contracts": extra.get("chart_contracts", []),
    }


_MOCK_RESPONSES: dict[str, Any] = {
    "/descriptive": lambda p: _base_envelope(
        "descriptive",
        summary={
            "response_column": p["params"].get("response_column", "value1"),
            "group_column": p["params"].get("group_column"),
            "n_groups": 3,
        },
        tables={
            "descriptive": [
                {
                    "group": g,
                    "n": 20,
                    "mean": m,
                    "sd": s,
                    "se": round(s / 20**0.5, 2),
                    "median": m - 0.5,
                    "min": m - 2 * s,
                    "max": m + 2 * s,
                    "q1": m - 0.67 * s,
                    "q3": m + 0.67 * s,
                    "iqr": round(1.34 * s, 2),
                    "cv": round(s / m * 100, 1),
                    "skewness": 0.1,
                    "kurtosis": -0.3,
                    "missing": 0,
                }
                for g, m, s in [("A", 10.5, 2.1), ("B", 15.3, 3.2), ("C", 12.1, 1.8)]
            ]
        },
    ),
    "/assumptions": lambda p: _base_envelope(
        "assumption_checks",
        summary={
            "response_column": p["params"].get("response_column", "value1"),
            "group_column": p["params"].get("group_column"),
            "n_rows_complete": 60,
            "n_rows_total": 60,
            "n_groups": 3,
        },
        tables={"outlier_summary": {"count": 0, "values": []}},
        assumptions={
            "shapiro_by_group": [
                {"group": "A", "statistic": 0.97, "p_value": 0.75},
                {"group": "B", "statistic": 0.96, "p_value": 0.60},
                {"group": "C", "statistic": 0.98, "p_value": 0.90},
            ],
            "levene": {"statistic": 1.5, "p_value": 0.23, "df1": 2, "df2": 57},
            "bartlett": {"test": "Bartlett", "statistic": 2.3, "df": 2, "p_value": 0.31},
        },
    ),
    "/t-test": lambda p: _base_envelope(
        "t_test",
        summary={
            "mode": p["params"].get("test_type", "independent"),
            "alternative": "two-sided",
            "conf_level": 0.95,
            "mu": 0,
            "var_equal": False,
            "n_x": 20,
            "n_y": 20,
            "method": "Welch Two Sample t-test",
        },
        tables={
            "t_test": {
                "statistic": -5.2,
                "df": 34.5,
                "p_value": 0.00001,
                "conf_int_low": -6.8,
                "conf_int_high": -2.8,
                "method": "Welch Two Sample t-test",
            },
            "estimates": [
                {"name": "mean of x", "value": 10.5},
                {"name": "mean of y", "value": 15.3},
            ],
        },
    ),
    "/anova/one-way": lambda p: _base_envelope(
        "anova_one_way",
        summary={
            "response_column": p["params"].get("response_column", "value1"),
            "group_column": p["params"].get("group_column", "group"),
            "n_groups": 3,
            "method": "One-way ANOVA",
            "posthoc_method": p["params"].get("posthoc_method", "tukey"),
        },
        tables={
            "anova": {
                "df_between": 2,
                "df_within": 57,
                "ss_between": 230.5,
                "ss_within": 315.2,
                "ms_between": 115.25,
                "ms_within": 5.53,
                "f_statistic": 20.84,
                "p_value": 0.000001,
            },
            "posthoc": [
                {"comparison": "B-A", "diff": 4.8, "lower": 2.9, "upper": 6.7, "p_adj": 0.00001},
                {"comparison": "C-A", "diff": 1.6, "lower": -0.3, "upper": 3.5, "p_adj": 0.12},
                {"comparison": "C-B", "diff": -3.2, "lower": -5.1, "upper": -1.3, "p_adj": 0.0003},
            ],
        },
    ),
    "/correlation": lambda p: _base_envelope(
        "correlation",
        summary={"method": p["params"].get("method", "pearson"), "n_variables": 2},
        tables={
            "pairwise_stats": [
                {"var1": "value1", "var2": "value2", "n": 60, "correlation": 0.45, "p_value": 0.001},
            ],
            "correlation_matrix": [
                {"row": "value1", "value1": 1.0, "value2": 0.45},
                {"row": "value2", "value1": 0.45, "value2": 1.0},
            ],
        },
    ),
    "/nonparametric/kruskal-wallis": lambda p: _base_envelope(
        "kruskal_wallis",
        summary={
            "response_column": p["params"].get("response_column", "value1"),
            "group_column": p["params"].get("group_column", "group"),
            "n_groups": 3,
        },
        tables={
            "kruskal_wallis": {
                "statistic": 30.5,
                "df": 2,
                "p_value": 0.0000002,
            },
            "posthoc": [
                {"comparison": "A-B", "p_value": 0.00001},
                {"comparison": "A-C", "p_value": 0.15},
                {"comparison": "B-C", "p_value": 0.001},
            ],
        },
    ),
    "/regression/linear": lambda p: _base_envelope(
        "regression_linear",
        summary={
            "response_column": p["params"].get("response_column", "value1"),
            "predictor_columns": p["params"].get("predictor_columns", ["value2"]),
            "n": 60,
            "r_squared": 0.21,
            "adj_r_squared": 0.20,
            "f_statistic": 15.3,
            "f_pvalue": 0.0002,
        },
        tables={
            "coefficients": [
                {"term": "(Intercept)", "estimate": 5.2, "std_error": 1.1, "t_value": 4.7, "p_value": 0.00002},
                {"term": "value2", "estimate": 1.1, "std_error": 0.28, "t_value": 3.9, "p_value": 0.0002},
            ],
        },
    ),
}


def _mock_r_call(endpoint: str, payload: dict) -> dict:
    factory = _MOCK_RESPONSES.get(endpoint)
    if factory is None:
        return _base_envelope("unknown", summary={"note": f"no mock for {endpoint}"})
    return factory(payload)


@pytest.fixture
def mock_r_plumber():
    """Patch ``httpx.post`` in the R Plumber client to return mock responses."""
    with patch("app.services.r_plumber_client.httpx.post") as mock_post:

        def _side_effect(url: str, json: dict | None = None, timeout: float | None = None):
            base_url = "http://localhost:8787"
            endpoint = url.replace(base_url, "") if url.startswith(base_url) else url
            result = _mock_r_call(endpoint, json or {})
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 200
            resp.raise_for_status.return_value = None
            resp.json.return_value = result
            return resp

        mock_post.side_effect = _side_effect
        yield mock_post


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _submit_and_get_result(
    client,
    url: str,
    payload: dict,
    headers: dict,
) -> tuple[dict, dict]:
    """Submit an analysis and retrieve the result.

    Returns (submit_response_body, result_body).
    """
    resp = await client.post(url, json=payload, headers=headers)
    assert resp.status_code == 200, f"Submit failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert "run_id" in body
    run_id = body["run_id"]

    # In eager mode the task finishes inline, so status should be 'succeeded'
    status_resp = await client.get(f"/api/v1/analysis-runs/{run_id}", headers=headers)
    assert status_resp.status_code == 200
    status = status_resp.json()
    assert status["status"] == "succeeded", f"Unexpected status: {status}"

    result_resp = await client.get(f"/api/v1/analysis-runs/{run_id}/result", headers=headers)
    assert result_resp.status_code == 200
    return body, result_resp.json()


# ===========================================================================
# Tests with mocked R Plumber (CI-safe)
# ===========================================================================


class TestE2EWithMockedR:
    """Full pipeline tests using mock R Plumber responses."""

    async def test_descriptive_stats(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        submit_body, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/descriptive",
            {
                "revision_id": rev_id,
                "response_columns": ["value1"],
                "group_column": "group",
            },
            headers,
        )
        assert submit_body["analysis_type"] == "descriptive"
        assert result["analysis_type"] == "descriptive"
        assert result["engine"] == "R"
        assert "descriptive" in result["tables"]
        assert len(result["tables"]["descriptive"]) == 3

    async def test_assumption_checks(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/assumptions",
            {
                "revision_id": rev_id,
                "response_columns": ["value1"],
                "group_column": "group",
            },
            headers,
        )
        assert result["analysis_type"] == "assumption_checks"
        assert result["assumptions"] is not None
        assert "shapiro_by_group" in result["assumptions"]
        assert "levene" in result["assumptions"]

    async def test_t_test(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/t-test",
            {
                "revision_id": rev_id,
                "response_column": "value1",
                "group_column": "group",
                "test_type": "independent",
            },
            headers,
        )
        assert result["analysis_type"] == "t_test"
        assert "t_test" in result["tables"]
        t = result["tables"]["t_test"]
        assert "statistic" in t
        assert "p_value" in t

    async def test_anova_one_way(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/anova/one-way",
            {
                "revision_id": rev_id,
                "response_column": "value1",
                "group_column": "group",
                "posthoc_method": "tukey",
            },
            headers,
        )
        assert result["analysis_type"] == "anova_one_way"
        assert "anova" in result["tables"]
        assert "posthoc" in result["tables"]
        assert result["tables"]["anova"]["p_value"] < 0.05

    async def test_correlation(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/correlation",
            {
                "revision_id": rev_id,
                "columns": ["value1", "value2"],
                "method": "pearson",
            },
            headers,
        )
        assert result["analysis_type"] == "correlation"
        assert "pairwise_stats" in result["tables"]
        assert "correlation_matrix" in result["tables"]

    async def test_kruskal_wallis(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/nonparametric/kruskal-wallis",
            {
                "revision_id": rev_id,
                "response_column": "value1",
                "group_column": "group",
            },
            headers,
        )
        assert result["analysis_type"] == "kruskal_wallis"
        assert "kruskal_wallis" in result["tables"]

    async def test_linear_regression(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/regression/linear",
            {
                "revision_id": rev_id,
                "response_column": "value1",
                "predictor_columns": ["value2"],
            },
            headers,
        )
        assert result["analysis_type"] == "regression_linear"
        assert "coefficients" in result["tables"]


# ---------------------------------------------------------------------------
# Unified dispatch endpoint tests
# ---------------------------------------------------------------------------


class TestE2EDispatch:
    """Tests for the ``POST /api/v1/analyses/run`` unified dispatch."""

    async def test_dispatch_descriptive(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        dataset_id = test_dataset["dataset_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/run",
            {
                "dataset_id": dataset_id,
                "analysis_type": "descriptive",
                "params": {
                    "response_column": "value1",
                    "group_column": "group",
                },
            },
            headers,
        )
        assert result["analysis_type"] == "descriptive"

    async def test_dispatch_anova_alias(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        """``anova`` alias should resolve to ``anova_one_way``."""
        headers = test_dataset["auth_headers"]
        dataset_id = test_dataset["dataset_id"]

        submit_body, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/run",
            {
                "dataset_id": dataset_id,
                "analysis_type": "anova",
                "params": {
                    "response_column": "value1",
                    "group_column": "group",
                },
            },
            headers,
        )
        assert submit_body["analysis_type"] == "anova_one_way"
        assert result["analysis_type"] == "anova_one_way"

    async def test_dispatch_nonparametric_routing(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        """``nonparametric`` with ``test=kruskal_wallis`` should route correctly."""
        headers = test_dataset["auth_headers"]
        dataset_id = test_dataset["dataset_id"]

        submit_body, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/run",
            {
                "dataset_id": dataset_id,
                "analysis_type": "nonparametric",
                "params": {
                    "test": "kruskal_wallis",
                    "response_column": "value1",
                    "group_column": "group",
                },
            },
            headers,
        )
        assert submit_body["analysis_type"] == "kruskal_wallis"

    async def test_dispatch_regression_routing(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        """``regression`` with ``method=lm`` should route to ``regression_linear``."""
        headers = test_dataset["auth_headers"]
        dataset_id = test_dataset["dataset_id"]

        submit_body, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/run",
            {
                "dataset_id": dataset_id,
                "analysis_type": "regression",
                "params": {
                    "method": "lm",
                    "response_column": "value1",
                    "predictor_columns": ["value2"],
                },
            },
            headers,
        )
        assert submit_body["analysis_type"] == "regression_linear"


# ---------------------------------------------------------------------------
# Error / edge-case tests
# ---------------------------------------------------------------------------


class TestE2EErrorCases:
    async def test_unsupported_analysis_type(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        dataset_id = test_dataset["dataset_id"]

        resp = await client.post(
            "/api/v1/analyses/run",
            json={
                "dataset_id": dataset_id,
                "analysis_type": "nonexistent_type",
                "params": {},
            },
            headers=headers,
        )
        assert resp.status_code in (400, 422)

    async def test_missing_auth_header(self, client, test_dataset, eager_celery):
        resp = await client.post(
            "/api/v1/analyses/descriptive",
            json={
                "revision_id": test_dataset["revision_id"],
                "response_columns": ["value1"],
            },
        )
        assert resp.status_code == 401

    async def test_nonexistent_dataset(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]

        resp = await client.post(
            "/api/v1/analyses/run",
            json={
                "dataset_id": "00000000-0000-0000-0000-000000000000",
                "analysis_type": "descriptive",
                "params": {"response_column": "value1"},
            },
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_nonexistent_revision(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]

        resp = await client.post(
            "/api/v1/analyses/descriptive",
            json={
                "revision_id": "00000000-0000-0000-0000-000000000000",
                "response_columns": ["value1"],
            },
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_result_not_available_for_pending_run(
        self, client, test_dataset, eager_celery
    ):
        """If the task somehow didn't finish, result should 404."""
        headers = test_dataset["auth_headers"]

        # Submit but make the R call fail so status = 'failed'
        with patch(
            "app.services.r_plumber_client.httpx.post",
            side_effect=httpx.ConnectError("R Plumber down"),
        ):
            resp = await client.post(
                "/api/v1/analyses/descriptive",
                json={
                    "revision_id": test_dataset["revision_id"],
                    "response_columns": ["value1"],
                    "group_column": "group",
                },
                headers=headers,
            )
        assert resp.status_code == 200
        run_id = resp.json()["run_id"]

        # Status should be 'failed'
        status_resp = await client.get(
            f"/api/v1/analysis-runs/{run_id}", headers=headers
        )
        assert status_resp.json()["status"] == "failed"

        # Result should 404
        result_resp = await client.get(
            f"/api/v1/analysis-runs/{run_id}/result", headers=headers
        )
        assert result_resp.status_code == 404


# ---------------------------------------------------------------------------
# Run listing / polling tests
# ---------------------------------------------------------------------------


class TestE2ERunManagement:
    async def test_list_runs_returns_submitted_analysis(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        resp = await client.post(
            "/api/v1/analyses/descriptive",
            json={
                "revision_id": rev_id,
                "response_columns": ["value1"],
                "group_column": "group",
            },
            headers=headers,
        )
        assert resp.status_code == 200

        list_resp = await client.get("/api/v1/analysis-runs", headers=headers)
        assert list_resp.status_code == 200
        runs = list_resp.json()
        assert len(runs) >= 1
        assert any(r["analysis_type"] == "descriptive" for r in runs)

    async def test_run_status_has_timestamps(
        self, client, test_dataset, eager_celery, mock_r_plumber
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        resp = await client.post(
            "/api/v1/analyses/t-test",
            json={
                "revision_id": rev_id,
                "response_column": "value1",
                "group_column": "group",
            },
            headers=headers,
        )
        run_id = resp.json()["run_id"]

        status_resp = await client.get(
            f"/api/v1/analysis-runs/{run_id}", headers=headers
        )
        status = status_resp.json()
        assert status["created_at"] is not None
        assert status["started_at"] is not None
        assert status["completed_at"] is not None


# ===========================================================================
# Live R Plumber tests (opt-in via --live-r)
# ===========================================================================


@pytest.mark.live_r
class TestE2ELiveR:
    """Tests that hit the real R Plumber service at localhost:8787.

    Run with: ``pytest --live-r -k TestE2ELiveR``
    """

    async def test_r_plumber_health(self):
        """Verify R Plumber is actually reachable."""
        from app.services.r_plumber_client import RPlumberClient

        client = RPlumberClient()
        assert client.health() is True, "R Plumber not reachable at localhost:8787"

    async def test_live_descriptive_stats(
        self, client, test_dataset, eager_celery
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/descriptive",
            {
                "revision_id": rev_id,
                "response_columns": ["value1"],
                "group_column": "group",
            },
            headers,
        )
        assert result["analysis_type"] == "descriptive"
        assert result["engine"] == "R"
        stats = result["tables"]["descriptive"]
        assert len(stats) == 3
        for row in stats:
            assert row["n"] == 20
            assert isinstance(row["mean"], (int, float))

    async def test_live_t_test(
        self, client, test_dataset, eager_celery
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/t-test",
            {
                "revision_id": rev_id,
                "response_column": "value1",
                "group_column": "group",
                "test_type": "independent",
            },
            headers,
        )
        assert result["analysis_type"] == "t_test"
        assert result["tables"]["t_test"]["p_value"] < 0.05

    async def test_live_anova_one_way(
        self, client, test_dataset, eager_celery
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/anova/one-way",
            {
                "revision_id": rev_id,
                "response_column": "value1",
                "group_column": "group",
                "posthoc_method": "tukey",
            },
            headers,
        )
        assert result["analysis_type"] == "anova_one_way"
        assert result["tables"]["anova"]["f_statistic"] > 0
        assert len(result["tables"]["posthoc"]) == 3

    async def test_live_assumptions(
        self, client, test_dataset, eager_celery
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/assumptions",
            {
                "revision_id": rev_id,
                "response_columns": ["value1"],
                "group_column": "group",
            },
            headers,
        )
        assert result["analysis_type"] == "assumption_checks"
        assert result["assumptions"] is not None

    async def test_live_correlation(
        self, client, test_dataset, eager_celery
    ):
        headers = test_dataset["auth_headers"]
        rev_id = test_dataset["revision_id"]

        _, result = await _submit_and_get_result(
            client,
            "/api/v1/analyses/correlation",
            {
                "revision_id": rev_id,
                "columns": ["value1", "value2"],
                "method": "pearson",
            },
            headers,
        )
        assert result["analysis_type"] == "correlation"
        pairwise = result["tables"]["pairwise_stats"]
        assert len(pairwise) >= 1
        assert -1 <= pairwise[0]["correlation"] <= 1
