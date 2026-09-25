"""Integration tests for app.api.limits — 本文を受信しきる前に上限で打ち切る。"""

from collections.abc import Iterator

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.limits import UploadLimitMiddleware

LIMIT = 1000


def _app(calls: list[int]) -> TestClient:
    app = FastAPI()

    @app.post("/upload")
    async def upload(request: Request) -> dict[str, int]:
        body = await request.body()
        calls.append(len(body))
        return {"size": len(body)}

    @app.post("/other")
    async def other(request: Request) -> dict[str, int]:
        return {"size": len(await request.body())}

    app.add_middleware(UploadLimitMiddleware, max_bytes=LIMIT, paths=("/upload",))
    return TestClient(app)


def _chunks(total: int, size: int = 100) -> Iterator[bytes]:
    for _ in range(total // size):
        yield b"x" * size


def test_body_within_the_limit_passes_through() -> None:
    calls: list[int] = []
    response = _app(calls).post("/upload", content=b"x" * LIMIT)
    assert response.status_code == 200
    assert calls == [LIMIT]


def test_declared_length_over_the_limit_is_rejected_before_the_handler_runs() -> None:
    calls: list[int] = []
    response = _app(calls).post("/upload", content=b"x" * (LIMIT + 1))
    assert response.status_code == 413
    assert "MB" in response.json()["detail"] or "上限" in response.json()["detail"]
    assert calls == []


def test_chunked_body_is_cut_off_once_it_exceeds_the_limit() -> None:
    calls: list[int] = []
    # イテレータで渡すと Content-Length なし(chunked)で送られる
    response = _app(calls).post("/upload", content=_chunks(LIMIT * 10))
    assert response.status_code == 413
    assert calls == []


def test_other_paths_are_not_limited() -> None:
    response = _app([]).post("/other", content=b"x" * (LIMIT * 3))
    assert response.status_code == 200
