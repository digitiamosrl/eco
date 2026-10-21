"""Genera il pool di personas dagli attributi del pubblico LinkedIn.

Gli attributi si campionano da data/processed/linkedin_audience.json (non si inventano);
la descrizione di ciascuna persona la scrive PERSONA_MODEL. Da backend/, con la chiave nel .env:
    python -m scripts.generate_personas --count 30 --seed 1
Poi in .env: PERSONAS_PATH=data/processed/personas.json
"""

import argparse
import asyncio
import json
from collections import Counter

import httpx

from app.config import REPO_ROOT, settings
from app.engine.llm_client import LlmError, chat_json, load_prompt
from app.models import Persona
from app.personas.audience import pool_weights
from app.personas.labels import role_of, sector_of
from app.personas.sampler import Attributes, sample_attributes

AUDIENCE_PATH = REPO_ROOT / "data" / "processed" / "linkedin_audience.json"
DEFAULT_OUT = "data/processed/personas.json"
SIZE_TEXT = {
    "micro": "micro azienda (meno di 10 persone)",
    "piccola": "piccola azienda (da 10 a 49 persone)",
    "media": "media azienda (da 50 a 249 persone)",
    "grande": "grande azienda (250 persone o più)",
}
PROFILE_SCHEMA = {
    "type": "object",
    "properties": {"profile": {"type": "string", "minLength": 20, "maxLength": 700}},
    "required": ["profile"],
    "additionalProperties": False,
}


async def _persona(
    index: int, attrs: Attributes, client: httpx.AsyncClient, semaphore: asyncio.Semaphore
) -> Persona:
    role, sector = role_of(attrs.seniority, attrs.job_function), sector_of(attrs.industry)
    prompt = load_prompt("persona_profile.md").format(
        role=role,
        sector=sector,
        company_size=SIZE_TEXT[attrs.company_size],
        region=attrs.region,
        ai_attitude=attrs.ai_attitude,
        linkedin_use=attrs.linkedin_use,
    )
    async with semaphore:
        data = await chat_json(
            client,
            model=settings.persona_model,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            schema_name="persona_profile",
            schema=PROFILE_SCHEMA,
        )
    return Persona(
        id=f"p{index + 1}",
        role=role,
        sector=sector,
        company_size=attrs.company_size,
        region=attrs.region,
        profile=data["profile"].strip(),
    )


def _compare(people: list[Attributes], weights: dict[str, dict[str, float]]) -> None:
    """Pool contro dati: quota nel pool e quota nel pubblico, per le categorie principali."""
    for dimension in ("seniority", "company_size", "region", "job_function", "industry"):
        counts = Counter(getattr(p, dimension) for p in people)
        print(f"\n{dimension} (pool / pubblico)")
        for key, weight in sorted(weights[dimension].items(), key=lambda kv: -kv[1])[:6]:
            print(
                f"  {key[:42]:42s} {100 * counts[key] / len(people):4.0f}%  /  {100 * weight:4.1f}%"
            )


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--decision-makers-only", action="store_true")
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    if not settings.openrouter_api_key or not settings.persona_model:
        print("Servono OPENROUTER_API_KEY e PERSONA_MODEL nel file .env.")
        return 1
    audience = json.loads(AUDIENCE_PATH.read_text(encoding="utf-8"))
    weights = pool_weights(audience, decision_makers_only=args.decision_makers_only)
    people = sample_attributes(weights, args.count, args.seed)
    semaphore = asyncio.Semaphore(settings.panel_concurrency)
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        try:
            personas = await asyncio.gather(
                *(_persona(i, attrs, client, semaphore) for i, attrs in enumerate(people))
            )
        except LlmError as exc:
            print(f"Generazione interrotta, nessun file scritto: {exc}")
            return 1
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = [p.model_dump() for p in personas]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Scritte {len(personas)} personas in {out}")
    _compare(people, weights)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
