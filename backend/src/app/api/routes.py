"""HTTP routes.

This layer only translates HTTP <-> domain: parse inputs, call domain functions,
map domain errors to HTTP status codes. No business logic here.
"""

from fastapi import APIRouter

from app.infra.ollama import OllamaClient

router = APIRouter(prefix="/api")


def get_llm() -> OllamaClient:
    """Dependency: the Ollama client built from settings (tests override this)."""
    raise NotImplementedError
