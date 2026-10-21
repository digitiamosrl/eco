from collections.abc import Sequence
from typing import Protocol

from app.config import settings
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
        label = top.stimulus.variant_label or top.stimulus.id
        return (
            f"In testa la variante {label} con media {top.mean_score:.2f} su {len(ranking)} "
            "varianti. Risultati simulati."
        )


class LlmSummarizer:
    # shortcut: stub senza provider, sostituire con il provider AI (parte AI, dopo il backend)
    async def said_summary(self, stats: StimulusStats) -> str:
        raise NotImplementedError("Provider AI non ancora configurato")

    async def thought_summary(self, stats: StimulusStats) -> str:
        raise NotImplementedError("Provider AI non ancora configurato")

    async def summary(self, ranking: Sequence[StimulusStats]) -> str:
        raise NotImplementedError("Provider AI non ancora configurato")


def build_summarizer() -> Summarizer:
    return LlmSummarizer() if settings.summarizer == "llm" else FakeSummarizer()
