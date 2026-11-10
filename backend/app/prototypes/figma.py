"""Import da Figma con l'API REST: frame, collegamenti del prototipo e render PNG.

Il file deve essere condiviso con «chiunque abbia il link»; serve FIGMA_TOKEN nel .env.
"""

import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from app.config import settings
from app.prototypes.raw import RawPrototype, RawScreen, RawStart
from app.prototypes.source import parse_figma_url

logger = logging.getLogger(__name__)

FIGMA_API = "https://api.figma.com/v1"
MAX_STARTS = 10  # importati; i percorsi scelti per il test restano al massimo 3
MAX_SCREENS = 8
PRIVATE_FILE = (
    "Non possiamo aprire il file: è privato. "
    "In Figma imposta la condivisione su «chiunque abbia il link» e riprova."
)
IMPORT_FAILED = "Import da Figma non riuscito. Riprova tra poco."
_IMAGE_HOSTS = (".amazonaws.com", ".figma.com")
BAD_TOKEN = "Il token Figma non è valido o è scaduto."
NO_PAGE = (
    "Copia il link da Condividi › Copia link al prototipo: deve contenere la pagina (page-id)."
)
NO_SCREENS = "Nel file Figma non ci sono schermate."
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
        if "token" in response.text.lower():
            raise HTTPException(status_code=502, detail=BAD_TOKEN)
        raise HTTPException(status_code=403, detail=PRIVATE_FILE)
    if response.is_error:
        logger.error("Figma ha risposto %s", response.status_code)
        raise HTTPException(status_code=502, detail=IMPORT_FAILED)
    return response


def _is_image_host(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").endswith(_IMAGE_HOSTS)


async def _render(
    client: httpx.AsyncClient, key: str, ids: list[str], headers: dict[str, str]
) -> dict[str, bytes]:
    response = await _get(
        client,
        f"{FIGMA_API}/images/{key}",
        headers=headers,
        params={"ids": ",".join(ids), "format": "png"},
    )
    urls: dict[str, str | None] = response.json().get("images", {})
    rendered: dict[str, bytes] = {}
    for node_id in ids:
        image_url = urls.get(node_id)
        if image_url is None or not _is_image_host(image_url):
            raise HTTPException(status_code=502, detail=IMPORT_FAILED)
        rendered[node_id] = (await _get(client, image_url)).content
    return rendered


async def _document(
    client: httpx.AsyncClient, key: str, page_id: str, headers: dict[str, str]
) -> tuple[str, dict[str, Any]]:
    """Solo la pagina del link: un file Figma intero può pesare centinaia di MB."""
    data = (
        await _get(
            client, f"{FIGMA_API}/files/{key}/nodes", headers=headers, params={"ids": page_id}
        )
    ).json()
    canvases = [node["document"] for node in data.get("nodes", {}).values() if node]
    return data.get("name", "Prototipo Figma"), {"children": canvases}


async def import_figma(url: str, client: httpx.AsyncClient) -> RawPrototype:
    key, wanted, page_id = parse_figma_url(url)
    if page_id is None:
        raise HTTPException(status_code=422, detail=NO_PAGE)
    if not settings.figma_token:
        raise HTTPException(status_code=502, detail=NO_TOKEN)
    headers = {"X-Figma-Token": settings.figma_token}
    name, document = await _document(client, key, page_id, headers)
    frames = _frames(document)
    paths = [(n, _path(i, frames)) for i, n in _start_points(document, frames, wanted)]
    if not paths:
        raise HTTPException(status_code=502, detail=NO_SCREENS)
    ids = list(dict.fromkeys(node_id for _, path in paths for node_id in path))
    rendered = await _render(client, key, ids, headers)
    starts = tuple(
        RawStart(start, tuple(RawScreen(frames[i]["name"], rendered[i]) for i in path))
        for start, path in paths
    )
    return RawPrototype(name=name, starts=starts)
