"""HTTP routes.

This layer only translates HTTP <-> domain: parse inputs, call domain functions,
map domain errors to HTTP status codes. No business logic here.
"""

from fastapi import APIRouter, HTTPException

from app.domain.pagination import PageError, paginate

router = APIRouter()

# サンプルデータ — 実開発では infra 層のデータソースに置き換える
_SAMPLE_ITEMS = [f"item-{i}" for i in range(1, 24)]


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns {"status": "ok"} when the app is up."""
    return {"status": "ok"}


@router.get("/items")
def list_items(page: int = 1, per_page: int = 10) -> dict[str, object]:
    """Return one page of sample items.

    Query params `page` (1-indexed) and `per_page` are validated by the domain
    layer; out-of-range values yield HTTP 422.
    """
    try:
        result = paginate(_SAMPLE_ITEMS, page=page, per_page=per_page)
    except PageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"items": list(result.items), "page": result.page, "total_pages": result.total_pages}
