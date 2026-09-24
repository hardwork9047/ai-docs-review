"""Structured review output from the LLM and the pass/fail verdict.

`Review.model_json_schema()` is passed to Ollama's `format` so the model is forced to
emit JSON that validates against `Review`; the same model then validates the reply.
"""

from pydantic import BaseModel

from app.domain.precheck import LintFinding


class Issue(BaseModel):
    """One actionable finding: where / what / why / how to fix."""

    slide: int
    severity: str
    problem: str
    why: str
    fix: str


class Review(BaseModel):
    """The reviewer's full critique of a deck."""

    score: int
    summary: str
    good_points: list[str]
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
    raise NotImplementedError
