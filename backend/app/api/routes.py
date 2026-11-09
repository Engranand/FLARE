from fastapi import APIRouter, Request

from app.schemas.system import HealthResponse, SystemInfo

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(application_name=settings.app_name, version=settings.app_version)


@router.get("/system/info", response_model=SystemInfo, tags=["system"])
def system_info(request: Request) -> SystemInfo:
    settings = request.app.state.settings
    return SystemInfo(
        application_name=settings.app_name,
        api_version=settings.app_version,
        environment=settings.environment,
    )
