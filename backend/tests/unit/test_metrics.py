"""Unit tests for app.domain.metrics — フォントサイズ・フォント・文字量の決定的採点。"""

import pytest

from app.domain.metrics import (
    SMALL_FONT_PT,
    font_family,
    measure,
    score_font,
    score_font_size,
    score_text_amount,
)
from app.domain.pages import Page


def _page(sizes: tuple[float, ...] = (), fonts: tuple[str, ...] = ()) -> Page:
    return Page(no=1, title="t", body="b", char_sizes=sizes, fonts=fonts)


@pytest.mark.parametrize(
    ("raw", "family"),
    [
        ("BAAAAA+HiraginoSans-W4", "HiraginoSans"),
        ("Carlito-Bold", "Carlito"),
        ("Arial,Bold", "Arial"),
        ("Meiryo UI", "Meiryo UI"),
        ("メイリオ", "メイリオ"),
        ("unknown", None),
        ("", None),
    ],
)
def test_font_family_normalisation(raw: str, family: str | None) -> None:
    assert font_family(raw) == family


def test_all_large_text_scores_full_marks() -> None:
    result = score_font_size(_page((36.0, 18.0, 18.0)))
    assert result.criterion == "フォントサイズ"
    assert result.score == 100
    assert result.note == "最小18pt / 14pt未満 0%"


def test_small_text_share_lowers_the_score() -> None:
    sizes = (18.0,) * 3 + (12.0,)  # 25% が小さい
    result = score_font_size(_page(sizes))
    assert result.score == 82  # 100 - 70 * 0.25 = 82.5 → 四捨五入(偶数丸め)で 82
    assert result.note == "最小12pt / 14pt未満 25%"


def test_boundary_size_is_not_small() -> None:
    assert score_font_size(_page((SMALL_FONT_PT,))).score == 100


def test_font_size_is_not_applicable_without_text() -> None:
    assert score_font_size(_page()).score is None


@pytest.mark.parametrize(("count", "expected"), [(1, 100), (2, 100), (3, 70), (4, 40), (6, 40)])
def test_font_score_by_family_count(count: int, expected: int) -> None:
    fonts = tuple(f"Font{i}" for i in range(count))
    assert score_font(_page(fonts=fonts)).score == expected


def test_font_variants_of_one_family_count_once() -> None:
    result = score_font(_page(fonts=("A+Meiryo-Bold", "B+Meiryo", "Arial", "Arial,Italic")))
    assert result.score == 100
    assert result.note == "Arial, Meiryo"


def test_font_is_not_applicable_when_names_are_unknown() -> None:
    assert score_font(_page(fonts=("unknown",))).score is None


@pytest.mark.parametrize(
    ("chars", "expected"), [(0, 100), (150, 100), (151, 80), (250, 80), (400, 60), (401, 40)]
)
def test_text_amount_bands(chars: int, expected: int) -> None:
    result = score_text_amount(_page((18.0,) * chars))
    assert result.score == expected
    assert result.note == f"{chars}字"


def test_measure_returns_the_three_deterministic_criteria() -> None:
    assert [s.criterion for s in measure(_page((18.0,)))] == ["フォントサイズ", "フォント", "文字量"]
