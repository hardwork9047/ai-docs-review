"""Unit tests for app.domain.standard — 会社ルール(基準パック)の決定的な判定。"""

from typing import Any

import pytest

from app.domain.pages import Page
from app.domain.precheck import LintFinding
from app.domain.standard import PackError, check_pack, parse_pack

PACK: dict[str, Any] = {
    "name": "サンプル",
    "version": "1.0",
    "rules": [
        {
            "id": "R-FORBID-01",
            "kind": "forbid",
            "patterns": ["必ず改善", "絶対"],
            "severity": "must",
            "source": "ガイドライン §4.2",
            "message": "効果を言い切らない",
        },
        {
            "id": "R-TERM-01",
            "kind": "prefer",
            "patterns": ["利用者さん"],
            "use": "利用者様",
            "source": "ガイドライン §3.1",
            "message": "施設の利用者の表記",
        },
        {
            "id": "R-REQ-01",
            "kind": "required",
            "patterns": ["料金|費用|お見積"],
            "regex": True,
            "severity": "must",
            "source": "ガイドライン §2.1",
            "message": "料金を記載する",
        },
    ],
}


def _pages(*bodies: str) -> list[Page]:
    return [Page(no=i, title=f"t{i}", body=b) for i, b in enumerate(bodies, start=1)]


def _check(*bodies: str) -> list[LintFinding]:
    return check_pack(_pages(*bodies), parse_pack(PACK))


def test_clean_document_has_no_findings() -> None:
    assert _check("導入で業務の改善が見込めます", "料金は別紙のとおり") == []


def test_forbidden_expression_is_reported_with_page_source_and_severity() -> None:
    findings = _check("導入すれば必ず改善します", "料金: 月3万円")
    assert findings == [
        LintFinding(
            rule="会社ルール",
            detail="効果を言い切らない(「必ず改善」)",
            rule_id="R-FORBID-01",
            severity="must",
            source="ガイドライン §4.2",
            page=1,
        )
    ]


def test_each_matched_text_is_reported_once_per_page() -> None:
    findings = _check("絶対に必ず改善、絶対です", "料金あり")
    assert [f.detail for f in findings] == [
        "効果を言い切らない(「必ず改善」)",
        "効果を言い切らない(「絶対」)",
    ]


def test_discouraged_spelling_suggests_the_approved_one() -> None:
    findings = _check("利用者さんの見守り", "費用は別途")
    assert findings[0].detail == "施設の利用者の表記: 「利用者さん」→「利用者様」"
    assert (findings[0].rule_id, findings[0].severity, findings[0].page) == (
        "R-TERM-01",
        "should",
        1,
    )


def test_missing_required_item_is_a_document_level_finding() -> None:
    findings = _check("概要", "スケジュール")
    assert findings == [
        LintFinding(
            rule="会社ルール",
            detail="料金を記載する",
            rule_id="R-REQ-01",
            severity="must",
            source="ガイドライン §2.1",
            page=0,
        )
    ]


def test_titles_are_checked_but_speaker_notes_are_not() -> None:
    pages = [
        Page(no=1, title="絶対に効果", body="料金あり"),
        Page(no=2, title="t", body="b", notes="必ず改善と口頭で言う"),
    ]
    findings = check_pack(pages, parse_pack(PACK))
    assert [(f.page, f.detail) for f in findings] == [(1, "効果を言い切らない(「絶対」)")]


def test_page_findings_come_in_page_then_rule_order_and_required_last() -> None:
    findings = _check("利用者さん", "必ず改善")
    assert [(f.page, f.rule_id) for f in findings] == [
        (1, "R-TERM-01"),
        (2, "R-FORBID-01"),
        (0, "R-REQ-01"),
    ]


def test_same_input_gives_identical_results() -> None:
    bodies = ("利用者さん 絶対", "必ず改善", "お見積")
    assert _check(*bodies) == _check(*bodies)


def test_regex_patterns_only_when_enabled() -> None:
    literal = {**PACK, "rules": [{**PACK["rules"][0], "patterns": ["a.c"]}]}
    pack = parse_pack(literal)
    assert check_pack(_pages("abc"), pack) == []
    assert len(check_pack(_pages("a.c"), pack)) == 1


@pytest.mark.parametrize(
    ("broken", "reason"),
    [
        ({**PACK, "rules": [PACK["rules"][0], PACK["rules"][0]]}, "重複"),
        ({**PACK, "rules": [{**PACK["rules"][2], "patterns": ["料金("]}]}, "正規表現"),
        ({**PACK, "rules": [{**PACK["rules"][1], "use": ""}]}, "use"),
        ({**PACK, "rules": [{**PACK["rules"][0], "patterns": []}]}, "patterns"),
        ({**PACK, "rules": [{**PACK["rules"][0], "kind": "unknown"}]}, "kind"),
        ({"name": "x"}, "version"),
        ("not a mapping", "形式"),
    ],
)
def test_invalid_packs_are_rejected_with_a_reason(broken: object, reason: str) -> None:
    with pytest.raises(PackError, match=reason):
        parse_pack(broken)


def test_spaces_and_line_breaks_inside_a_match_are_ignored() -> None:
    # Regression: PDF のテキスト抽出は書体の切り替わりに空白を、折り返しに改行を入れる
    # (「業界 No.1」「山田花子様 (85 歳 )」「必\nず改善」)。照合では空白・改行を無視する
    findings = _check("効果は必\nず改善します", "料 金は別紙")
    assert [(f.rule_id, f.page) for f in findings] == [("R-FORBID-01", 1)]
    assert findings[0].detail == "効果を言い切らない(「必ず改善」)"


def test_required_item_is_not_satisfied_across_a_page_boundary() -> None:
    # Regression: 空白を詰めるときにページの境目まで詰めると、1ページ目末尾の「料」と
    # 2ページ目先頭の「金」がつながって「料金あり」と誤判定されていた
    pages = [Page(no=1, title="t1", body="概要と料"), Page(no=2, title="金額感", body="なし")]
    findings = check_pack(pages, parse_pack(PACK))
    assert [f.rule_id for f in findings] == ["R-REQ-01"]


def test_matches_do_not_span_the_title_and_the_body() -> None:
    pages = [Page(no=1, title="効果は必", body="ず改善の料金")]
    assert check_pack(pages, parse_pack(PACK)) == []


def test_dot_in_a_regex_does_not_cross_a_boundary() -> None:
    pack = parse_pack(
        {**PACK, "rules": [{**PACK["rules"][2], "patterns": ["料.金"], "regex": True}]}
    )
    pages = [Page(no=1, title="t", body="料"), Page(no=2, title="金", body="x")]
    assert [f.rule_id for f in check_pack(pages, pack)] == ["R-REQ-01"]


GUIDELINES = {
    "content": ["代替案と比較している"],
    "figure": ["図の文字が読める大きさ"],
    "chart": ["単位と出典がある", "強調色は1色"],
}


def test_review_guidelines_are_optional_and_parsed() -> None:
    assert parse_pack(PACK).review_guidelines.chart == []
    pack = parse_pack({**PACK, "review_guidelines": GUIDELINES})
    assert pack.review_guidelines.chart == ["単位と出典がある", "強調色は1色"]


@pytest.mark.parametrize(
    ("guidelines", "reason"),
    [
        ({"chart": [f"観点{i}" for i in range(6)]}, "5"),
        ({"figure": ["あ" * 201]}, "200"),
        ({"figure": [""]}, "空"),
        ({"layout": ["x"]}, "review_guidelines"),
    ],
)
def test_invalid_review_guidelines_are_rejected(guidelines: dict[str, Any], reason: str) -> None:
    with pytest.raises(PackError, match=reason):
        parse_pack({**PACK, "review_guidelines": guidelines})
