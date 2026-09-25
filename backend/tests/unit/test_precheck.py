"""Unit tests for app.domain.precheck — LLM を使わない決定的ルールチェック。"""

from app.domain.pages import Page
from app.domain.precheck import MAX_LINE_LEN, LintFinding, run_precheck


def _deck(*bodies: str, title: str = "表紙") -> list[Page]:
    return [Page(no=i, title=title, body=b) for i, b in enumerate(bodies, start=1)]


def test_clean_deck_has_no_findings() -> None:
    assert run_precheck(_deck("サーバーを増設します")) == []


def test_mixed_spelling_variants_are_reported() -> None:
    findings = run_precheck(_deck("サーバーを増設", "サーバの台数"))
    assert findings == [LintFinding("表記ゆれ", "「サーバー」と「サーバ」が混在しています")]


def test_long_form_alone_is_not_a_variant_mix() -> None:
    # 「サーバー」は「サーバ」を部分文字列として含むが、混在ではない
    assert run_precheck(_deck("サーバーとサーバーラック")) == []


def test_variant_in_title_is_also_checked() -> None:
    slides = [Page(no=1, title="ユーザー調査", body=""), Page(no=2, title="t", body="ユーザ数")]
    assert [f.rule for f in run_precheck(slides)] == ["表記ゆれ"]


def test_halfwidth_katakana_is_reported() -> None:
    assert [f.rule for f in run_precheck(_deck("ｻｰﾊﾞ"))] == ["半角カナ"]


def test_overlong_body_line_is_reported_with_slide_number_and_length() -> None:
    line = "あ" * (MAX_LINE_LEN + 1)
    findings = run_precheck(_deck("短い", line))
    assert findings == [
        LintFinding("長文", f"スライド2: 1文が{MAX_LINE_LEN + 1}字(分割か箇条書き化を推奨)")
    ]


def test_line_at_limit_is_not_reported() -> None:
    assert run_precheck(_deck("あ" * MAX_LINE_LEN)) == []


def test_empty_cover_title_is_reported() -> None:
    assert [f.rule for f in run_precheck(_deck("本文", title=""))] == ["必須項目"]


def test_empty_deck_has_no_findings() -> None:
    assert run_precheck([]) == []
