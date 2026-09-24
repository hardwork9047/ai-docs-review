"""Integration tests for app.infra.ollama — httpx.MockTransport で Ollama を差し替える。"""

import asyncio
import json
from collections.abc import Callable

import httpx
import pytest

from app.domain.service import LLMError
from app.infra.ollama import OllamaClient
from app.infra.settings import Settings

SETTINGS = Settings(ollama_url="http://ollama.test", model="gemma4:e2b")
Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> OllamaClient:
    return OllamaClient(SETTINGS, transport=httpx.MockTransport(handler))


def test_complete_posts_chat_request_with_schema_and_returns_content() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"message": {"content": '{"score": 1}'}})

    reply = asyncio.run(_client(handler).complete("sys", "usr", {"type": "object"}))

    assert reply == '{"score": 1}'
    assert str(seen[0].url) == "http://ollama.test/api/chat"
    body = json.loads(seen[0].content)
    assert body["model"] == "gemma4:e2b"
    assert body["stream"] is False
    assert body["format"] == {"type": "object"}
    assert body["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]
    assert body["options"] == {"temperature": 0.2, "num_ctx": 8192}


@pytest.mark.parametrize(
    "handler",
    [
        lambda r: httpx.Response(500, text="boom"),
        lambda r: httpx.Response(200, json={"unexpected": True}),
    ],
    ids=["http-error", "malformed-body"],
)
def test_complete_wraps_backend_failures_in_llm_error(handler: Handler) -> None:
    with pytest.raises(LLMError):
        asyncio.run(_client(handler).complete("s", "u", {}))


def test_complete_wraps_connection_error_in_llm_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(LLMError, match="refused"):
        asyncio.run(_client(handler).complete("s", "u", {}))


@pytest.mark.parametrize(
    ("names", "ready"),
    [(["gemma4:e2b", "x:1"], True), (["gemma4:e4b"], False), ([], False)],
)
def test_health_reports_whether_configured_model_is_pulled(names: list[str], ready: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": n} for n in names]})

    health = asyncio.run(_client(handler).health())
    assert health.ok
    assert health.model == "gemma4:e2b"
    assert health.model_ready is ready


def test_health_accepts_implicit_latest_tag() -> None:
    client = OllamaClient(
        Settings(ollama_url="http://ollama.test", model="llama3"),
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"models": [{"name": "llama3:latest"}]})
        ),
    )
    assert asyncio.run(client.health()).model_ready


def test_health_reports_unreachable_ollama_without_raising() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    health = asyncio.run(_client(handler).health())
    assert not health.ok
    assert health.error is not None


def test_settings_can_be_overridden_by_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REVIEW_MODEL", "gemma3:4b")
    assert Settings().model == "gemma3:4b"
