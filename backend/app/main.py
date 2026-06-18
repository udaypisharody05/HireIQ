from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.health import router as health_router
from app.api.leetcode import router as leetcode_router
from app.api.users import router as users_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analytics_router)
    app.include_router(health_router)
    app.include_router(leetcode_router)
    app.include_router(users_router)

    return app


app = create_app()
