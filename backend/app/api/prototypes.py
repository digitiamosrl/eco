from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, ValidationError
from starlette.datastructures import UploadFile

from app.models import Prototype
from app.prototypes import service
from app.prototypes.source import INVALID_LINK

router = APIRouter()

MAX_HTML_BYTES = 2 * 1024 * 1024
_FORM_OVERHEAD = 64 * 1024
_MAX_JSON_BYTES = 4 * 1024
TOO_LARGE = "Richiesta troppo grande"


def _check_size(request: Request, limit: int) -> None:
    """Prima di leggere il corpo: form() e json() lo caricherebbero tutto in memoria o su disco."""
    length = request.headers.get("content-length", "")
    if not length.isdigit() or int(length) > limit:
        raise HTTPException(status_code=413, detail=TOO_LARGE)


class ImportRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: Literal["figma", "artifact"]
    url: str


async def _read_html(form_file: Any) -> str:
    if not isinstance(form_file, UploadFile):
        raise HTTPException(status_code=422, detail="Il campo file deve essere un file HTML")
    data = await form_file.read(MAX_HTML_BYTES + 1)
    if len(data) > MAX_HTML_BYTES:
        raise HTTPException(status_code=422, detail="Il file HTML supera 2 MB")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Il file HTML deve essere UTF-8") from exc


async def _import_html(request: Request) -> Prototype:
    _check_size(request, MAX_HTML_BYTES + _FORM_OVERHEAD)
    form = await request.form()
    if form.get("source") != "artifact":
        raise HTTPException(status_code=422, detail="Con un file la sorgente è «artifact»")
    return await service.import_from_artifact_html(await _read_html(form.get("file")))


async def _import_link(request: Request) -> Prototype:
    _check_size(request, _MAX_JSON_BYTES)
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=INVALID_LINK) from exc
    try:
        body = ImportRequest.model_validate(payload)
    except ValidationError as exc:
        raise RequestValidationError(
            [{**error, "loc": ("body", *error["loc"])} for error in exc.errors()]
        ) from exc
    if body.source == "figma":
        return await service.import_from_figma(body.url)
    return await service.import_from_artifact_url(body.url)


@router.post("/prototypes/import", status_code=201, response_model=Prototype)
async def import_prototype(request: Request) -> Prototype:
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        return await _import_html(request)
    return await _import_link(request)
