from fastapi import APIRouter, Request, Response, status

from app.api.analysis import router as analysis_router
from app.api.intelligence import router as intelligence_router
from app.db.check import check_database_health
from app.schemas.system import DatabaseHealth, HealthResponse, SystemInfo

from app.api.workstation import router as workstation_router

router = APIRouter()
router.include_router(workstation_router)
router.include_router(analysis_router)
router.include_router(intelligence_router)


@router.get("/health", response_model=HealthResponse, response_model_exclude_none=True, tags=["system"])
def health(request: Request, response: Response, db: bool = False) -> HealthResponse:
    settings = request.app.state.settings
    db_health = None
    app_status = "ok"

    if db:
        engine = getattr(request.app.state, "db_engine", None)
        report = check_database_health(settings, engine=engine)
        db_health = DatabaseHealth(**report)
        if report.get("status") == "healthy":
            app_status = "ok"
        else:
            app_status = report.get("status", "unhealthy")
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=app_status,
        application_name=settings.app_name,
        version=settings.app_version,
        database=db_health,
    )


@router.get("/system/info", response_model=SystemInfo, tags=["system"])
def system_info(request: Request) -> SystemInfo:
    settings = request.app.state.settings
    return SystemInfo(
        application_name=settings.app_name,
        api_version=settings.app_version,
        environment=settings.environment,
    )
