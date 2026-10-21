import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.personas.audience import quota

_OWNER_SENIORITIES = frozenset({"Owner", "Partner"})
_NO_COHERENT_MATCH = "Nessuna combinazione coerente di attributi per le personas."


@dataclass(frozen=True)
class Attributes:
    seniority: str
    company_size: str
    job_function: str
    industry: str
    region: str
    ai_attitude: str
    linkedin_use: str


def _coherent(seniority: str, company_size: str) -> bool:
    # shortcut: una sola regola (titolari e soci non guidano una grande azienda), servono
    # più regole solo se i dati reali mostrano altre combinazioni impossibili.
    return not (seniority in _OWNER_SENIORITIES and company_size == "grande")


def is_coherent(attributes: Attributes) -> bool:
    return _coherent(attributes.seniority, attributes.company_size)


def _repaired_sizes(seniorities: Sequence[str], sizes: Sequence[str]) -> list[str]:
    """Scambia la dimensione aziendale tra personas finché nessuna combinazione è incoerente."""
    fixed = list(sizes)
    for i, seniority in enumerate(seniorities):
        if _coherent(seniority, fixed[i]):
            continue
        for j, other in enumerate(seniorities):
            if _coherent(seniority, fixed[j]) and _coherent(other, fixed[i]):
                fixed[i], fixed[j] = fixed[j], fixed[i]
                break
        else:
            raise ValueError(_NO_COHERENT_MATCH)
    return fixed


def sample_attributes(
    weights: Mapping[str, Mapping[str, float]], n: int, seed: int
) -> list[Attributes]:
    """n personas con le distribuzioni di ogni attributo rispettate a quota, accoppiate a caso."""
    rng = random.Random(seed)
    columns = {dimension: rng.sample(quota(w, n), n) for dimension, w in sorted(weights.items())}
    columns["company_size"] = _repaired_sizes(columns["seniority"], columns["company_size"])
    return [
        Attributes(**{dimension: column[i] for dimension, column in columns.items()})
        for i in range(n)
    ]
