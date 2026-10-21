from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    persona_model: str = ""
    report_model: str = ""
    panel_concurrency: int = 5
    database_path: str = "eco.sqlite"
    # Durata simulata di un test completo (fixture, nessuna chiamata reale).
    fixture_delay_seconds: float = 3.0


settings = Settings()
