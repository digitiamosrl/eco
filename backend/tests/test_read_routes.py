from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_personas_returns_valid_list(validate) -> None:
    response = client.get("/personas")
    assert response.status_code == 200
    personas = response.json()
    assert len(personas) >= 6
    for persona in personas:
        validate("persona.schema.json", persona)


def test_get_flows_returns_valid_list(validate) -> None:
    response = client.get("/flows")
    assert response.status_code == 200
    flows = response.json()
    assert {flow["id"] for flow in flows} >= {"onboarding", "preventivo"}
    for flow in flows:
        validate("flow.schema.json", flow)
