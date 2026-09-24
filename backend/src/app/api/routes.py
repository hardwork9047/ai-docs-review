"""HTTP routes.

This layer only translates HTTP <-> domain: parse inputs, call domain functions,
map domain errors to HTTP status codes. No business logic here.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.infra.ollama import OllamaClient, OllamaHealth
from app.infra.settings import Settings

router = APIRouter(prefix="/api")


@lru_cache
def get_settings() -> Settings:
    """Dependency: settings read once from the environment."""
    return Settings()


def get_llm(settings: Annotated[Settings, Depends(get_settings)]) -> OllamaClient:
    """Dependency: the Ollama client built from settings (tests override this)."""
    return OllamaClient(settings)


@router.get("/health")
async def health(llm: Annotated[OllamaClient, Depends(get_llm)]) -> OllamaHealth:
    """Report whether Ollama is reachable and the configured model is pulled."""
    return await llm.health()
