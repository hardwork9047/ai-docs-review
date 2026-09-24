"""Unit tests for app.domain.review — LLM 出力の検証と合否判定。"""

import pytest
from pydantic import ValidationError

from app.domain.precheck import LintFinding
from app.domain.review import Issue, Review, judge


def _issue(severity: str) -> Issue:
    return Issue(slide=1, severity=severity, problem="p", why="w", fix="f")


def _review(score: int, *severities: str) -> Review:
    return Review(
        score=score, summary="s", good_points=["g"], issues=[_issue(s) for s in severities]
    )


LINT = [LintFinding("半角カナ", "d")]


def test_score_at_threshold_without_high_issue_passes() -> None:
    verdict = judge(_review(70, "中", "低"), [], pass_score=70)
    assert verdict.passed
    assert verdict.overall_passed
    assert verdict.high_issues == 0


def test_score_below_threshold_fails() -> None:
    assert not judge(_review(69), [], pass_score=70).passed


def test_any_high_issue_fails_even_with_full_score() -> None:
    verdict = judge(_review(100, "高", "高", "中"), [], pass_score=70)
    assert not verdict.passed
    assert verdict.high_issues == 2


def test_lint_findings_fail_overall_but_not_reviewer() -> None:
    verdict = judge(_review(90), LINT, pass_score=70)
    assert verdict.passed
    assert not verdict.overall_passed


def test_valid_llm_json_is_parsed() -> None:
    raw = (
        '{"score": 80, "summary": "s", "good_points": ["g"],'
        ' "issues": [{"slide": 0, "severity": "高", "problem": "p", "why": "w", "fix": "f"}]}'
    )
    assert Review.model_validate_json(raw).issues[0].severity == "高"


@pytest.mark.parametrize("score", [-1, 101])
def test_score_out_of_range_is_rejected(score: int) -> None:
    with pytest.raises(ValidationError):
        _review(score)


def test_unknown_severity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _issue("緊急")


def test_json_schema_constrains_severity_and_score_for_the_llm() -> None:
    schema = Review.model_json_schema()
    issue_schema = schema["$defs"]["Issue"]["properties"]
    assert issue_schema["severity"]["enum"] == ["高", "中", "低"]
    assert schema["properties"]["score"]["maximum"] == 100
    assert set(schema["required"]) == {"score", "summary", "good_points", "issues"}
