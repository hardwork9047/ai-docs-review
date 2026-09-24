"""Application entry point.

Run locally with: `make dev-backend` (uvicorn app.main:app --reload).
"""

from fastapi import FastAPI

from app.api.routes import router


def create_app(static_dir: str | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Factory pattern so tests can construct a fresh app instance. When `static_dir`
    is given, the built frontend in it is served at "/" (API routes take precedence).
    """
    application = FastAPI(title="app")
    application.include_router(router)
    return application


app = create_app()
