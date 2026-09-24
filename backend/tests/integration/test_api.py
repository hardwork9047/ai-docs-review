"""Integration tests: hit the API boundary with a real test client."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_items_returns_first_page_by_default() -> None:
    response = client.get("/items")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 10
    assert body["page"] == 1
    assert body["total_pages"] == 3


def test_items_out_of_range_page_is_422() -> None:
    response = client.get("/items", params={"page": 99})
    assert response.status_code == 422
