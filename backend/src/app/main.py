"""Application entry point.

Run locally with: `make dev-backend` (uvicorn app.main:app --reload).
"""

from fastapi import FastAPI

from app.api.routes import router


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Factory pattern so tests can construct a fresh app instance.
    """
    application = FastAPI(title="app")
    application.include_router(router)
    return application


app = create_app()
