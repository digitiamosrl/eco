from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

POST_BODY = {
    "kind": "post",
    "variants": [
        {"label": "A", "text": "Primo testo."},
        {"label": "B", "text": "Secondo testo."},
    ],
}


def _create_done_post() -> dict:
    created = client.post("/tests", json=POST_BODY).json()
    assert client.get(f"/tests/{created['id']}").json()["status"] == "done"
    return created


def test_report_unknown_test_returns_404() -> None:
    response = client.get("/tests/non-esiste/report")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test non trovato"}


def test_report_of_unfinished_test_returns_409(no_background) -> None:
    created = client.post("/tests", json=POST_BODY).json()
    response = client.get(f"/tests/{created['id']}/report")
    assert response.status_code == 409
    assert response.json() == {"detail": "Il test non è ancora completato"}


def test_report_of_prototype_returns_501() -> None:
    created = client.post("/tests", json={"kind": "prototype", "flow_ids": ["onboarding"]}).json()
    response = client.get(f"/tests/{created['id']}/report")
    assert response.status_code == 501
    assert response.json() == {"detail": "Report del prototipo non ancora disponibile"}


def test_post_report_has_one_item_per_stimulus(validate) -> None:
    created = _create_done_post()
    response = client.get(f"/tests/{created['id']}/report")
    assert response.status_code == 200
    report = response.json()
    validate("report.schema.json", report)
    assert report["test_id"] == created["id"]
    assert [item["stimulus_id"] for item in report["items"]] == ["variante-a", "variante-b"]
    assert [item["rank"] for item in report["items"]] == [1, 2]
    for item in report["items"]:
        assert {r["stimulus_id"] for r in item["responses"]} == {item["stimulus_id"]}


def test_validation_error_returns_italian_detail_string() -> None:
    body = {"kind": "post", "variants": [{"label": "A", "text": "Solo una variante."}]}
    response = client.post("/tests", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": "Richiesta non valida: variants"}


def test_duplicate_variant_labels_return_422() -> None:
    body = {"kind": "post", "variants": [{"label": "A", "text": "x"}, {"label": "a", "text": "y"}]}
    response = client.post("/tests", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": "Richiesta non valida: variants"}


def test_duplicate_flow_ids_return_422() -> None:
    body = {"kind": "prototype", "flow_ids": ["onboarding", "onboarding"]}
    response = client.post("/tests", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": "Richiesta non valida: flow_ids"}
