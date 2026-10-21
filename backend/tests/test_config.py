import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
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


def test_llm_responder_without_openrouter_key_fails_at_startup(monkeypatch) -> None:
    monkeypatch.setattr(settings, "responder", "llm")
    monkeypatch.setattr(settings, "persona_model", "modello/persona")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    with pytest.raises(RuntimeError, match="richiede OPENROUTER_API_KEY"):
        with TestClient(app):
            pass


def test_llm_summarizer_without_openrouter_key_fails_at_startup(monkeypatch) -> None:
    monkeypatch.setattr(settings, "summarizer", "llm")
    monkeypatch.setattr(settings, "report_model", "modello/report")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    with pytest.raises(RuntimeError, match="richiede OPENROUTER_API_KEY"):
        with TestClient(app):
            pass


def test_openrouter_defaults() -> None:
    defaults = Settings(_env_file=None)
    assert defaults.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert defaults.llm_timeout_seconds == 60
