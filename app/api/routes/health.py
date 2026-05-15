from fastapi import APIRouter
from app.models.paper import HealthResponse
from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    return HealthResponse(
        status='ok',
        version=settings.app_version,
        environment=settings.environment,
    )