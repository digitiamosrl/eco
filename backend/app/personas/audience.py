"""Dal export Analytics di LinkedIn ai pesi di campionamento delle personas.

I dati sono distribuzioni marginali (una per attributo): non esiste la distribuzione congiunta.
"""

from collections import defaultdict
from collections.abc import Mapping

DECISION_SENIORITIES = frozenset({"Manager", "Director", "VP", "CXO", "Owner", "Partner"})

# Soglie europee (micro < 10, piccola < 50, media < 250). 201-500 sta a cavallo di 250:
# la maggior parte del bucket è sopra, quindi finisce in "grande".
_SIZE_BUCKETS = {
    "1": "micro",
    "2-10": "micro",
    "11-50": "piccola",
    "51-200": "media",
    "201-500": "grande",
    "501-1000": "grande",
    "1001-5000": "grande",
    "5001-10000": "grande",
    "10001+": "grande",
}

_REGION_OF_CITY = {
    **dict.fromkeys(
        [
            "Milan",
            "Varese",
            "Bergamo",
            "Brescia",
            "Como",
            "Lecco",
            "Pavia",
            "Cremona",
            "Sondrio",
            "Busto Arsizio",
        ],
        "Lombardia",
    ),
    **dict.fromkeys(["Turin", "Asti", "Biella", "Novara"], "Piemonte"),
    **dict.fromkeys(
        [
            "Bologna",
            "Ferrara",
            "Forli",
            "Modena",
            "Parma",
            "Piacenza",
            "Ravenna",
            "Reggio Emilia",
            "Rimini",
        ],
        "Emilia-Romagna",
    ),
    **dict.fromkeys(["Florence", "Pisa", "Prato", "Lucca"], "Toscana"),
    **dict.fromkeys(["Padova (Padua)", "Treviso", "Venice", "Verona", "Vicenza"], "Veneto"),
    **dict.fromkeys(["Rome", "Latina"], "Lazio"),
    **dict.fromkeys(["Naples", "Caserta", "Salerno"], "Campania"),
    **dict.fromkeys(["Bari", "Brindisi", "Foggia", "Lecce", "Taranto"], "Puglia"),
    **dict.fromkeys(["Catania", "Messina", "Palermo", "Modica", "Ragusa"], "Sicilia"),
    **dict.fromkeys(["Ancona", "Apecchio", "Pesaro", "Recanati"], "Marche"),
    **dict.fromkeys(["Genoa", "La Spezia"], "Liguria"),
    **dict.fromkeys(["Pordenone", "Trieste", "Udine"], "Friuli-Venezia Giulia"),
    **dict.fromkeys(["Bolzano", "Trento"], "Trentino-Alto Adige"),
    **dict.fromkeys(["Cagliari", "Sassari"], "Sardegna"),
    **dict.fromkeys(["Matera", "Potenza"], "Basilicata"),
    **dict.fromkeys(["Pescara", "L’Aquila"], "Abruzzo"),
    "Perugia": "Umbria",
    "Cosenza": "Calabria",
}


def company_size_of(label: str) -> str:
    return _SIZE_BUCKETS[label]


def _city(location: str) -> str:
    name = location.removesuffix(", Italy").replace(", Italy Metropolitan Area", "")
    return name.removeprefix("Greater ").removesuffix(" Metropolitan Area")


def region_of(location: str) -> str | None:
    """Regione italiana di un'area di LinkedIn; None per le località estere."""
    if not location.endswith("Italy"):
        return None
    return _REGION_OF_CITY[_city(location)]


def blend(*distributions: Mapping[str, int | float]) -> dict[str, float]:
    """Media delle distribuzioni normalizzate: ogni fonte pesa uguale, qualunque sia il totale."""
    result: dict[str, float] = defaultdict(float)
    for distribution in distributions:
        total = sum(distribution.values())
        for key, value in distribution.items():
            result[key] += value / total / len(distributions)
    return dict(result)


def quota(weights: Mapping[str, float], n: int) -> list[str]:
    """n valori in proporzione ai pesi (metodo del resto più grande), in ordine deterministico."""
    total = sum(weights.values())
    shares = {key: n * weight / total for key, weight in weights.items()}
    counts = {key: int(share) for key, share in shares.items()}
    by_remainder = sorted(shares, key=lambda key: (-(shares[key] - counts[key]), key))
    for key in by_remainder[: n - sum(counts.values())]:
        counts[key] += 1
    return [key for key in sorted(counts) for _ in range(counts[key])]


def _regrouped(counts: Mapping[str, int], key_of) -> dict[str, int]:
    grouped: dict[str, int] = defaultdict(int)
    for label, count in counts.items():
        key = key_of(label)
        if key is not None:
            grouped[key] += count
    return dict(grouped)


def pool_weights(
    audience: Mapping[str, Mapping[str, Mapping[str, int]]], decision_makers_only: bool = False
) -> dict[str, dict[str, float]]:
    """Pesi per attributo, mediando follower e visitatori. Le località estere sono escluse."""
    sources = [audience["followers"], audience["visitors"]]

    def keep(seniority: str) -> str | None:
        allowed = not decision_makers_only or seniority in DECISION_SENIORITIES
        return seniority if allowed else None

    return {
        "seniority": blend(*(_regrouped(s["seniority"], keep) for s in sources)),
        "company_size": blend(*(_regrouped(s["company_size"], company_size_of) for s in sources)),
        "job_function": blend(*(s["job_function"] for s in sources)),
        "industry": blend(*(s["industry"] for s in sources)),
        "region": blend(*(_regrouped(s["location"], region_of) for s in sources)),
    }
