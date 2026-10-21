import re
import uuid
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, NamedTuple

from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.config import MAX_IMAGE_BYTES, settings

_VARIANT_KEY = re.compile(r"^variants\[(\d+)\]\[(label|text|image)\]$")
_FORMAT_ERROR = "Formato immagine non valido: usa PNG, JPEG o WebP"


class Upload(NamedTuple):
    name: str
    data: bytes


def group_variant_fields(items: Iterable[tuple[str, Any]]) -> list[dict[str, Any]]:
    """Raggruppa `variants[i][campo]` per indice, in ordine. Le altre chiavi si ignorano."""
    grouped: dict[int, dict[str, Any]] = {}
    for key, value in items:
        match = _VARIANT_KEY.match(key)
        if match is None:
            continue
        index, field = int(match.group(1)), match.group(2)
        grouped = {**grouped, index: {**grouped.get(index, {}), field: value}}
    return [grouped[index] for index in sorted(grouped)]


def _extension(data: bytes) -> str | None:
    """Il tipo si riconosce dai primi byte, non da estensione o header del client."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def make_upload(data: bytes) -> Upload:
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=422, detail="L'immagine supera 5 MB")
    extension = _extension(data)
    if extension is None:
        raise HTTPException(status_code=422, detail=_FORMAT_ERROR)
    return Upload(name=f"{uuid.uuid4().hex}{extension}", data=data)


async def read_upload(file: UploadFile) -> Upload:
    """Legge al massimo un byte oltre il limite, così un file enorme non finisce in memoria."""
    return make_upload(await file.read(MAX_IMAGE_BYTES + 1))


def upload_url(upload: Upload | None) -> str | None:
    return None if upload is None else f"/files/{upload.name}"


def save_uploads(uploads: Sequence[Upload | None]) -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    for upload in uploads:
        if upload is not None:
            (settings.upload_dir / upload.name).write_bytes(upload.data)


def delete_uploads(uploads: Sequence[Upload | None]) -> None:
    for upload in uploads:
        if upload is not None:
            (settings.upload_dir / upload.name).unlink(missing_ok=True)


def find_upload(name: str) -> Path | None:
    """Solo file diretti in UPLOAD_DIR: niente separatori, niente '..'."""
    if name in {"", ".", ".."} or "/" in name or "\\" in name:
        return None
    path = settings.upload_dir / name
    return path if path.is_file() else None
