"""HTTP routes.

This layer only translates HTTP <-> domain: parse inputs, call domain functions,
map domain errors to HTTP status codes. No business logic here.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns {"status": "ok"} when the app is up."""
    return {"status": "ok"}
