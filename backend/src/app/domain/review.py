"""Scoring model: the six criteria, the LLM's per-page assessment, and aggregation.

内容・図・グラフは LLM(ページ画像 + テキスト)が採点し、フォントサイズ・フォント・文字量は
`app.domain.metrics` が PDF から決定的に採点する。該当しない基準(図がないページの「図」など)は
score=None とし、平均から除外する。
"""

import base64
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.pages import Page
from app.domain.precheck import LintFinding

Criterion = Literal["内容", "フォントサイズ", "フォント", "図", "グラフ", "文字量"]
CRITERIA: tuple[Criterion, ...] = ("内容", "フォントサイズ", "フォント", "図", "グラフ", "文字量")


class CriterionScore(BaseModel):
    """Score (0-100) for one criterion; None when the criterion does not apply."""

    criterion: Criterion
    score: int | None
    note: str = ""


class PageAssessment(BaseModel):
    """What the LLM returns for one page (passed to Ollama as the JSON schema)."""

    content_score: int = Field(ge=0, le=100, description="内容の点数(0-100)")
    figure_score: int | None = Field(
        ge=0, le=100, description="図(写真・イラスト・図解・表)の点数。図が無ければ null"
    )
    chart_score: int | None = Field(ge=0, le=100, description="グラフの点数。グラフが無ければ null")
    good_points: list[str] = Field(description="このページの良い点(1〜3件)")
    bad_points: list[str] = Field(description="このページの悪い点(1〜3件)")
    fixes: list[str] = Field(description="具体的な修正点(1〜3件)")


class PageResult(BaseModel):
    """Review of one page: all six criteria in `CRITERIA` order plus comments.

    `score` is the mean of the applicable criteria. `thumbnail` is the page JPEG,
    base64-encoded (empty when the page has no image).
    """

    no: int
    title: str
    scores: list[CriterionScore]
    score: int | None
    good_points: list[str]
    bad_points: list[str]
    fixes: list[str]
    thumbnail: str

    @classmethod
    def build(
        cls, page: Page, assessment: PageAssessment, measured: list[CriterionScore]
    ) -> "PageResult":
        """Merge the LLM assessment with the measured criteria for `page`."""
        judged = {
            "内容": assessment.content_score,
            "図": assessment.figure_score,
            "グラフ": assessment.chart_score,
        }
        by_criterion = {m.criterion: m for m in measured}
        scores = [
            by_criterion.get(c) or CriterionScore(criterion=c, score=judged.get(c))
            for c in CRITERIA
        ]
        return cls(
            no=page.no,
            title=page.title,
            scores=scores,
            score=_mean([s.score for s in scores]),
            good_points=assessment.good_points,
            bad_points=assessment.bad_points,
            fixes=assessment.fixes,
            thumbnail=encode_thumbnail(page.image),
        )


class Verdict(BaseModel):
    """`passed`: overall score >= pass score. `overall_passed` also needs zero lint.

    `formal_passed`: no "must" rule-check finding (company rules). Deterministic: it does
    not depend on LLM scores, so the same document always gets the same value.
    """

    passed: bool
    overall_passed: bool
    formal_passed: bool = True


class Summary(BaseModel):
    """Whole-document result: per-criterion averages over reviewed pages.

    `verdict` is None when no page could be reviewed.
    """

    criteria: list[CriterionScore]
    score: int | None
    reviewed_pages: int
    failed_pages: int
    verdict: Verdict | None


def summarize(
    results: list[PageResult], failed_pages: int, lint: list[LintFinding], pass_score: int
) -> Summary:
    """Average each criterion over the pages where it applies, then judge."""
    criteria = []
    for criterion in CRITERIA:
        values = [s.score for r in results for s in r.scores if s.criterion == criterion]
        applicable = [v for v in values if v is not None]
        note = f"{len(applicable)}ページ" if applicable else ""
        criteria.append(CriterionScore(criterion=criterion, score=_mean(applicable), note=note))

    score = _mean([r.score for r in results])
    verdict = None
    if score is not None:
        passed = score >= pass_score
        verdict = Verdict(passed=passed, overall_passed=passed and not lint)
    return Summary(
        criteria=criteria,
        score=score,
        reviewed_pages=len(results),
        failed_pages=failed_pages,
        verdict=verdict,
    )


def _mean(values: Sequence[int | None]) -> int | None:
    applicable = [v for v in values if v is not None]
    return round(sum(applicable) / len(applicable)) if applicable else None


def encode_thumbnail(image: bytes) -> str:
    """Base64 text for embedding the page JPEG in JSON."""
    return base64.b64encode(image).decode("ascii")
