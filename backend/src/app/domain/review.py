"""Scoring model: the six criteria, the LLM's per-page assessment, and aggregation.

内容・図・グラフは LLM(ページ画像 + テキスト)が採点し、フォントサイズ・フォント・文字量は
`app.domain.metrics` が PDF から決定的に採点する。該当しない基準(図がないページの「図」など)は
score=None とし、平均から除外する。
"""

import base64
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

    content_score: int
    figure_score: int | None
    chart_score: int | None
    good_points: list[str]
    bad_points: list[str]
    fixes: list[str]


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
        raise NotImplementedError


class Verdict(BaseModel):
    """`passed`: overall score >= pass score. `overall_passed` also needs zero lint."""

    passed: bool
    overall_passed: bool


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
    raise NotImplementedError


def encode_thumbnail(image: bytes) -> str:
    """Base64 text for embedding the page JPEG in JSON."""
    return base64.b64encode(image).decode("ascii")
