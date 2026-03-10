from fastapi import APIRouter

from app.api.routes import (
    analysis_dispatch,
    analysis_m2,
    analysis_m3,
    analysis_m4,
    analysis_m5,
    analysis_runs,
    auth,
    datasets,
    exports,
    health,
    preprocess,
)

__all__ = ["api_router"]

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(datasets.router)
api_router.include_router(preprocess.router)
api_router.include_router(analysis_runs.router)
api_router.include_router(analysis_dispatch.router)
api_router.include_router(analysis_m2.router)
api_router.include_router(analysis_m3.router)
api_router.include_router(analysis_m4.router)
api_router.include_router(analysis_m5.router)
api_router.include_router(exports.router)
