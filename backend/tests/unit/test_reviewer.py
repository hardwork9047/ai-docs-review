"""Unit tests for app.domain.reviewer — 1ページ分のユーザープロンプト組み立て。"""

from app.domain.pages import Page
from app.domain.review import CriterionScore
from app.domain.reviewer import BOSS, build_page_prompt, build_system_prompt
from app.domain.standard import StandardPack, parse_pack

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
    assert "- フォントサイズ: 最小12pt / 14pt未満 60%(判定: 要改善)" in prompt
    assert "- フォント: 計測不可" in prompt
    assert "- 文字量: 520字(判定: 要改善)" in prompt
    assert "- 埋め込み画像: 2個" in prompt


def test_measured_scores_are_not_shown_as_numbers() -> None:
    # 小型モデルが「58点」を「58pt」と読み違えたため、点数は数値で渡さない
    prompt = _prompt()
    assert "58点" not in prompt
    assert "40点" not in prompt


def test_measurement_verdict_bands() -> None:
    measured = [
        CriterionScore(criterion="フォントサイズ", score=85, note="a"),
        CriterionScore(criterion="フォント", score=70, note="b"),
        CriterionScore(criterion="文字量", score=59, note="c"),
    ]
    prompt = build_page_prompt(PAGE, total=10, outline=[], measured=measured)
    assert "- フォントサイズ: a(判定: 良好)" in prompt
    assert "- フォント: b(判定: やや問題)" in prompt
    assert "- 文字量: c(判定: 要改善)" in prompt


def test_notes_are_included_only_when_present() -> None:
    assert "[発表者ノート] 口頭で補足" in _prompt()
    no_notes = Page(no=3, title="効果", body="大幅改善")
    assert "発表者ノート" not in _prompt(no_notes)


def test_missing_title_is_marked() -> None:
    assert "[タイトル] (なし)" in _prompt(Page(no=3, title="", body="x"))


def test_boss_prompt_defines_the_llm_scored_criteria() -> None:
    for key in ("content_score", "figure_score", "chart_score", "null"):
        assert key in BOSS.system_prompt


def _pack(guidelines: dict[str, list[str]] | None = None) -> StandardPack:
    data: dict[str, object] = {"name": "製造基準", "version": "2.1", "rules": []}
    if guidelines is not None:
        data["review_guidelines"] = guidelines
    return parse_pack(data)


def test_system_prompt_is_unchanged_without_pack_or_guidelines() -> None:
    assert build_system_prompt(BOSS, None) == BOSS.system_prompt
    assert build_system_prompt(BOSS, _pack()) == BOSS.system_prompt


def test_system_prompt_lists_company_guidelines_by_criterion() -> None:
    prompt = build_system_prompt(
        BOSS, _pack({"content": ["代替案と比較している"], "chart": ["単位と出典がある"]})
    )
    assert prompt.startswith(BOSS.system_prompt)
    assert "## 会社の観点(基準パック「製造基準」v2.1)" in prompt
    assert "- 内容(content_score):\n  - 代替案と比較している" in prompt
    assert "- グラフ(chart_score):\n  - 単位と出典がある" in prompt
    assert "図(figure_score)" not in prompt  # 空の観点は出さない
    assert "bad_points" in prompt.split("## 会社の観点")[1]
