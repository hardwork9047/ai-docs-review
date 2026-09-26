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


def _ndjson(*chunks: dict[str, object]) -> httpx.Response:
    return httpx.Response(200, text="\n".join(json.dumps(c) for c in chunks) + "\n")


def test_complete_streams_chat_and_joins_the_content_chunks() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _ndjson(
            {"message": {"content": '{"score"'}, "done": False},
            {"message": {"content": ": 1}"}, "done": False},
            {"message": {"content": ""}, "done": True},
        )

    reply = asyncio.run(_client(handler).complete("sys", "usr", {"type": "object"}))

    assert reply == '{"score": 1}'
    assert str(seen[0].url) == "http://ollama.test/api/chat"
    body = json.loads(seen[0].content)
    assert body["model"] == "gemma4:e2b"
    assert body["stream"] is True
    assert body["format"] == {"type": "object"}
    assert body["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]
    assert body["options"] == {"temperature": 0.2, "num_ctx": 8192}
    assert "think" not in body  # 既定はモデル任せ


def test_images_are_attached_to_the_user_message_as_base64() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _ndjson({"message": {"content": "{}"}, "done": True})

    asyncio.run(_client(handler).complete("s", "u", {}, images=[b"\xff\xd8jpeg"]))
    user = json.loads(seen[0].content)["messages"][1]
    assert user["images"] == ["/9hqcGVn"]


def test_think_setting_is_forwarded_when_configured() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _ndjson({"message": {"content": "{}"}, "done": True})

    client = OllamaClient(
        Settings(ollama_url="http://ollama.test", think=False),
        transport=httpx.MockTransport(handler),
    )
    asyncio.run(client.complete("s", "u", {}))
    assert json.loads(seen[0].content)["think"] is False


@pytest.mark.parametrize(
    "handler",
    [
        lambda r: httpx.Response(500, text="boom"),
        lambda r: httpx.Response(200, text="not json\n"),
        lambda r: _ndjson({"error": "model not found"}),
    ],
    ids=["http-error", "malformed-line", "error-chunk"],
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


def _flaky(*statuses: int) -> tuple[Handler, list[httpx.Request]]:
    """Handler answering with `statuses` in order, then a successful stream."""
    seen: list[httpx.Request] = []
    queue = list(statuses)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if queue:
            return httpx.Response(queue.pop(0), text="")
        return _ndjson({"message": {"content": "{}"}, "done": True})

    return handler, seen


def test_cloudflare_timeout_is_retried_once() -> None:
    # Colab 起動直後の初回はモデル読み込みで Cloudflare の 100 秒制限(524)を超えることがある
    handler, seen = _flaky(524)
    assert asyncio.run(_client(handler).complete("s", "u", {})) == "{}"
    assert len(seen) == 2


def test_second_cloudflare_timeout_is_reported() -> None:
    handler, seen = _flaky(524, 524)
    with pytest.raises(LLMError, match="524"):
        asyncio.run(_client(handler).complete("s", "u", {}))
    assert len(seen) == 2


def test_other_server_errors_are_not_retried() -> None:
    handler, seen = _flaky(500)
    with pytest.raises(LLMError):
        asyncio.run(_client(handler).complete("s", "u", {}))
    assert len(seen) == 1


def test_configured_headers_are_sent_on_chat_and_health() -> None:
    # Modal の proxy auth(Modal-Key / Modal-Secret)など、接続先が要求する認証ヘッダー
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        return _ndjson({"message": {"content": "{}"}, "done": True})

    settings = Settings(
        ollama_url="http://ollama.test", ollama_headers={"Modal-Key": "k", "Modal-Secret": "s"}
    )
    client = OllamaClient(settings, transport=httpx.MockTransport(handler))
    asyncio.run(client.complete("s", "u", {}))
    asyncio.run(client.health())
    assert [(r.headers.get("Modal-Key"), r.headers.get("Modal-Secret")) for r in seen] == [
        ("k", "s"),
        ("k", "s"),
    ]


def test_headers_can_be_given_as_json_in_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REVIEW_OLLAMA_HEADERS", '{"Modal-Key": "k", "Modal-Secret": "s"}')
    assert Settings().ollama_headers == {"Modal-Key": "k", "Modal-Secret": "s"}


def test_no_extra_headers_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REVIEW_OLLAMA_HEADERS", raising=False)
    assert Settings().ollama_headers == {}


def test_health_waits_long_enough_for_a_cold_start(monkeypatch: pytest.MonkeyPatch) -> None:
    # Modal はアクセスが無いと GPU コンテナを止め、次の起動に 80 秒ほどかかる。
    # その間に接続ランプが「未接続」と誤表示されないよう、既定の待ち時間はそれより長くする
    monkeypatch.delenv("REVIEW_HEALTH_TIMEOUT_SECONDS", raising=False)
    assert Settings().health_timeout_seconds >= 120


def test_health_uses_the_configured_timeout() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"models": []})

    client = OllamaClient(
        Settings(ollama_url="http://ollama.test", health_timeout_seconds=7.5),
        transport=httpx.MockTransport(handler),
    )
    asyncio.run(client.health())
    assert seen[0].extensions["timeout"]["read"] == 7.5


def test_modal_timeout_redirect_is_followed_to_the_original_response() -> None:
    # Regression: Modal はリクエストが 150 秒を超えると 303 で待ち受け用の URL を返す
    # (__modal_attempt_token 付き)。GET で追うと元の応答(ストリーム)が届く。
    # コールドスタート直後の 1 ページ目がこれで失敗していた
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "POST":
            return httpx.Response(303, headers={"location": "/api/chat?__modal_attempt_token=abc"})
        return _ndjson({"message": {"content": '{"ok": 1}'}, "done": True})

    settings = Settings(ollama_url="http://ollama.test", ollama_headers={"Modal-Key": "k"})
    client = OllamaClient(settings, transport=httpx.MockTransport(handler))
    assert asyncio.run(client.complete("s", "u", {})) == '{"ok": 1}'
    follow = seen[1]
    assert (follow.method, follow.url.params["__modal_attempt_token"]) == ("GET", "abc")
    assert follow.headers["Modal-Key"] == "k"  # 認証ヘッダーを付けたまま追う
