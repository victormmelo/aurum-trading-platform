from fastapi import FastAPI

from app.api.routes.bot import router as bot_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.api_version,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )
    app.include_router(health_router)
    app.include_router(bot_router)
    return app


app = create_app()
