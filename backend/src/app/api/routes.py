"""HTTP routes.

This layer only translates HTTP <-> domain: parse inputs, call domain functions,
map domain errors to HTTP status codes. No business logic here.
"""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.domain.service import review_deck
from app.infra.ollama import OllamaClient, OllamaHealth
from app.infra.pptx_reader import DeckReadError, read_slides
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


@router.post("/review")
async def review(
    file: Annotated[UploadFile, File()],
    llm: Annotated[OllamaClient, Depends(get_llm)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    """Review an uploaded .pptx and stream the events as NDJSON (one JSON per line).

    400 when the file is not a .pptx, cannot be parsed, or has no slides.
    """
    if not (file.filename or "").lower().endswith(".pptx"):
        raise HTTPException(400, ".pptx ファイルをアップロードしてください")
    try:
        slides = read_slides(await file.read())
    except DeckReadError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not slides:
        raise HTTPException(400, "スライドがありません")

    async def ndjson() -> AsyncIterator[str]:
        async for event in review_deck(slides, llm, max_slides=settings.max_slides):
            yield event.model_dump_json() + "\n"

    return StreamingResponse(ndjson(), media_type="application/x-ndjson")
