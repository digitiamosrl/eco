"""Confronto tra modelli e test di stabilità. Verifica manuale: non gira in pytest.

Ogni modello risponde, per più run, con tutte le personas a 4 post di calibrazione scritti
apposta (forte, buono, debole, scadente). Uso, da backend/ con OPENROUTER_API_KEY nel .env:
    python -m scripts.compare_models --models id1,id2 --repeats 3
"""

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field
from statistics import mean, quantiles
from typing import Any

import httpx

from app.api.personas import PERSONAS
from app.config import settings
from app.engine.responder import LlmResponder
from app.engine.runner import _is_valid  # stessa validazione del runner
from app.models import Response, Stimulus
from scripts import compare_metrics as metrics

DEFAULT_MODELS = (
    "minimax/minimax-m3.1-flash:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "dots-studio/dots-3-note-preview:free",
)
# Ordine atteso dal migliore al peggiore: l'unica verità di riferimento che abbiamo per ora.
POSTS = (
    Stimulus(
        id="calibrazione-forte",
        kind="post",
        text="Una PMI di Brescia (22 dipendenti) ha ridotto da 3 giorni a 4 ore il tempo per "
        "fare un preventivo, collegando gestionale e magazzino. Abbiamo misurato il risultato "
        "per 6 mesi: -35% di errori e nessuno straordinario a fine mese. Ecco cosa abbiamo "
        "cambiato, passo per passo.",
    ),
    Stimulus(
        id="calibrazione-buono",
        kind="post",
        text="Come una piccola azienda manifatturiera ha semplificato la gestione degli ordini: "
        "abbiamo eliminato i fogli Excel duplicati e oggi il team lavora su un unico strumento. "
        "Il racconto del progetto, con i dubbi iniziali e cosa rifaremmo.",
    ),
    Stimulus(
        id="calibrazione-debole",
        kind="post",
        text="La digitalizzazione è fondamentale per le imprese di oggi. Innovare significa "
        "restare competitivi in un mercato in continua evoluzione. Siamo al fianco delle "
        "aziende nel loro percorso di trasformazione digitale.",
    ),
    Stimulus(
        id="calibrazione-scadente",
        kind="post",
        text="SCOPRI LA RIVOLUZIONE DIGITALE!!! Offerta imperdibile solo per oggi: contattaci "
        "SUBITO e trasforma la tua azienda con soluzioni innovative a 360°! Non perdere "
        "questa occasione unica!",
    ),
)
EXPECTED_ORDER = [post.id for post in POSTS]


@dataclass
class ModelResult:
    runs: list[list[Response]]
    first_try: int = 0
    retried: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0


async def _ask(
    responder: LlmResponder, persona: Any, post: Stimulus, semaphore: asyncio.Semaphore
) -> tuple[Response | None, int | None, float | None]:
    """Due tentativi come il runner: eccezione o risposta fuori schema contano come fallimento."""
    async with semaphore:
        for attempt in (1, 2):
            started = time.perf_counter()
            try:
                response = await responder.respond(persona, post)
            except Exception:  # qui si conta il fallimento, non si nasconde
                continue
            if _is_valid(response):
                return response, attempt, time.perf_counter() - started
    return None, None, None


async def _run_model(model: str, repeats: int, concurrency: int) -> ModelResult:
    result = ModelResult(runs=[[] for _ in range(repeats)])

    async def record_usage(response: httpx.Response) -> None:
        await response.aread()
        try:
            usage = response.json().get("usage") or {}
        except (ValueError, AttributeError):
            return
        result.tokens_in += usage.get("prompt_tokens", 0)
        result.tokens_out += usage.get("completion_tokens", 0)

    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(
        timeout=settings.llm_timeout_seconds, event_hooks={"response": [record_usage]}
    ) as client:
        responder = LlmResponder(client, model=model)
        jobs = [
            (run, _ask(responder, persona, post, semaphore))
            for run in range(repeats)
            for persona in PERSONAS
            for post in POSTS
        ]
        outcomes = await asyncio.gather(*(job for _, job in jobs))
    for (run, _), (response, attempt, latency) in zip(jobs, outcomes, strict=True):
        if response is None:
            result.failed += 1
            continue
        result.runs[run].append(response)
        result.first_try += attempt == 1
        result.retried += attempt == 2
        result.latencies.append(latency)
    return result


def _fmt(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def _row(model: str, r: ModelResult) -> list[str]:
    total = r.first_try + r.retried + r.failed
    complete = [run for run in r.runs if run]
    p95 = quantiles(r.latencies, n=20)[-1] if len(r.latencies) >= 2 else None
    return [
        model.split("/")[-1][:28],
        f"{100 * r.first_try / total:.0f}%",
        f"{r.retried}/{r.failed}",
        _fmt(mean(r.latencies) if r.latencies else None, 1),
        _fmt(p95, 1),
        f"{r.tokens_in // 1000}k/{r.tokens_out // 1000}k",
        _fmt(metrics.mean_pairwise_tau(complete)),
        _fmt(metrics.top1_agreement(complete)),
        _fmt(metrics.post_std(complete)),
        _fmt(metrics.persona_consistency(complete)),
        _fmt(metrics.spread(complete)),
        _fmt(metrics.expected_tau(complete, EXPECTED_ORDER)),
        _fmt(metrics.persona_spread(complete)),
        _fmt(metrics.distinct_objection_ratio(complete)),
    ]


HEADER = [
    "modello",
    "ok 1o",
    "retry/fail",
    "lat s",
    "p95 s",
    "token in/out",
    "tau run",
    "top1",
    "std post",
    "std pers.",
    "scarto",
    "tau atteso",
    "var pers.",
    "obiez. div.",
]


def _print_table(rows: list[list[str]]) -> None:
    widths = [max(len(line[i]) for line in [HEADER, *rows]) for i in range(len(HEADER))]
    for line in [HEADER, *rows]:
        print("  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)))


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=settings.panel_concurrency)
    parser.add_argument("--out", help="File JSON opzionale con le risposte; di default non salva")
    args = parser.parse_args()
    if not settings.openrouter_api_key:
        print("Serve OPENROUTER_API_KEY nel file .env.")
        return 1
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    results = await asyncio.gather(*(_run_model(m, args.repeats, args.concurrency) for m in models))
    _print_table([_row(m, r) for m, r in zip(models, results, strict=True)])
    if args.out:
        dump = {
            m: [[x.model_dump() for x in run] for run in r.runs]
            for m, r in zip(models, results, strict=True)
        }
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(dump, fh, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
