"""Application entry point.

Run locally with: `make dev-backend` (uvicorn app.main:app --reload).
On Render the Docker image sets `REVIEW_STATIC_DIR` so this app also serves the
built frontend from the same origin.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.limits import UploadLimitMiddleware
from app.api.routes import get_settings, router

# multipart の境界・ヘッダ分の余裕。ファイル本体の厳密な上限はルート側で判定する
MULTIPART_OVERHEAD_BYTES = 64 * 1024


def create_app(static_dir: str | None = None, max_upload_mb: int | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Factory pattern so tests can construct a fresh app instance. When `static_dir`
    is given, the built frontend in it is served at "/" (API routes take precedence).
    Request bodies to /api/review larger than `max_upload_mb` (default: settings) plus a
    small multipart overhead margin are cut off with 413 before they are parsed; the
    exact file-size limit is then enforced by the route.
    """
    limit_mb = max_upload_mb if max_upload_mb is not None else get_settings().max_upload_mb
    application = FastAPI(title="部長レビュー")
    application.add_middleware(
        UploadLimitMiddleware,
        max_bytes=limit_mb * 1024 * 1024 + MULTIPART_OVERHEAD_BYTES,
        paths=("/api/review",),
    )
    application.include_router(router)
    if static_dir:
        application.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return application


app = create_app(get_settings().static_dir)
