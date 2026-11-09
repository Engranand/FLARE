from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import Settings
from app.schemas.system import ApiInfo
from app.db.engine import create_db_engine
from app.db.session import create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine = create_db_engine(settings) if settings.database_url is not None else None
        application.state.db_engine = engine
        application.state.session_factory = create_session_factory(engine) if engine else None
        try:
            yield
        finally:
            if engine is not None:
                engine.dispose()
            application.state.session_factory = None
            application.state.db_engine = None

    application = FastAPI(title=settings.app_name, version=settings.app_version,
                          lifespan=lifespan)
    application.state.settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
        allow_credentials=False,
    )
    application.include_router(router, prefix=settings.api_v1_prefix)

    @application.get("/", response_model=ApiInfo, tags=["system"])
    def root() -> ApiInfo:
        return ApiInfo(
            application_name=settings.app_name,
            version=settings.app_version,
            docs_url="/docs",
        )

    return application


app = create_app()
