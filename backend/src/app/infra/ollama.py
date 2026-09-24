"""Ollama adapter implementing the domain `ReviewLLM` port over its HTTP API."""

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

    async def complete(self, system: str, user: str, schema: dict[str, Any]) -> str:
        """Return the model's JSON reply text. Raise `LLMError` on any backend failure."""
        raise NotImplementedError

    async def health(self) -> OllamaHealth:
        """Check `/api/tags`. Never raises: failures are reported as `ok=False`."""
        raise NotImplementedError
