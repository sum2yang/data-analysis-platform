from fastapi import APIRouter
from pydantic import BaseModel

__all__ = ["router"]

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/live", response_model=HealthResponse)
async def liveness():
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/ready", response_model=HealthResponse)
async def readiness():
    return HealthResponse(status="ok", version="0.1.0")
