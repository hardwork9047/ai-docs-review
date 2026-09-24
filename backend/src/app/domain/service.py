"""Review orchestration: rule checks, one LLM review, verdict — emitted as events.

The LLM is injected through the `ReviewLLM` port so this module stays testable
without Ollama. The API layer serialises each event as one NDJSON line.
"""

from collections.abc import AsyncIterator
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ValidationError

from app.domain.precheck import LintFinding, run_precheck
from app.domain.review import Review, Verdict, judge
from app.domain.reviewer import BOSS, Reviewer, ReviewerProfile
from app.domain.slides import Slide, build_user_prompt


class LLMError(Exception):
    """The LLM backend could not produce a reply (connection, HTTP or timeout failure)."""


class ReviewLLM(Protocol):
    """Port for a chat LLM that returns JSON constrained by a JSON schema."""

    async def complete(self, system: str, user: str, schema: dict[str, Any]) -> str:
        """Return the raw JSON text of the reply. Raise `LLMError` on backend failure."""
        ...


class MetaEvent(BaseModel):
    """First event: available immediately, before the LLM runs."""

    type: Literal["meta"] = "meta"
    slide_count: int
    truncated: bool
    lint: list[LintFinding]
    reviewer: ReviewerProfile


class ResultEvent(BaseModel):
    """Final event on success: the validated review and its verdict."""

    type: Literal["result"] = "result"
    review: Review
    verdict: Verdict


class ErrorEvent(BaseModel):
    """Final event on failure: the LLM failed or replied with schema-invalid JSON."""

    type: Literal["error"] = "error"
    message: str


Event = MetaEvent | ResultEvent | ErrorEvent


async def review_deck(
    slides: list[Slide], llm: ReviewLLM, *, max_slides: int, reviewer: Reviewer = BOSS
) -> AsyncIterator[Event]:
    """Yield a `MetaEvent`, then exactly one `ResultEvent` or `ErrorEvent`.

    LLM backend errors and invalid LLM output become an `ErrorEvent` rather than
    raising, because the HTTP response has already started streaming by then.
    """
    lint = run_precheck(slides)
    yield MetaEvent(
        slide_count=len(slides),
        truncated=len(slides) > max_slides,
        lint=lint,
        reviewer=reviewer.profile,
    )

    user_prompt = build_user_prompt(slides, max_slides)
    try:
        raw = await llm.complete(reviewer.system_prompt, user_prompt, Review.model_json_schema())
        review = Review.model_validate_json(raw)
    except LLMError as exc:
        yield ErrorEvent(message=f"LLMの呼び出しに失敗しました: {exc}")
        return
    except ValidationError as exc:
        yield ErrorEvent(message=f"LLMの出力がスキーマに合いません: {exc}")
        return

    yield ResultEvent(review=review, verdict=judge(review, lint, reviewer.pass_score))
