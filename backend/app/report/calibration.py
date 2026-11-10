"""Calibrazione: quanto la classifica del panel rispecchia l'engagement reale (fidelity score).

Si calcola una volta, fuori dal flusso del test, e si salva in `calibration.json`;
ogni report lo legge da lì. Se il file manca, il report dichiara che la calibrazione non c'è.
"""

import json
import logging
from collections.abc import Mapping, Sequence
from itertools import combinations
from math import sqrt
from pathlib import Path

from pydantic import ValidationError

from app.config import settings
from app.models import Fidelity

logger = logging.getLogger(__name__)


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Correlazione di rango con gestione dei pareggi. None se un vettore è costante."""
    concordant = discordant = tied_x = tied_y = 0
    for (x1, y1), (x2, y2) in combinations(zip(x, y, strict=True), 2):
        dx, dy = x1 - x2, y1 - y2
        if dx == 0 and dy == 0:
            continue
        if dx == 0:
            tied_x += 1
        elif dy == 0:
            tied_y += 1
        elif (dx > 0) == (dy > 0):
            concordant += 1
        else:
            discordant += 1
    denominator = sqrt((concordant + discordant + tied_x) * (concordant + discordant + tied_y))
    return None if denominator == 0 else (concordant - discordant) / denominator


def compute_fidelity(
    panel_means: Mapping[str, float], engagement: Mapping[str, float], basis: str
) -> Fidelity | None:
    """Tau-b tra media del panel ed engagement reale, sui post presenti in entrambi."""
    common = sorted(panel_means.keys() & engagement.keys())
    tau = kendall_tau_b([panel_means[p] for p in common], [engagement[p] for p in common])
    return None if tau is None else Fidelity(score=round(tau, 2), basis=basis)


def load_fidelity(path: Path | None = None) -> Fidelity | None:
    """None se la calibrazione non è disponibile (file assente o illeggibile)."""
    target = path or Path(settings.calibration_path)
    if not target.is_file():
        return None
    try:
        return Fidelity.model_validate(json.loads(target.read_text("utf-8")))
    except (ValueError, ValidationError):
        logger.exception("Calibrazione non valida in %s", target)
        return None
