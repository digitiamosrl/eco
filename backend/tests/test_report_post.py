from fastapi.testclient import TestClient

from app import store
from app.main import app

client = TestClient(app)

POST_BODY = {
    "kind": "post",
    "variants": [
        {"label": "A", "text": "Primo testo."},
        {"label": "B", "text": "Secondo testo."},
        {"label": "C", "text": "Terzo testo."},
    ],
}


def _done_post() -> dict:
    created = client.post("/tests", json=POST_BODY).json()
    assert client.get(f"/tests/{created['id']}").json()["status"] == "done"
    return created


def test_report_is_built_from_saved_responses(validate) -> None:
    created = _done_post()
    report = client.get(f"/tests/{created['id']}/report").json()
    validate("report.schema.json", report)
    assert report["test_id"] == created["id"]
    assert report["simulated"] is True
    assert sorted(item["rank"] for item in report["items"]) == [1, 2, 3]
    assert {item["stimulus_id"] for item in report["items"]} == {
        "variante-a",
        "variante-b",
        "variante-c",
    }


def test_report_means_match_stored_responses() -> None:
    created = _done_post()
    report = client.get(f"/tests/{created['id']}/report").json()
    stored = store.list_responses(created["id"])
    for item in report["items"]:
        scores = [r.score for r in stored if r.stimulus_id == item["stimulus_id"]]
        assert item["mean_score"] == round(sum(scores) / len(scores), 2)
        assert len(item["responses"]) == len(scores)
        assert all(r["stimulus_id"] == item["stimulus_id"] for r in item["responses"])


def test_report_items_are_ordered_by_rank() -> None:
    created = _done_post()
    items = client.get(f"/tests/{created['id']}/report").json()["items"]
    assert [item["rank"] for item in items] == [1, 2, 3]
    means = [item["mean_score"] for item in items]
    assert means == sorted(means, reverse=True)


def test_post_flow_end_to_end_with_multipart_and_image(validate) -> None:
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    fields = {
        "kind": (None, "post"),
        "variants[0][label]": (None, "A"),
        "variants[0][text]": (None, "Primo"),
        "variants[1][label]": (None, "B"),
        "variants[1][text]": (None, "Secondo"),
    }
    created = client.post(
        "/tests",
        files={**fields, "variants[0][image]": ("foto.png", png, "image/png")},
    ).json()
    assert client.get(f"/tests/{created['id']}").json()["status"] == "done"
    report = client.get(f"/tests/{created['id']}/report").json()
    validate("report.schema.json", report)
    image_url = created["stimuli"][0]["image_url"]
    assert client.get(image_url).content == png


def test_report_returns_503_when_summarizer_fails(monkeypatch) -> None:
    from app.api import reports as reports_api
    from app.engine.llm_client import LlmError

    class FailingSummarizer:
        async def said_summary(self, stats):
            raise LlmError("Il servizio di analisi non è disponibile in questo momento.")

    created = _done_post()
    monkeypatch.setattr(reports_api, "build_summarizer", lambda: FailingSummarizer())
    response = client.get(f"/tests/{created['id']}/report")
    assert response.status_code == 503
    assert "non è disponibile" in response.json()["detail"]
