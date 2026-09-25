"""Unit tests for app.domain.review — LLM 評価と計測値の統合、全体集計と判定。"""

import pytest
from pydantic import ValidationError

from app.domain.pages import Page
from app.domain.precheck import LintFinding
from app.domain.review import (
    CRITERIA,
    CriterionScore,
    PageAssessment,
    PageResult,
    summarize,
)

MEASURED = [
    CriterionScore(criterion="フォントサイズ", score=80, note="最小12pt"),
    CriterionScore(criterion="フォント", score=100, note="Meiryo"),
    CriterionScore(criterion="文字量", score=60, note="300字"),
]


def _assessment(
    content: int = 70, figure: int | None = 90, chart: int | None = None
) -> PageAssessment:
    return PageAssessment(
        content_score=content,
        figure_score=figure,
        chart_score=chart,
        good_points=["g"],
        bad_points=["b"],
        fixes=["f"],
    )


def _result(no: int, **kw: int | None) -> PageResult:
    page = Page(no=no, title=f"p{no}", body="", image=b"\xff\xd8")
    return PageResult.build(page, _assessment(**kw), MEASURED)


def test_build_orders_all_six_criteria() -> None:
    result = _result(1)
    assert [s.criterion for s in result.scores] == list(CRITERIA)
    assert [s.score for s in result.scores] == [70, 80, 100, 90, None, 60]
    assert result.scores[1].note == "最小12pt"


def test_page_score_is_mean_of_applicable_criteria() -> None:
    assert _result(1).score == 80  # (70 + 80 + 100 + 90 + 60) / 5


def test_build_carries_comments_title_and_base64_thumbnail() -> None:
    result = _result(3)
    assert (result.no, result.title) == (3, "p3")
    assert (result.good_points, result.bad_points, result.fixes) == (["g"], ["b"], ["f"])
    assert result.thumbnail == "/9g="


def test_summary_averages_each_criterion_over_applicable_pages() -> None:
    summary = summarize([_result(1, figure=90), _result(2, figure=None, chart=50)], 0, [], 70)
    by_name = {c.criterion: c for c in summary.criteria}
    assert by_name["図"].score == 90
    assert by_name["図"].note == "1ページ"
    assert by_name["グラフ"].score == 50
    assert by_name["内容"].note == "2ページ"
    assert summary.reviewed_pages == 2


def test_summary_score_is_mean_of_page_scores_and_passes_at_threshold() -> None:
    summary = summarize([_result(1)], failed_pages=1, lint=[], pass_score=80)
    assert summary.score == 80
    assert summary.failed_pages == 1
    assert summary.verdict is not None
    assert summary.verdict.passed
    assert summary.verdict.overall_passed


def test_lint_blocks_overall_pass_only() -> None:
    summary = summarize([_result(1)], 0, [LintFinding("半角カナ", "d")], 70)
    assert summary.verdict is not None
    assert summary.verdict.passed
    assert not summary.verdict.overall_passed


def test_below_threshold_fails() -> None:
    summary = summarize([_result(1)], 0, [], 81)
    assert summary.verdict is not None
    assert not summary.verdict.passed


def test_no_reviewed_page_means_no_verdict() -> None:
    summary = summarize([], failed_pages=3, lint=[], pass_score=70)
    assert summary.verdict is None
    assert summary.score is None
    assert all(c.score is None for c in summary.criteria)


@pytest.mark.parametrize("field", ["content_score", "figure_score", "chart_score"])
def test_llm_scores_out_of_range_are_rejected(field: str) -> None:
    values = {"content_score": 50, "figure_score": 50, "chart_score": 50, field: 101}
    with pytest.raises(ValidationError):
        PageAssessment(good_points=[], bad_points=[], fixes=[], **values)


def test_llm_schema_requires_every_field_and_allows_null_figure_and_chart() -> None:
    schema = PageAssessment.model_json_schema()
    assert set(schema["required"]) == {
        "content_score",
        "figure_score",
        "chart_score",
        "good_points",
        "bad_points",
        "fixes",
    }
    figure_types = {branch["type"] for branch in schema["properties"]["figure_score"]["anyOf"]}
    assert figure_types == {"integer", "null"}
    assert schema["properties"]["content_score"]["maximum"] == 100
