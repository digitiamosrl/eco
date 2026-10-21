from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.uploads import find_upload

router = APIRouter()


@router.get("/files/{name}")
def get_file(name: str) -> FileResponse:
    path = find_upload(name)
    if path is None:
        raise HTTPException(status_code=404, detail="File non trovato")
    return FileResponse(path)
