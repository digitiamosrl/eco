import pytest
from fastapi.testclient import TestClient

from app.api import tests as tests_api
from app.api.tests import run_test
from app.main import app

client = TestClient(app)

POST_BODY = {
    "kind": "post",
    "variants": [
        {"label": "A", "text": "Primo testo."},
        {"label": "B", "text": "Secondo testo."},
    ],
}
PROTOTYPE_BODY = {"kind": "prototype", "flow_ids": ["onboarding"]}
PERSONAS_COUNT = 6


@pytest.fixture
def no_background(monkeypatch):
    """Il test resta in queued: il task in background non parte."""
    monkeypatch.setattr(tests_api, "run_test", lambda test_id: None)


def test_create_post_test_is_queued_then_done(validate) -> None:
    response = client.post("/tests", json=POST_BODY)
    assert response.status_code == 201
    created = response.json()
    assert created["kind"] == "post"
    assert created["status"] == "queued"
    assert created["total_count"] == PERSONAS_COUNT * 2
    assert [s["id"] for s in created["stimuli"]] == ["variante-a", "variante-b"]
    validate("test.schema.json", created)

    final = client.get(f"/tests/{created['id']}").json()
    assert final["status"] == "done"
    assert final["done_count"] == final["total_count"] == PERSONAS_COUNT * 2
    validate("test.schema.json", final)


def test_create_prototype_test_has_one_stimulus_per_screen(validate) -> None:
    response = client.post("/tests", json=PROTOTYPE_BODY)
    assert response.status_code == 201
    created = response.json()
    assert created["kind"] == "prototype"
    assert created["total_count"] == PERSONAS_COUNT * 4
    assert [s["screen_index"] for s in created["stimuli"]] == [0, 1, 2, 3]
    assert {s["flow_id"] for s in created["stimuli"]} == {"onboarding"}
    assert {s["kind"] for s in created["stimuli"]} == {"prototype_screen"}
    validate("test.schema.json", created)


def test_second_test_while_one_is_active_returns_409(no_background) -> None:
    assert client.post("/tests", json=POST_BODY).status_code == 201
    response = client.post("/tests", json=POST_BODY)
    assert response.status_code == 409
    assert response.json() == {"detail": "Un test è già in corso"}


def test_unknown_flow_returns_422() -> None:
    response = client.post("/tests", json={"kind": "prototype", "flow_ids": ["inesistente"]})
    assert response.status_code == 422
    assert response.json() == {"detail": "Flusso non trovato: inesistente"}


def test_run_test_reaches_done(no_background) -> None:
    created = client.post("/tests", json=POST_BODY).json()
    run_test(created["id"])
    final = client.get(f"/tests/{created['id']}").json()
    assert final["status"] == "done"
    assert final["done_count"] == final["total_count"]


def test_get_unknown_test_returns_404() -> None:
    response = client.get("/tests/non-esiste")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test non trovato"}


def test_list_tests_most_recent_first(validate) -> None:
    first = client.post("/tests", json=POST_BODY).json()
    second = client.post("/tests", json=PROTOTYPE_BODY).json()
    listing = client.get("/tests").json()
    assert [t["id"] for t in listing] == [second["id"], first["id"]]
    for test in listing:
        validate("test.schema.json", test)
