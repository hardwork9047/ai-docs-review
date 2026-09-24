"""Unit tests for app.domain.reviewer — 1ページ分のユーザープロンプト組み立て。"""

from app.domain.pages import Page
from app.domain.review import CriterionScore
from app.domain.reviewer import BOSS, build_page_prompt

MEASURED = [
    CriterionScore(criterion="フォントサイズ", score=58, note="最小12pt / 14pt未満 60%"),
    CriterionScore(criterion="フォント", score=None, note=""),
    CriterionScore(criterion="文字量", score=40, note="520字"),
]
PAGE = Page(no=3, title="効果", body="大幅改善", notes="口頭で補足", image_count=2)


def _prompt(page: Page = PAGE) -> str:
    return build_page_prompt(page, total=10, outline=["表紙", "現状", "効果"], measured=MEASURED)


def test_prompt_states_position_title_and_body() -> None:
    prompt = _prompt()
    assert "全10ページ中の3ページ目" in prompt
    assert "[タイトル] 効果" in prompt
    assert "[本文]\n大幅改善" in prompt


def test_prompt_lists_deck_outline_for_context() -> None:
    assert "1. 表紙\n2. 現状\n3. 効果" in _prompt()


def test_prompt_includes_measurements_and_marks_unknown_ones() -> None:
    prompt = _prompt()
    assert "- フォントサイズ: 58点(最小12pt / 14pt未満 60%)" in prompt
    assert "- フォント: 計測不可" in prompt
    assert "- 文字量: 40点(520字)" in prompt
    assert "- 埋め込み画像: 2個" in prompt


def test_notes_are_included_only_when_present() -> None:
    assert "[発表者ノート] 口頭で補足" in _prompt()
    no_notes = Page(no=3, title="効果", body="大幅改善")
    assert "発表者ノート" not in _prompt(no_notes)


def test_missing_title_is_marked() -> None:
    assert "[タイトル] (なし)" in _prompt(Page(no=3, title="", body="x"))


def test_boss_prompt_defines_the_llm_scored_criteria() -> None:
    for key in ("content_score", "figure_score", "chart_score", "null"):
        assert key in BOSS.system_prompt
