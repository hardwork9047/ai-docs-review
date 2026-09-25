"""HTTP routes.

This layer only translates HTTP <-> domain: parse inputs, call domain functions,
map domain errors to HTTP status codes. No business logic here.
"""

import asyncio
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.domain.service import review_document
from app.infra.converter import default_soffice, soffice_available
from app.infra.document import load_document
from app.infra.errors import DocumentError
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


@router.get("/live")
def live() -> dict[str, str]:
    """Liveness probe for the hosting platform. Never calls Ollama.

    Render のヘルスチェックはこちらを使う。/api/health は Ollama に問い合わせるので、
    Modal のような従量課金の GPU を定期的に起こしてしまう。
    """
    return {"status": "ok"}


@router.get("/health")
async def health(llm: Annotated[OllamaClient, Depends(get_llm)]) -> OllamaHealth:
    """Report whether Ollama is reachable and the configured model is pulled."""
    return await llm.health()


@router.get("/capabilities")
def capabilities(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, list[str]]:
    """Upload formats this deployment accepts: "pptx" only when LibreOffice is available."""
    soffice = settings.soffice_path or default_soffice()
    return {"formats": ["pdf", "pptx"] if soffice_available(soffice) else ["pdf"]}


@router.post("/review")
async def review(
    file: Annotated[UploadFile, File()],
    llm: Annotated[OllamaClient, Depends(get_llm)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    """Review an uploaded .pptx / .pdf page by page and stream events as NDJSON.

    413 when larger than `max_upload_mb`; 400 when the type is unsupported, the file
    cannot be read or converted, or it has no pages.
    """
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"ファイルは {settings.max_upload_mb}MB 以下にしてください")
    try:
        pages = await asyncio.to_thread(
            load_document,
            file.filename or "",
            data,
            soffice=settings.soffice_path or default_soffice(),
            image_width=settings.image_width,
        )
    except DocumentError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not pages:
        raise HTTPException(400, "ページがありません")

    async def ndjson() -> AsyncIterator[str]:
        async for event in review_document(pages, llm, max_pages=settings.max_pages):
            yield event.model_dump_json() + "\n"

    return StreamingResponse(ndjson(), media_type="application/x-ndjson")
