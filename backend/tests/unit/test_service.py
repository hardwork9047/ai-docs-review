"""Unit tests for app.domain.service — 偽物の LLM を注入してイベント列を検証する。"""

import asyncio
import json
from collections.abc import Sequence
from typing import Any

from app.domain.pages import Page
from app.domain.review import PageAssessment
from app.domain.reviewer import BOSS
from app.domain.service import (
    DoneEvent,
    Event,
    LLMError,
    MetaEvent,
    PageErrorEvent,
    PageEvent,
    review_document,
)
from app.domain.standard import parse_pack

GOOD_REPLY = json.dumps(
    {
        "content_score": 60,
        "figure_score": None,
        "chart_score": 80,
        "good_points": ["グラフがある"],
        "bad_points": ["結論がない"],
        "fixes": ["タイトルを結論にする"],
    }
)


class FakeLLM:
    """Replies per call from `replies` (an Exception is raised); records every call."""

    def __init__(self, *replies: str | Exception) -> None:
        self.replies = list(replies)
        self.calls: list[tuple[str, str, dict[str, Any], list[bytes]]] = []

    async def complete(
        self, system: str, user: str, schema: dict[str, Any], images: Sequence[bytes] = ()
    ) -> str:
        self.calls.append((system, user, schema, list(images)))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return reply


def _pages(n: int) -> list[Page]:
    return [
        Page(no=i, title=f"t{i}", body="本文", char_sizes=(18.0,) * 10, image=b"img%d" % i)
        for i in range(1, n + 1)
    ]


def _run(pages: list[Page], llm: FakeLLM, max_pages: int = 40) -> list[Event]:
    async def collect() -> list[Event]:
        return [e async for e in review_document(pages, llm, max_pages=max_pages)]

    return asyncio.run(collect())


def test_event_sequence_is_meta_pages_done() -> None:
    events = _run(_pages(2), FakeLLM(GOOD_REPLY))
    assert [e.type for e in events] == ["meta", "page", "page", "done"]


def test_meta_reports_counts_lint_reviewer_and_criteria() -> None:
    pages = [Page(no=1, title="", body="ｱ")]
    meta = _run(pages, FakeLLM(GOOD_REPLY))[0]
    assert isinstance(meta, MetaEvent)
    assert meta.page_count == 1
    assert meta.review_count == 1
    assert not meta.truncated
    assert {f.rule for f in meta.lint} == {"半角カナ", "必須項目"}
    assert meta.reviewer == BOSS.profile
    assert meta.criteria == ["内容", "フォントサイズ", "フォント", "図", "グラフ", "文字量"]


def test_each_page_is_sent_with_its_image_prompt_and_schema() -> None:
    llm = FakeLLM(GOOD_REPLY)
    _run(_pages(2), llm)
    system, user, schema, images = llm.calls[1]
    assert system == BOSS.system_prompt
    assert "全2ページ中の2ページ目" in user
    assert schema == PageAssessment.model_json_schema()
    assert images == [b"img2"]


def test_page_without_image_is_sent_without_images() -> None:
    llm = FakeLLM(GOOD_REPLY)
    _run([Page(no=1, title="t", body="b")], llm)
    assert llm.calls[0][3] == []


def test_page_event_merges_llm_and_measured_scores() -> None:
    page_event = _run(_pages(1), FakeLLM(GOOD_REPLY))[1]
    assert isinstance(page_event, PageEvent)
    scores = {s.criterion: s.score for s in page_event.result.scores}
    assert scores == {
        "内容": 60,
        "フォントサイズ": 100,
        "フォント": None,
        "図": None,
        "グラフ": 80,
        "文字量": 100,
    }
    assert page_event.result.fixes == ["タイトルを結論にする"]


def test_failing_page_is_reported_and_the_rest_continue() -> None:
    events = _run(_pages(3), FakeLLM(GOOD_REPLY, LLMError("timeout"), '{"bad": 1}', GOOD_REPLY))
    assert [e.type for e in events] == ["meta", "page", "page_error", "page_error", "done"]
    llm_error, schema_error = events[2], events[3]
    assert isinstance(llm_error, PageErrorEvent)
    assert llm_error.no == 2
    assert "timeout" in llm_error.message
    assert isinstance(schema_error, PageErrorEvent)
    assert "スキーマ" in schema_error.message
    done = events[-1]
    assert isinstance(done, DoneEvent)
    assert done.summary.reviewed_pages == 1
    assert done.summary.failed_pages == 2


def test_only_max_pages_are_reviewed_and_truncation_is_flagged() -> None:
    llm = FakeLLM(GOOD_REPLY)
    events = _run(_pages(3), llm, max_pages=2)
    meta = events[0]
    assert isinstance(meta, MetaEvent)
    assert meta.page_count == 3
    assert meta.review_count == 2
    assert meta.truncated
    assert len(llm.calls) == 2
    assert [e.type for e in events].count("page") == 2


def test_done_carries_verdict_with_lint() -> None:
    done = _run(_pages(1), FakeLLM(GOOD_REPLY))[-1]
    assert isinstance(done, DoneEvent)
    assert done.summary.verdict is not None
    assert done.summary.score == 85  # (60 + 100 + 80 + 100) / 4
    assert done.summary.verdict.overall_passed


PACK = parse_pack(
    {
        "name": "サンプル",
        "version": "1.0",
        "rules": [
            {
                "id": "R-FORBID-01",
                "kind": "forbid",
                "patterns": ["本文"],
                "severity": "must",
                "source": "§1",
                "message": "禁止",
            }
        ],
    }
)


def _run_with_pack(pages: list[Page]) -> list[Event]:
    async def collect() -> list[Event]:
        return [
            e async for e in review_document(pages, FakeLLM(GOOD_REPLY), max_pages=40, pack=PACK)
        ]

    return asyncio.run(collect())


def test_pack_findings_follow_builtin_lint_and_name_the_pack() -> None:
    meta = _run_with_pack([Page(no=1, title="", body="本文")])[0]
    assert isinstance(meta, MetaEvent)
    assert [f.rule for f in meta.lint] == ["必須項目", "会社ルール"]
    assert meta.lint[1].rule_id == "R-FORBID-01"
    assert meta.standard is not None
    assert (meta.standard.name, meta.standard.version) == ("サンプル", "1.0")


def test_must_violation_fails_the_formal_verdict() -> None:
    done = _run_with_pack(_pages(1))[-1]
    assert isinstance(done, DoneEvent)
    assert done.summary.verdict is not None
    assert not done.summary.verdict.formal_passed


def test_without_a_pack_there_is_no_standard_and_no_company_findings() -> None:
    meta = _run(_pages(1), FakeLLM(GOOD_REPLY))[0]
    assert isinstance(meta, MetaEvent)
    assert meta.standard is None
    assert all(f.rule != "会社ルール" for f in meta.lint)


def test_llm_receives_the_pack_guidelines_in_the_system_prompt() -> None:
    pack = parse_pack(
        {
            "name": "サンプル",
            "version": "1.0",
            "rules": [],
            "review_guidelines": {"chart": ["単位と出典がある"]},
        }
    )
    llm = FakeLLM(GOOD_REPLY)

    async def collect() -> list[Event]:
        return [e async for e in review_document(_pages(1), llm, max_pages=40, pack=pack)]

    asyncio.run(collect())
    system = llm.calls[0][0]
    assert system.startswith(BOSS.system_prompt)
    assert "単位と出典がある" in system
