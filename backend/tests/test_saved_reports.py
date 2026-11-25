from fastapi.testclient import TestClient

from app.api import reports
from app.main import app
from app.models import Fidelity

client = TestClient(app)
BODY = {
    "kind": "post",
    "variants": [{"label": "A", "text": "Uno."}, {"label": "B", "text": "Due."}],
}


async def _must_not_build(*args, **kwargs):
    raise AssertionError("il report salvato non va rigenerato")


def test_report_is_saved_and_read_back_after_a_restart(monkeypatch) -> None:
    created = client.post("/tests", json=BODY).json()
    first = client.get(f"/tests/{created['id']}/report").json()
    reports._REPORTS.clear()  # come dopo un riavvio
    monkeypatch.setattr(reports, "build_report", _must_not_build)
    assert client.get(f"/tests/{created['id']}/report").json() == first


def test_fidelity_is_added_when_reading_a_saved_report(monkeypatch) -> None:
    created = client.post("/tests", json=BODY).json()
    monkeypatch.setattr(reports, "load_fidelity", lambda: None)
    assert "fidelity" not in client.get(f"/tests/{created['id']}/report").json()
    reports._REPORTS.clear()
    monkeypatch.setattr(reports, "load_fidelity", lambda: Fidelity(score=0.4, basis="57 post"))
    report = client.get(f"/tests/{created['id']}/report").json()
    assert report["fidelity"] == {"score": 0.4, "basis": "57 post"}
