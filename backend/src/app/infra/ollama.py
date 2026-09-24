"""Ollama adapter implementing the domain `ReviewLLM` port over its HTTP API."""

import base64
import json
from collections.abc import Sequence
from typing import Any

import httpx
from pydantic import BaseModel

from app.domain.service import LLMError
from app.infra.settings import Settings


class OllamaHealth(BaseModel):
    """Reachability of Ollama and whether the configured model has been pulled."""

    ok: bool
    model: str
    model_ready: bool = False
    error: str | None = None


class OllamaClient:
    """Calls `/api/chat` with structured outputs (`format` = JSON schema).

    `transport` is for tests (e.g. `httpx.MockTransport`); production uses the default.
    """

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._transport = transport

    async def complete(
        self, system: str, user: str, schema: dict[str, Any], images: Sequence[bytes] = ()
    ) -> str:
        """Return the model's JSON reply text. Raise `LLMError` on any backend failure.

        The reply is received with `stream: true` and joined, so slow generations keep
        the connection alive through proxies with idle timeouts (e.g. Cloudflare's 100 s).
        """
        user_message: dict[str, Any] = {"role": "user", "content": user}
        if images:
            user_message["images"] = [base64.b64encode(i).decode("ascii") for i in images]
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "messages": [{"role": "system", "content": system}, user_message],
            "stream": True,
            "format": schema,
            "options": {
                "temperature": self._settings.temperature,
                "num_ctx": self._settings.num_ctx,
            },
        }
        if self._settings.think is not None:
            payload["think"] = self._settings.think
        try:
            async with (
                self._client(self._settings.timeout_seconds) as client,
                client.stream("POST", "/api/chat", json=payload) as response,
            ):
                response.raise_for_status()
                parts: list[str] = []
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    if "error" in chunk:
                        raise LLMError(str(chunk["error"]))
                    parts.append(str(chunk.get("message", {}).get("content", "")))
                return "".join(parts)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise LLMError(str(exc) or type(exc).__name__) from exc

    async def health(self) -> OllamaHealth:
        """Check `/api/tags`. Never raises: failures are reported as `ok=False`."""
        model = self._settings.model
        try:
            async with self._client(timeout=3.0) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                names = {m["name"] for m in response.json().get("models", [])}
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            return OllamaHealth(ok=False, model=model, error=str(exc) or type(exc).__name__)
        # タグ省略のモデル名は Ollama 上では ":latest" として登録される
        ready = model in names or f"{model}:latest" in names
        return OllamaHealth(ok=True, model=model, model_ready=ready)

    def _client(self, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._settings.ollama_url, timeout=timeout, transport=self._transport
        )
