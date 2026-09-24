"""Review orchestration: rule checks, then one LLM call per page, then a summary.

The LLM is injected through the `ReviewLLM` port so this module stays testable
without Ollama. The API layer serialises each event as one NDJSON line:
`meta` → (`page` | `page_error`) x pages → `done`.
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ValidationError

from app.domain.metrics import measure
from app.domain.pages import Page
from app.domain.precheck import LintFinding, run_precheck
from app.domain.review import (
    CRITERIA,
    Criterion,
    PageAssessment,
    PageResult,
    Summary,
    summarize,
)
from app.domain.reviewer import BOSS, Reviewer, ReviewerProfile, build_page_prompt


class LLMError(Exception):
    """The LLM backend could not produce a reply (connection, HTTP or timeout failure)."""


class ReviewLLM(Protocol):
    """Port for a (vision) chat LLM that returns JSON constrained by a JSON schema."""

    async def complete(
        self, system: str, user: str, schema: dict[str, Any], images: Sequence[bytes] = ()
    ) -> str:
        """Return the raw JSON text of the reply. Raise `LLMError` on backend failure.

        `images` are attached to the user message (JPEG/PNG bytes).
        """
        ...


class MetaEvent(BaseModel):
    """First event: available immediately, before the LLM runs."""

    type: Literal["meta"] = "meta"
    page_count: int
    truncated: bool
    lint: list[LintFinding]
    reviewer: ReviewerProfile
    criteria: list[Criterion] = list(CRITERIA)


class PageEvent(BaseModel):
    """One page reviewed successfully."""

    type: Literal["page"] = "page"
    result: PageResult


class PageErrorEvent(BaseModel):
    """One page could not be reviewed (LLM failure or schema-invalid reply)."""

    type: Literal["page_error"] = "page_error"
    no: int
    message: str


class DoneEvent(BaseModel):
    """Last event: the whole-document summary and verdict."""

    type: Literal["done"] = "done"
    summary: Summary


Event = MetaEvent | PageEvent | PageErrorEvent | DoneEvent


async def review_document(
    pages: list[Page], llm: ReviewLLM, *, max_pages: int, reviewer: Reviewer = BOSS
) -> AsyncIterator[Event]:
    """Yield `MetaEvent`, one `PageEvent`/`PageErrorEvent` per page, then `DoneEvent`.

    Only the first `max_pages` pages are reviewed. A failing page does not stop the
    others, because the HTTP response is already streaming.
    """
    lint = run_precheck(pages)
    yield MetaEvent(
        page_count=len(pages),
        truncated=len(pages) > max_pages,
        lint=lint,
        reviewer=reviewer.profile,
    )

    targets = pages[:max_pages]
    outline = [p.title for p in targets]
    schema = PageAssessment.model_json_schema()
    results: list[PageResult] = []
    failed = 0
    for page in targets:
        measured = measure(page)
        prompt = build_page_prompt(page, len(targets), outline, measured)
        images = [page.image] if page.image else []
        try:
            raw = await llm.complete(reviewer.system_prompt, prompt, schema, images)
            assessment = PageAssessment.model_validate_json(raw)
        except LLMError as exc:
            failed += 1
            yield PageErrorEvent(no=page.no, message=f"LLMの呼び出しに失敗しました: {exc}")
            continue
        except ValidationError as exc:
            failed += 1
            yield PageErrorEvent(no=page.no, message=f"LLMの出力がスキーマに合いません: {exc}")
            continue
        result = PageResult.build(page, assessment, measured)
        results.append(result)
        yield PageEvent(result=result)

    yield DoneEvent(summary=summarize(results, failed, lint, reviewer.pass_score))
