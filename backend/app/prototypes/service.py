import uuid
from datetime import UTC, datetime

import httpx

from app import store
from app.models import Prototype, PrototypeScreen, PrototypeStart
from app.prototypes.artifact import import_artifact
from app.prototypes.figma import import_figma
from app.prototypes.raw import RawPrototype
from app.prototypes.source import check_artifact_url
from app.uploads import Upload, save_uploads, upload_url


def _to_prototype(source: str, raw: RawPrototype) -> tuple[Prototype, list[Upload]]:
    uploads: list[Upload] = []
    starts: list[PrototypeStart] = []
    for start_index, start in enumerate(raw.starts, start=1):
        screens: list[PrototypeScreen] = []
        for index, screen in enumerate(start.screens):
            upload = Upload(name=f"{uuid.uuid4().hex}.png", data=screen.png)
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
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        return await _save("figma", await import_figma(url, client))


async def import_from_artifact_url(url: str) -> Prototype:
    return await _save("artifact", await import_artifact(url=check_artifact_url(url)))


async def import_from_artifact_html(html: str) -> Prototype:
    return await _save("artifact", await import_artifact(html=html))
