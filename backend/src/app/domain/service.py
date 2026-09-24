"""Review orchestration: rule checks, then one LLM call per page, then a summary.

The LLM is injected through the `ReviewLLM` port so this module stays testable
without Ollama. The API layer serialises each event as one NDJSON line:
`meta` → (`page` | `page_error`) x pages → `done`.
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any, Literal, Protocol

from pydantic import BaseModel

from app.domain.pages import Page
from app.domain.precheck import LintFinding
from app.domain.review import CRITERIA, Criterion, PageResult, Summary
from app.domain.reviewer import BOSS, Reviewer, ReviewerProfile


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
    raise NotImplementedError
    yield  # pragma: no cover - makes this an async generator
