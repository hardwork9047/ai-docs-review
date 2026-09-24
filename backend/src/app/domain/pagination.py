"""Pure pagination logic.

このモジュールと tests/unit/test_pagination.py は、このテンプレートの TDD スタイルを示す
サンプルです。実開発を始めるときに削除して構いません。
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class PageError(ValueError):
    """Raised when page or per_page is out of range."""


@dataclass(frozen=True)
class Page(Generic[T]):
    """One page of results.

    Attributes:
        items: the items on this page (may be empty only when the source is empty).
        page: the 1-indexed page number that was requested.
        total_pages: total number of pages for the source (0 for an empty source).
    """

    items: Sequence[T]
    page: int
    total_pages: int


def paginate(items: Sequence[T], *, page: int, per_page: int) -> Page[T]:
    """Return the requested 1-indexed page of `items`.

    Args:
        items: the full sequence to paginate. Not mutated.
        page: 1-indexed page number.
        per_page: number of items per page; must be >= 1.

    Returns:
        A Page with the slice for `page`. For an empty `items`, page 1 returns an
        empty Page with total_pages == 0.

    Raises:
        PageError: if per_page < 1, page < 1, or page exceeds total_pages
            (except page 1 of an empty sequence, which is allowed).
    """
    if per_page < 1:
        raise PageError(f"per_page must be >= 1, got {per_page}")
    if page < 1:
        raise PageError(f"page must be >= 1, got {page}")

    total_pages = -(-len(items) // per_page)  # ceil division
    if page > total_pages and not (page == 1 and total_pages == 0):
        raise PageError(f"page {page} is out of range (total_pages={total_pages})")

    start = (page - 1) * per_page
    return Page(items=items[start : start + per_page], page=page, total_pages=total_pages)
