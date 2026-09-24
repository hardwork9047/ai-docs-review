"""Unit tests for app.domain.service — 偽物の LLM を注入してイベント列を検証する。"""

import asyncio
import json
from typing import Any

from app.domain.review import Review
from app.domain.reviewer import BOSS
from app.domain.service import (
    ErrorEvent,
    Event,
    LLMError,
    MetaEvent,
    ResultEvent,
    review_deck,
)
from app.domain.slides import Slide

GOOD_REPLY = json.dumps(
    {
        "score": 85,
        "summary": "結論が明確",
        "good_points": ["1枚目に結論"],
        "issues": [{"slide": 2, "severity": "中", "problem": "p", "why": "w", "fix": "f"}],
    }
)


class FakeLLM:
    """Returns a canned reply (or raises) and records what it was asked."""

    def __init__(self, reply: str = GOOD_REPLY, error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def complete(self, system: str, user: str, schema: dict[str, Any]) -> str:
        self.calls.append((system, user, schema))
        if self.error:
            raise self.error
        return self.reply


def _run(slides: list[Slide], llm: FakeLLM, max_slides: int = 40) -> list[Event]:
    async def collect() -> list[Event]:
        return [e async for e in review_deck(slides, llm, max_slides=max_slides)]

    return asyncio.run(collect())


DECK = [Slide(no=1, title="表紙", body="承認依頼"), Slide(no=2, title="結論", body="A案")]


def test_meta_comes_first_with_lint_and_reviewer_profile() -> None:
    events = _run([Slide(no=1, title="", body="ｱ")], FakeLLM())
    meta = events[0]
    assert isinstance(meta, MetaEvent)
    assert meta.slide_count == 1
    assert not meta.truncated
    assert {f.rule for f in meta.lint} == {"半角カナ", "必須項目"}
    assert meta.reviewer == BOSS.profile


def test_successful_review_ends_with_result_and_verdict() -> None:
    events = _run(DECK, FakeLLM())
    assert len(events) == 2
    result = events[1]
    assert isinstance(result, ResultEvent)
    assert result.review.score == 85
    assert result.verdict.passed
    assert result.verdict.overall_passed


def test_llm_receives_boss_prompt_deck_text_and_review_schema() -> None:
    llm = FakeLLM()
    _run(DECK, llm)
    system, user, schema = llm.calls[0]
    assert system == BOSS.system_prompt
    assert "--- スライド2 ---" in user
    assert schema == Review.model_json_schema()


def test_truncation_is_flagged_when_deck_exceeds_max_slides() -> None:
    meta = _run(DECK, FakeLLM(), max_slides=1)[0]
    assert isinstance(meta, MetaEvent)
    assert meta.truncated


def test_llm_backend_failure_becomes_error_event() -> None:
    events = _run(DECK, FakeLLM(error=LLMError("connection refused")))
    assert isinstance(events[-1], ErrorEvent)
    assert "connection refused" in events[-1].message


def test_schema_invalid_reply_becomes_error_event() -> None:
    events = _run(DECK, FakeLLM(reply='{"score": 500}'))
    assert isinstance(events[-1], ErrorEvent)
    assert "スキーマ" in events[-1].message
