from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .types import HealthCheckResponse
from .manager import manager
from mcp_bridge.openapi_tags import Tag

router = APIRouter(tags=[Tag.health])


@router.get("/health", response_model=HealthCheckResponse)
async def health():
    """Health check endpoint"""
    healthy = manager.is_healthy()

    if not healthy:
        # Create HealthCheckResponse instance
        response = HealthCheckResponse(
            status="error",
            unhealthy_events=manager.get_unhealthy_events(),
        )
        # Return JSONResponse with custom status code and serialized content
        return JSONResponse(content=response.model_dump(), status_code=500)

    # Create and return HealthCheckResponse for healthy state
    response = HealthCheckResponse(
        status="ok",
        unhealthy_events=[],
    )
    return response
