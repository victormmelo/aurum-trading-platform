from fastapi import FastAPI

from app.api.routes.bot import router as bot_router
from app.api.routes.configs import router as configs_router
from app.api.routes.decisions import router as decisions_router
from app.api.routes.exports import router as exports_router
from app.api.routes.health import router as health_router
from app.api.routes.market import router as market_router
from app.api.routes.mcp import router as mcp_router
from app.api.routes.operations import router as operations_router
from app.api.routes.portfolio import router as portfolio_router
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
    app.include_router(configs_router)
    app.include_router(market_router)
    app.include_router(portfolio_router)
    app.include_router(operations_router)
    app.include_router(decisions_router)
    app.include_router(exports_router)
    app.include_router(mcp_router)
    return app


app = create_app()
