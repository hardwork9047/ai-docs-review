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
    family = name.split("+", 1)[-1].split(",", 1)[0].split("-", 1)[0].strip()
    return family if family and family.lower() != "unknown" else None


def score_font_size(page: Page) -> CriterionScore:
    """100 minus 70 x (share of glyphs smaller than SMALL_FONT_PT). None without text."""
    sizes = page.char_sizes
    if not sizes:
        return CriterionScore(criterion="フォントサイズ", score=None)
    small = sum(1 for s in sizes if s < SMALL_FONT_PT) / len(sizes)
    note = f"最小{min(sizes):.0f}pt / {SMALL_FONT_PT:.0f}pt未満 {small:.0%}"
    return CriterionScore(criterion="フォントサイズ", score=round(100 - 70 * small), note=note)


def score_font(page: Page) -> CriterionScore:
    """Font families on the page: 1-2 → 100, 3 → 70, 4+ → 40. None when unknown."""
    families = sorted({f for f in map(font_family, page.fonts) if f})
    if not families:
        return CriterionScore(criterion="フォント", score=None)
    score = 100 if len(families) <= 2 else 70 if len(families) == 3 else 40
    return CriterionScore(criterion="フォント", score=score, note=", ".join(families))


def score_text_amount(page: Page) -> CriterionScore:
    """Glyph count bands: <=150 → 100, <=250 → 80, <=400 → 60, more → 40."""
    count = len(page.char_sizes)
    score = next((s for limit, s in TEXT_AMOUNT_BANDS if count <= limit), TEXT_AMOUNT_FLOOR)
    return CriterionScore(criterion="文字量", score=score, note=f"{count}字")


def measure(page: Page) -> list[CriterionScore]:
    """All deterministic criteria for `page`."""
    return [score_font_size(page), score_font(page), score_text_amount(page)]
