import json
from collections.abc import Sequence
from typing import Any, Protocol

import httpx
from jsonschema import Draft202012Validator

from app.config import settings
from app.engine.llm_client import LlmError, chat_json, load_prompt, shared_client
from app.models import Stimulus
from app.report.aggregate import StimulusStats


class Summarizer(Protocol):
    async def said_summary(self, stats: StimulusStats) -> str: ...

    async def thought_summary(self, stats: StimulusStats) -> str: ...

    async def summary(self, ranking: Sequence[StimulusStats]) -> str: ...


class FakeSummarizer:
    """Testo semplice composto dai numeri, nessun modello."""

    async def said_summary(self, stats: StimulusStats) -> str:
        base = f"Media {stats.mean_score:.2f} su 5 da {len(stats.responses)} risposte."
        if not stats.objections:
            return f"{base} Nessuna obiezione ricorrente."
        return f"{base} Obiezione più frequente: {stats.objections[0]}"

    async def thought_summary(self, stats: StimulusStats) -> str:
        positive = sum(1 for r in stats.responses if r.score >= 4)
        return f"{positive} risposte su {len(stats.responses)} con punteggio 4 o 5."

    async def summary(self, ranking: Sequence[StimulusStats]) -> str:
        if not ranking:
            return "Nessuna risposta registrata."
        top = ranking[0]
        if top.abandon_count is not None:
            return (
                f"Punto più critico la {label(top.stimulus)}, con {top.abandon_count} abbandoni "
                f"su {len(top.responses)} risposte. Risultati simulati."
            )
        return (
            f"In testa la {label(top.stimulus)} con media {top.mean_score:.2f} su {len(ranking)} "
            "varianti. Risultati simulati."
        )


_VARIANT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["said_summary", "thought_summary"],
    "properties": {
        "said_summary": {"type": "string", "minLength": 1},
        "thought_summary": {"type": "string", "minLength": 1},
    },
}
_OVERVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary"],
    "properties": {"summary": {"type": "string", "minLength": 1}},
}
_VARIANT_VALIDATOR = Draft202012Validator(_VARIANT_SCHEMA)
_OVERVIEW_VALIDATOR = Draft202012Validator(_OVERVIEW_SCHEMA)
_NO_RESPONSES = "Nessuna risposta registrata."
_INVALID_SUMMARY = "Il riepilogo generato non è valido."


def label(stimulus: Stimulus) -> str:
    """Come il report nomina uno stimolo: la variante di un post o la schermata di un prototipo."""
    if stimulus.kind == "prototype_screen":
        return f"schermata {(stimulus.screen_index or 0) + 1} «{stimulus.page_structure or ''}»"
    return f"variante {stimulus.variant_label or stimulus.id}"


_RESPONSE_FIELDS = {"thought", "said", "score", "objections", "misunderstood", "would_abandon"}


def _responses_json(stats: StimulusStats) -> str:
    rows = [r.model_dump(include=_RESPONSE_FIELDS, exclude_none=True) for r in stats.responses]
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _ranking_text(ranking: Sequence[StimulusStats]) -> str:
    lines = []
    for stats in ranking:
        objections = ", ".join(stats.objections) or "nessuna"
        abandons = "" if stats.abandon_count is None else f", abbandoni: {stats.abandon_count}"
        lines.append(
            f"- {stats.rank}. {label(stats.stimulus)}: media {stats.mean_score:.2f} su 5 "
            f"({len(stats.responses)} risposte{abandons}), obiezioni: {objections}"
        )
    return "\n".join(lines)


class LlmSummarizer:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        # Said e thought di una variante vengono dalla stessa chiamata: il dict evita la seconda.
        self._variants: dict[str, dict[str, str]] = {}

    async def said_summary(self, stats: StimulusStats) -> str:
        return (await self._variant(stats))["said_summary"]

    async def thought_summary(self, stats: StimulusStats) -> str:
        return (await self._variant(stats))["thought_summary"]

    async def summary(self, ranking: Sequence[StimulusStats]) -> str:
        if not ranking:
            return _NO_RESPONSES
        prompt = load_prompt("report_overview.md").format(ranking=_ranking_text(ranking))
        data = await self._ask(prompt, _OVERVIEW_SCHEMA, "report_overview")
        if not _OVERVIEW_VALIDATOR.is_valid(data):
            raise LlmError(_INVALID_SUMMARY)
        return data["summary"]

    async def _variant(self, stats: StimulusStats) -> dict[str, str]:
        key = stats.stimulus.id
        if key not in self._variants:
            prompt = load_prompt("report_summary.md").format(
                label=label(stats.stimulus), responses=_responses_json(stats)
            )
            data = await self._ask(prompt, _VARIANT_SCHEMA, "report_summary")
            if not _VARIANT_VALIDATOR.is_valid(data):
                raise LlmError(_INVALID_SUMMARY)
            self._variants[key] = data
        return self._variants[key]

    async def _ask(self, prompt: str, schema: dict, schema_name: str) -> dict[str, Any]:
        return await chat_json(
            self._client or shared_client(),
            model=settings.report_model,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            schema_name=schema_name,
            schema=schema,
        )


def build_summarizer() -> Summarizer:
    return LlmSummarizer() if settings.summarizer == "llm" else FakeSummarizer()
