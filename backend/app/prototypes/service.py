import asyncio
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException

from app import store
from app.models import Prototype, PrototypeScreen, PrototypeStart
from app.prototypes.artifact import import_artifact
from app.prototypes.figma import import_figma
from app.prototypes.raw import RawPrototype
from app.prototypes.source import check_artifact_url
from app.uploads import Upload, make_upload, save_uploads, upload_url

# Un browser o un import per volta (al massimo due): non c'è altro limite alle richieste.
_SLOTS = asyncio.Semaphore(2)
BAD_SCREEN = "Una schermata supera 5 MB o non è un'immagine valida."


def _checked(png: bytes) -> Upload:
    try:
        return make_upload(png)
    except HTTPException as exc:
        raise HTTPException(status_code=502, detail=BAD_SCREEN) from exc


def _to_prototype(source: str, raw: RawPrototype) -> tuple[Prototype, list[Upload]]:
    uploads: list[Upload] = []
    starts: list[PrototypeStart] = []
    for start_index, start in enumerate(raw.starts, start=1):
        screens: list[PrototypeScreen] = []
        for index, screen in enumerate(start.screens):
            upload = _checked(screen.png)
            uploads.append(upload)
            screens.append(
                PrototypeScreen(index=index, name=screen.name, image_url=upload_url(upload) or "")
            )
        starts.append(PrototypeStart(id=f"s{start_index}", name=start.name, screens=screens))
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
