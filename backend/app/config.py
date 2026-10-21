from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Il server genera il nome dei file; questo è solo il limite per immagine caricata.
MAX_IMAGE_BYTES = 5 * 1024 * 1024
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Id modello di OpenRouter, da impostare nel .env (nessun default).
    persona_model: str = ""
    report_model: str = ""
    llm_timeout_seconds: float = 60
    panel_concurrency: int = 5
    database_path: str = "eco.sqlite"
    # Durata simulata di un test completo (fixture, nessuna chiamata reale).
    fixture_delay_seconds: float = 3.0
    upload_dir: Path = REPO_ROOT / "data" / "uploads"
    # fake: risponditore deterministico senza rete. llm: modelli via OpenRouter.
    responder: Literal["fake", "llm"] = "fake"
    summarizer: Literal["fake", "llm"] = "fake"
    # Pool di personas generato (percorso dalla radice del repo). Vuoto: le fixture.
    personas_path: str = ""


settings = Settings()


def validate_startup() -> None:
    """Errore chiaro all'avvio, solo per le configurazioni che richiedono un modello."""
    if settings.responder == "llm" and not settings.persona_model:
        raise RuntimeError("RESPONDER=llm richiede PERSONA_MODEL nel file .env")
    if settings.summarizer == "llm" and not settings.report_model:
        raise RuntimeError("SUMMARIZER=llm richiede REPORT_MODEL nel file .env")
    uses_llm = "llm" in (settings.responder, settings.summarizer)
    if uses_llm and not settings.openrouter_api_key:
        raise RuntimeError("Il provider AI richiede OPENROUTER_API_KEY nel file .env")
