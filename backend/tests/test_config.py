import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_llm_responder_without_persona_model_fails_at_startup(monkeypatch) -> None:
    monkeypatch.setattr(settings, "responder", "llm")
    monkeypatch.setattr(settings, "persona_model", "")
    with pytest.raises(RuntimeError, match="RESPONDER=llm richiede PERSONA_MODEL"):
        with TestClient(app):
            pass


def test_llm_summarizer_without_report_model_fails_at_startup(monkeypatch) -> None:
    monkeypatch.setattr(settings, "summarizer", "llm")
    monkeypatch.setattr(settings, "report_model", "")
    with pytest.raises(RuntimeError, match="SUMMARIZER=llm richiede REPORT_MODEL"):
        with TestClient(app):
            pass


def test_default_configuration_starts() -> None:
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
