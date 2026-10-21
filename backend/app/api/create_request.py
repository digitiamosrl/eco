from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import TypeAdapter, ValidationError
from starlette.datastructures import UploadFile

from app.models import CreateTestRequest
from app.uploads import Upload, group_variant_fields, read_upload

_ADAPTER: TypeAdapter[CreateTestRequest] = TypeAdapter(CreateTestRequest)


def _validate(payload: object) -> CreateTestRequest:
    try:
        return _ADAPTER.validate_python(payload)
    except ValidationError as exc:
        # Stessa forma degli errori di FastAPI, così il gestore 422 in main.py li tratta uguale.
        raise RequestValidationError(
            [{**error, "loc": ("body", *error["loc"])} for error in exc.errors()]
        ) from exc


async def _read_json(request: Request) -> object:
    try:
        return await request.json()
    except ValueError:
        return None


async def _read_image(value: Any) -> Upload | None:
    if value is None or value == "":
        return None
    if not isinstance(value, UploadFile):
        raise HTTPException(status_code=422, detail="Il campo immagine deve essere un file")
    return await read_upload(value)


async def read_create_request(
    request: Request,
) -> tuple[CreateTestRequest, tuple[Upload | None, ...]]:
    """Legge `POST /tests`: multipart per i post con immagini, JSON per il resto."""
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        return _validate(await _read_json(request)), ()
    form = await request.form()
    variants = group_variant_fields(form.multi_items())
    body = _validate(
        {
            "kind": form.get("kind"),
            "variants": [{"label": v.get("label"), "text": v.get("text")} for v in variants],
        }
    )
    uploads = tuple([await _read_image(v.get("image")) for v in variants])
    return body, uploads
