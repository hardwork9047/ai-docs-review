"""Integration tests: hit the API boundary with a real test client and a fake LLM."""

import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_llm, get_settings
from app.domain.service import LLMError
from app.infra.ollama import OllamaHealth
from app.infra.settings import Settings
from app.main import create_app
from tests.pdf_factory import make_pdf

REPLY = json.dumps(
    {
        "content_score": 90,
        "figure_score": None,
        "chart_score": None,
        "good_points": ["g"],
        "bad_points": ["b"],
        "fixes": ["f"],
    }
)
PDF = make_pdf([[("Approval", 32), ("Body text", 18)], [("Next", 24)]])


class FakeLLM:
    """Stands in for OllamaClient: canned chat reply (or error) and canned health."""

    def __init__(self) -> None:
        self.error: Exception | None = None

    async def complete(
        self, system: str, user: str, schema: dict[str, Any], images: Sequence[bytes] = ()
    ) -> str:
        if self.error:
            raise self.error
        return REPLY

    async def health(self) -> OllamaHealth:
        return OllamaHealth(ok=True, model="fake:1", model_ready=True)


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def client(llm: FakeLLM) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_llm] = lambda: llm
    app.dependency_overrides[get_settings] = lambda: Settings(max_upload_mb=1)
    with TestClient(app) as c:
        yield c


def _post(client: TestClient, data: bytes, name: str = "deck.pdf") -> Any:
    return client.post("/api/review", files={"file": (name, data, "application/octet-stream")})


def _lines(response: Any) -> list[dict[str, Any]]:
    return [json.loads(line) for line in response.text.splitlines()]


def test_health_reports_ollama_status(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "model": "fake:1", "model_ready": True, "error": None}


def test_review_streams_meta_pages_done_as_ndjson(client: TestClient) -> None:
    response = _post(client, PDF)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = _lines(response)
    assert [e["type"] for e in events] == ["meta", "page", "page", "done"]
    meta, first, _, done = events
    assert meta["page_count"] == 2
    assert "system_prompt" not in meta["reviewer"]
    assert first["result"]["title"] == "Approval"
    assert first["result"]["thumbnail"]
    assert done["summary"]["verdict"]["passed"] is True


def test_llm_failure_is_streamed_per_page(client: TestClient, llm: FakeLLM) -> None:
    llm.error = LLMError("down")
    events = _lines(_post(client, PDF))
    assert [e["type"] for e in events] == ["meta", "page_error", "page_error", "done"]


@pytest.mark.parametrize("name", ["deck.ppt", "deck.docx", "deck.png"])
def test_unsupported_file_type_is_400(client: TestClient, name: str) -> None:
    response = _post(client, PDF, name=name)
    assert response.status_code == 400
    assert "pptx" in response.json()["detail"]


def test_corrupt_pdf_is_400(client: TestClient) -> None:
    assert _post(client, b"%PDF-1.4 broken").status_code == 400


def test_upload_over_the_size_limit_is_413(client: TestClient) -> None:
    assert _post(client, b"%PDF" + b"0" * (1024 * 1024)).status_code == 413


def test_built_frontend_is_served_when_static_dir_is_set(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<title>app</title>")
    with TestClient(create_app(static_dir=str(tmp_path))) as c:
        assert "<title>app</title>" in c.get("/").text
        assert c.get("/api/health").status_code == 200  # API は静的配信より優先


def test_app_rejects_oversized_uploads_before_parsing(llm: FakeLLM) -> None:
    app = create_app(max_upload_mb=1)
    app.dependency_overrides[get_llm] = lambda: llm
    with TestClient(app) as c:
        response = _post(c, b"%PDF" + b"0" * (2 * 1024 * 1024))
    assert response.status_code == 413
