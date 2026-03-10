from __future__ import annotations

import logging
from typing import Any

from app.workers.celery_worker import celery_app
from app.db.session import SessionLocal
from app.repositories.analysis_runs import AnalysisRunRepository
from app.services.analysis_request_builder import AnalysisRequestBuilder
from app.services.r_plumber_client import RPlumberClient
from app.services.result_contract_service import ResultContractService

__all__ = ["run_analysis_task"]

logger = logging.getLogger(__name__)

ANALYSIS_TYPE_TO_ENDPOINT: dict[str, str] = {
    "descriptive": "/descriptive",
    "assumptions": "/assumptions",
    "t_test": "/t-test",
    "anova_one_way": "/anova/one-way",
    "anova_multi_way": "/anova/multi-way",
    "anova_welch": "/anova/welch",
    "kruskal_wallis": "/nonparametric/kruskal-wallis",
    "mann_whitney": "/nonparametric/mann-whitney",
    "correlation": "/correlation",
    "regression_linear": "/regression/linear",
    "regression_glm": "/regression/glm",
    "pca": "/ordination/pca",
    "pcoa": "/ordination/pcoa",
    "nmds": "/ordination/nmds",
    "rda": "/ordination/rda",
    "cca": "/ordination/cca",
}


@celery_app.task(name="run_analysis", bind=True, max_retries=0)
def run_analysis_task(
    self,
    *,
    run_id: str,
    analysis_type: str,
    params: dict[str, Any],
    revision_paths: dict[str, str],
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        repo = AnalysisRunRepository(db)
        repo.update_status(run_id, "running")

        endpoint = ANALYSIS_TYPE_TO_ENDPOINT.get(analysis_type)
        if not endpoint:
            repo.update_status(run_id, "failed", error_message=f"Unknown analysis type: {analysis_type}")
            return {"error": f"Unknown analysis type: {analysis_type}"}

        bundle = AnalysisRequestBuilder.build_bundle(
            analysis_type=analysis_type,
            params=params,
            revision_paths=revision_paths,
        )

        client = RPlumberClient()
        raw_result = client.call(endpoint, bundle)

        result = ResultContractService.validate_envelope(raw_result)

        repo.update_status(run_id, "succeeded", result=result)
        return result

    except Exception as e:
        logger.exception("Analysis task failed: run_id=%s", run_id)
        try:
            repo.update_status(run_id, "failed", error_message=str(e))
        except Exception:
            logger.exception("Failed to update run status")
        return {"error": str(e)}

    finally:
        db.close()
