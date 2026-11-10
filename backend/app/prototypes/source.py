"""Riconosce da dove arriva il prototipo. Solo host noti: niente richieste verso URL arbitrari."""

import re
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException

INVALID_LINK = "Link non valido: usa un link Figma o un artifact Claude pubblico."
_FIGMA_HOSTS = {"figma.com", "www.figma.com"}
_FIGMA_PATH = re.compile(r"^/(?:proto|design|file)/([A-Za-z0-9]+)")
_ARTIFACT_HOSTS = {"claude.ai", "www.claude.ai"}
_ARTIFACT_PREFIX = "/public/artifacts/"


def _node_id(value: str | None) -> str | None:
    """`1-2` nel link è `1:2` nell'API."""
    return None if value is None else value.replace("-", ":")


def parse_figma_url(url: str) -> tuple[str, str | None, str | None]:
    """Chiave del file, nodo di partenza e pagina, gli ultimi due solo se il link li ha."""
    parsed = urlparse(url)
    match = _FIGMA_PATH.match(parsed.path)
    if parsed.scheme != "https" or parsed.hostname not in _FIGMA_HOSTS or match is None:
        raise HTTPException(status_code=422, detail=INVALID_LINK)
    query = parse_qs(parsed.query)
    start = (query.get("starting-point-node-id") or query.get("node-id") or [None])[0]
    return match.group(1), _node_id(start), _node_id((query.get("page-id") or [None])[0])


def check_artifact_url(url: str) -> str:
    parsed = urlparse(url)
    valid = (
        parsed.scheme == "https"
        and parsed.hostname in _ARTIFACT_HOSTS
        and parsed.path.startswith(_ARTIFACT_PREFIX)
        and len(parsed.path) > len(_ARTIFACT_PREFIX)
    )
    if not valid:
        raise HTTPException(status_code=422, detail=INVALID_LINK)
    return url
