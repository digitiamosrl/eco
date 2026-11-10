import asyncio
import logging
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException

from app import store
from app.models import Prototype, PrototypeScreen, PrototypeStart
from app.prototypes.artifact import import_artifact
from app.prototypes.figma import import_figma
from app.prototypes.raw import RawPrototype, RawStart
from app.prototypes.source import check_artifact_url
from app.uploads import Upload, make_upload, save_uploads, upload_url

logger = logging.getLogger(__name__)
# Un browser o un import per volta (al massimo due): non c'è altro limite alle richieste.
_SLOTS = asyncio.Semaphore(2)
BAD_SCREEN = "Una schermata supera 5 MB o non è un'immagine valida."


def _checked(png: bytes) -> Upload | None:
    try:
        return make_upload(png)
    except HTTPException:
        return None


def _screens(start: RawStart) -> tuple[list[PrototypeScreen], list[Upload], bool]:
    """Le schermate valide in ordine, fino alla prima troppo grande (il resto non si raggiunge)."""
    screens: list[PrototypeScreen] = []
    uploads: list[Upload] = []
    for index, screen in enumerate(start.screens):
        upload = _checked(screen.png)
        if upload is None:
            logger.warning("%s: schermata %d scartata (oltre 5 MB o non valida)", start.name, index)
            return screens, uploads, True
        uploads.append(upload)
        screens.append(
            PrototypeScreen(index=index, name=screen.name, image_url=upload_url(upload) or "")
        )
    return screens, uploads, False


def _to_prototype(source: str, raw: RawPrototype) -> tuple[Prototype, list[Upload]]:
    """Un percorso con una schermata troppo grande si accorcia o si scarta: gli altri restano."""
    uploads: list[Upload] = []
    starts: list[PrototypeStart] = []
    for start in raw.starts:
        screens, start_uploads, cut = _screens(start)
        if not screens:
            continue
        uploads += start_uploads
        name = f"{start.name} (accorciato: schermata troppo grande)" if cut else start.name
        starts.append(PrototypeStart(id=f"s{len(starts) + 1}", name=name, screens=screens))
    if not starts:
        raise HTTPException(status_code=502, detail=BAD_SCREEN)
    prototype = Prototype(
        id=uuid.uuid4().hex,
        source=source,  # type: ignore[arg-type]
        name=raw.name,
        imported_at=datetime.now(UTC).isoformat(),
        starts=starts,
    )
    return prototype, uploads


async def _save(source: str, raw: RawPrototype) -> Prototype:
    prototype, uploads = _to_prototype(source, raw)
    save_uploads(uploads)
    store.add_prototype(prototype)
    return prototype


async def import_from_figma(url: str) -> Prototype:
    async with _SLOTS, httpx.AsyncClient(timeout=60) as client:
        return await _save("figma", await import_figma(url, client))


async def import_from_artifact_url(url: str) -> Prototype:
    checked = check_artifact_url(url)
    async with _SLOTS:
        return await _save("artifact", await import_artifact(url=checked))


async def import_from_artifact_html(html: str) -> Prototype:
    async with _SLOTS:
        return await _save("artifact", await import_artifact(html=html))
