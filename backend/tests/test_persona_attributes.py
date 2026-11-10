import asyncio
import json

import httpx

from app.config import REPO_ROOT, settings
from app.engine import llm_client
from app.models import Persona
from app.personas.audience import HYPOTHESES
from app.personas.fallback import fallback_profile
from app.personas.labels import ai_attitude_key, linkedin_use_key
from app.personas.sampler import Attributes
from scripts.generate_personas import _persona


def test_attribute_keys_match_the_schema_enums(validate) -> None:
    ai = [ai_attitude_key(label) for label in HYPOTHESES["ai_attitude"]]
    use = [linkedin_use_key(label) for label in HYPOTHESES["linkedin_use"]]
    assert ai == ["entusiasta", "curiosa", "pragmatica", "scettica", "indifferente"]
    assert use == ["legge", "ogni_tanto", "partecipa", "solo_contatti"]


def test_generated_pool_has_both_attributes(validate) -> None:
    pool = json.loads((REPO_ROOT / "data/processed/personas.json").read_text("utf-8"))
    for item in pool:
        validate("persona.schema.json", item)
        assert item["ai_attitude"] and item["linkedin_use"]


def test_fallback_profile_uses_only_sampled_attributes() -> None:
    text = fallback_profile(
        "Titolare, Vendite", "Retail", "piccola azienda", "Lazio", "scettica", "legge in silenzio"
    )
    for part in ("Titolare, Vendite", "Retail", "Lazio", "scettica", "legge in silenzio"):
        assert part in text


def test_generation_falls_back_to_template_when_the_model_fails(monkeypatch) -> None:
    monkeypatch.setattr(settings, "persona_model", "modello/persona")

    async def broken(*args, **kwargs):
        raise llm_client.LlmError("illeggibile")

    monkeypatch.setattr("scripts.generate_personas.chat_json", broken)
    attrs = Attributes(
        seniority="Owner",
        company_size="piccola",
        job_function="Sales",
        industry="Retail",
        region="Lazio",
        ai_attitude=next(iter(HYPOTHESES["ai_attitude"])),
        linkedin_use=next(iter(HYPOTHESES["linkedin_use"])),
    )

    async def run() -> Persona:
        async with httpx.AsyncClient() as client:
            return await _persona(0, attrs, client, asyncio.Semaphore(1))

    persona = asyncio.run(run())
    assert persona.id == "p1"
    assert persona.ai_attitude == "entusiasta" and persona.linkedin_use == "legge"
    assert "Lazio" in persona.profile


def test_personas_endpoint_returns_attributes(validate) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    for persona in TestClient(app).get("/personas").json():
        validate("persona.schema.json", persona)
        assert persona["ai_attitude"] and persona["linkedin_use"]
