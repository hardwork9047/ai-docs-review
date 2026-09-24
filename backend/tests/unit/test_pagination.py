"""Unit tests for app.domain.pagination — TDD スタイルのサンプル。

受け入れシナリオを1テスト1シナリオで平文に近い名前に翻訳する。
実開発開始時に pagination.py ごと削除してよい。
"""

import pytest

from app.domain.pagination import PageError, paginate

ITEMS = list(range(1, 24))  # 23 items


def test_first_page_returns_per_page_items() -> None:
    result = paginate(ITEMS, page=1, per_page=10)
    assert list(result.items) == list(range(1, 11))
    assert result.page == 1
    assert result.total_pages == 3


def test_last_page_may_be_partial() -> None:
    result = paginate(ITEMS, page=3, per_page=10)
    assert list(result.items) == [21, 22, 23]


def test_page_beyond_total_raises() -> None:
    with pytest.raises(PageError, match="out of range"):
        paginate(ITEMS, page=4, per_page=10)


def test_page_below_one_raises() -> None:
    with pytest.raises(PageError, match="page must be >= 1"):
        paginate(ITEMS, page=0, per_page=10)


def test_per_page_below_one_raises() -> None:
    with pytest.raises(PageError, match="per_page must be >= 1"):
        paginate(ITEMS, page=1, per_page=0)


def test_empty_source_page_one_is_allowed() -> None:
    result = paginate([], page=1, per_page=10)
    assert list(result.items) == []
    assert result.total_pages == 0


def test_source_is_not_mutated() -> None:
    source = [1, 2, 3]
    paginate(source, page=1, per_page=2)
    assert source == [1, 2, 3]
