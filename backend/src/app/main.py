"""Application entry point.

Run locally with: `make dev-backend` (uvicorn app.main:app --reload).
On Render the Docker image sets `REVIEW_STATIC_DIR` so this app also serves the
built frontend from the same origin.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import get_settings, router


def create_app(static_dir: str | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Factory pattern so tests can construct a fresh app instance. When `static_dir`
    is given, the built frontend in it is served at "/" (API routes take precedence).
    """
    application = FastAPI(title="部長レビュー")
    application.include_router(router)
    if static_dir:
        application.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return application


app = create_app(get_settings().static_dir)
