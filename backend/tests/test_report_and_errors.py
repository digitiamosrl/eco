from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.models import Prototype, PrototypeScreen, PrototypeStart

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


def _create_done_prototype() -> dict:
    screens = [
        PrototypeScreen(index=i, name=f"Passo {i}", image_url="/files/x.png") for i in range(3)
    ]
    store.add_prototype(
        Prototype(
            id="proto",
            source="artifact",
            name="Prova",
            imported_at="2026-11-17T10:00:00+00:00",
            starts=[PrototypeStart(id="s1", name="Home", screens=screens)],
        )
    )
    body = {
        "kind": "prototype",
        "prototype_id": "proto",
        "paths": [{"start_id": "s1", "screen_indexes": [0, 1, 2]}],
        "task": "Provare il prodotto",
    }
    created = client.post("/tests", json=body).json()
    assert client.get(f"/tests/{created['id']}").json()["status"] == "done"
    return created


def test_prototype_report_has_abandons_per_screen(validate) -> None:
    created = _create_done_prototype()
    response = client.get(f"/tests/{created['id']}/report")
    assert response.status_code == 200
    report = response.json()
    validate("report.schema.json", report)
    assert report["simulated"] is True
    assert "fidelity" not in report  # la calibrazione vale per i post, non per i prototipi
    assert {item["stimulus_id"] for item in report["items"]} == {
        s["id"] for s in created["stimuli"]
    }
    assert all("abandon_count" in item and "misunderstood" in item for item in report["items"])
    counts = [item["abandon_count"] for item in report["items"]]
    assert counts == sorted(counts, reverse=True)


def test_post_report_has_one_item_per_stimulus(validate) -> None:
    created = _create_done_post()
    response = client.get(f"/tests/{created['id']}/report")
    assert response.status_code == 200
    report = response.json()
    validate("report.schema.json", report)
    assert report["test_id"] == created["id"]
    assert sorted(item["stimulus_id"] for item in report["items"]) == ["variante-a", "variante-b"]
    assert sorted(item["rank"] for item in report["items"]) == [1, 2]
    for item in report["items"]:
        assert {r["stimulus_id"] for r in item["responses"]} == {item["stimulus_id"]}


def test_validation_error_returns_italian_detail_string() -> None:
    body = {"kind": "post", "variants": []}
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


def test_prototype_report_is_prepared_when_the_test_ends(monkeypatch) -> None:
    from app.api import reports as reports_api
    from app.report.summarize import FakeSummarizer

    calls: list[str] = []

    class Counting(FakeSummarizer):
        async def summary(self, ranking) -> str:
            calls.append("summary")
            return await super().summary(ranking)

    monkeypatch.setattr(reports_api, "build_summarizer", Counting)
    created = _create_done_prototype()
    assert calls == ["summary"]  # pronto prima che qualcuno apra il report
    assert client.get(f"/tests/{created['id']}/report").status_code == 200
    assert calls == ["summary"]
