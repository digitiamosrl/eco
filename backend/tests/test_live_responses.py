from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.models import Response

client = TestClient(app)

POST_BODY = {"kind": "post", "variants": [{"label": "A", "text": "Primo."}]}


def test_responses_of_running_test_are_the_ones_saved_so_far(no_background, validate) -> None:
    created = client.post("/tests", json=POST_BODY).json()
    assert client.get(f"/tests/{created['id']}/responses").json() == []

    saved = Response(
        persona_id="p1",
        stimulus_id="variante-a",
        thought="Pensato.",
        said="Detto.",
        score=4,
        objections=[],
        action="react",
    )
    store.add_response(created["id"], saved)
    [response] = client.get(f"/tests/{created['id']}/responses").json()
    validate("response.schema.json", response)
    assert response["score"] == 4
    assert "reaction" not in response  # i campi assenti non diventano null


def test_responses_of_unknown_test_return_404() -> None:
    response = client.get("/tests/non-esiste/responses")
    assert (response.status_code, response.json()) == (404, {"detail": "Test non trovato"})


def test_responses_come_back_in_arrival_order(no_background) -> None:
    created = client.post("/tests", json=POST_BODY).json()
    for persona in ("p3", "p1", "p2"):  # la chiave primaria li ordinerebbe p1, p2, p3
        store.add_response(
            created["id"],
            Response(
                persona_id=persona,
                stimulus_id="variante-a",
                thought="t",
                said="s",
                score=3,
                objections=[],
            ),
        )
    responses = client.get(f"/tests/{created['id']}/responses").json()
    assert [r["persona_id"] for r in responses] == ["p3", "p1", "p2"]
