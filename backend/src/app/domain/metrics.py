"""Deterministic criteria measured from the page: フォントサイズ / フォント / 文字量.

小型の LLM に計測をさせず、PDF から数えた値で採点する(毎回同じ・説明可能)。
"""

from app.domain.pages import Page
from app.domain.review import CriterionScore

SMALL_FONT_PT = 14.0  # これ未満の文字は「小さい」
TEXT_AMOUNT_BANDS: tuple[tuple[int, int], ...] = ((150, 100), (250, 80), (400, 60))
TEXT_AMOUNT_FLOOR = 40


def font_family(name: str) -> str | None:
    """Normalise a font name to its family.

    Drops the PDF subset prefix ("ABCDEF+") and style suffixes after "-" or ",".
    Returns None for unnamed fonts ("", "unknown").
    """
    raise NotImplementedError


def score_font_size(page: Page) -> CriterionScore:
    """100 minus 70 x (share of glyphs smaller than SMALL_FONT_PT). None without text."""
    raise NotImplementedError


def score_font(page: Page) -> CriterionScore:
    """Font families on the page: 1-2 → 100, 3 → 70, 4+ → 40. None when unknown."""
    raise NotImplementedError


def score_text_amount(page: Page) -> CriterionScore:
    """Glyph count bands: <=150 → 100, <=250 → 80, <=400 → 60, more → 40."""
    raise NotImplementedError


def measure(page: Page) -> list[CriterionScore]:
    """All deterministic criteria for `page`."""
    return [score_font_size(page), score_font(page), score_text_amount(page)]
