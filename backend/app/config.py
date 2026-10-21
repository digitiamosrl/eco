from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Il server genera il nome dei file; questo è solo il limite per immagine caricata.
MAX_IMAGE_BYTES = 5 * 1024 * 1024
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    persona_model: str = ""
    report_model: str = ""
    panel_concurrency: int = 5
    database_path: str = "eco.sqlite"
    # Durata simulata di un test completo (fixture, nessuna chiamata reale).
    fixture_delay_seconds: float = 3.0
    upload_dir: Path = REPO_ROOT / "data" / "uploads"
    # fake: risponditore deterministico senza rete. llm: provider AI (non ancora configurato).
    responder: Literal["fake", "llm"] = "fake"


settings = Settings()
