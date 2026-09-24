"""Structured review output from the LLM and the pass/fail verdict.

`Review.model_json_schema()` is passed to Ollama's `format` so the model is forced to
emit JSON that validates against `Review`; the same model then validates the reply.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.domain.precheck import LintFinding


class Issue(BaseModel):
    """One actionable finding: where / what / why / how to fix."""

    slide: int = Field(description="対象スライド番号。資料全体への指摘は0")
    severity: Literal["高", "中", "低"]
    problem: str = Field(description="何が問題か")
    why: str = Field(description="なぜ問題か")
    fix: str = Field(description="どう直すか(具体的に)")


class Review(BaseModel):
    """The reviewer's full critique of a deck."""

    score: int = Field(ge=0, le=100, description="この視点での資料の完成度(0-100)")
    summary: str = Field(description="総評を2〜3文で")
    good_points: list[str] = Field(description="良い点(最低1つ)")
    issues: list[Issue]


class Verdict(BaseModel):
    """Outcome of judging a review.

    `passed` reflects the reviewer alone; `overall_passed` additionally requires zero
    rule-check findings.
    """

    passed: bool
    high_issues: int
    overall_passed: bool


def judge(review: Review, lint: list[LintFinding], pass_score: int) -> Verdict:
    """Pass when score >= pass_score and there is no 高 issue; overall also needs no lint."""
    high = sum(1 for issue in review.issues if issue.severity == "高")
    passed = review.score >= pass_score and high == 0
    return Verdict(passed=passed, high_issues=high, overall_passed=passed and not lint)
