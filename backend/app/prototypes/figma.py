"""Import da Figma con l'API REST: frame, collegamenti del prototipo e render PNG.

Il file deve essere condiviso con «chiunque abbia il link»; serve FIGMA_TOKEN nel .env.
"""

import logging
from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings
from app.prototypes.raw import RawPrototype, RawScreen, RawStart
from app.prototypes.source import parse_figma_url

logger = logging.getLogger(__name__)

FIGMA_API = "https://api.figma.com/v1"
MAX_STARTS = 3
MAX_SCREENS = 8
PRIVATE_FILE = (
    "Non possiamo aprire il file: è privato. "
    "In Figma imposta la condivisione su «chiunque abbia il link» e riprova."
)
IMPORT_FAILED = "Import da Figma non riuscito. Riprova tra poco."
NO_TOKEN = "Import da Figma non configurato: manca FIGMA_TOKEN."


def _walk(node: dict[str, Any]):
    yield node
    for child in node.get("children", []):
        yield from _walk(child)


def _frames(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in _walk(document) if n.get("type") == "FRAME"}


def _destinations(frame: dict[str, Any]) -> list[str]:
    """Frame raggiunti dai collegamenti del prototipo, nell'ordine in cui compaiono."""
    return [
        action["destinationId"]
        for node in _walk(frame)
        for interaction in node.get("interactions", [])
        for action in interaction.get("actions", [])
        if action.get("type") == "NODE" and action.get("destinationId")
    ]


def _start_points(
    document: dict[str, Any], frames: dict, wanted: str | None
) -> list[tuple[str, str]]:
    declared = [
        (point["nodeId"], point.get("name") or frames[point["nodeId"]]["name"])
        for page in document.get("children", [])
        for point in page.get("flowStartingPoints", [])
        if point.get("nodeId") in frames
    ]
    if wanted in frames and wanted not in {node_id for node_id, _ in declared}:
        declared = [(wanted, frames[wanted]["name"]), *declared]
    if not declared and frames:
        first = next(iter(frames))
        declared = [(first, frames[first]["name"])]
    return declared[:MAX_STARTS]


def _path(start: str, frames: dict[str, dict[str, Any]]) -> list[str]:
    """Una sola catena: da ogni frame al primo collegamento non ancora visitato."""
    path = [start]
    while len(path) < MAX_SCREENS:
        unseen = [d for d in _destinations(frames[path[-1]]) if d in frames and d not in path]
        if not unseen:
            break
        path.append(unseen[0])
    return path


async def _get(client: httpx.AsyncClient, url: str, **kwargs: Any) -> httpx.Response:
    try:
        response = await client.get(url, **kwargs)
    except httpx.HTTPError as exc:
        logger.exception("Figma non raggiungibile")
        raise HTTPException(status_code=502, detail=IMPORT_FAILED) from exc
    if response.status_code in (403, 404):
        raise HTTPException(status_code=403, detail=PRIVATE_FILE)
    if response.is_error:
        logger.error("Figma ha risposto %s", response.status_code)
        raise HTTPException(status_code=502, detail=IMPORT_FAILED)
    return response


async def _render(client: httpx.AsyncClient, key: str, ids: list[str]) -> dict[str, bytes]:
    response = await _get(
        client, f"{FIGMA_API}/images/{key}", params={"ids": ",".join(ids), "format": "png"}
    )
    urls: dict[str, str | None] = response.json().get("images", {})
    rendered: dict[str, bytes] = {}
    for node_id in ids:
        if urls.get(node_id) is None:
            raise HTTPException(status_code=502, detail=IMPORT_FAILED)
        rendered[node_id] = (await _get(client, urls[node_id])).content
    return rendered


async def import_figma(url: str, client: httpx.AsyncClient) -> RawPrototype:
    key, wanted = parse_figma_url(url)
    if not settings.figma_token:
        raise HTTPException(status_code=502, detail=NO_TOKEN)
    headers = {"X-Figma-Token": settings.figma_token}
    data = (await _get(client, f"{FIGMA_API}/files/{key}", headers=headers)).json()
    frames = _frames(data["document"])
    paths = [
        (name, _path(node_id, frames))
        for node_id, name in _start_points(data["document"], frames, wanted)
    ]
    if not paths:
        raise HTTPException(status_code=502, detail="Nel file Figma non ci sono schermate.")
    ids = list(dict.fromkeys(node_id for _, path in paths for node_id in path))
    rendered = await _render(client, key, ids)
    starts = tuple(
        RawStart(name, tuple(RawScreen(frames[i]["name"], rendered[i]) for i in path))
        for name, path in paths
    )
    return RawPrototype(name=data.get("name", "Prototipo Figma"), starts=starts)
