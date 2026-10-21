from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import store
from app.api.flows import router as flows_router
from app.api.health import router as health_router
from app.api.personas import router as personas_router
from app.api.reports import router as reports_router
from app.api.tests import router as tests_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    store.init_db()
    store.mark_interrupted()
    yield


app = FastAPI(title="eco", lifespan=lifespan)
app.include_router(health_router)
app.include_router(personas_router)
app.include_router(flows_router)
app.include_router(tests_router)
app.include_router(reports_router)

# Gli errori di FastAPI (lista di dict) non escono mai: si mostra solo il campo, in italiano.
_TAG_LOCATIONS = {"post", "prototype"}


def _field_name(error: dict) -> str:
    parts = [str(p) for p in error["loc"][1:] if not isinstance(p, int) and p not in _TAG_LOCATIONS]
    return ".".join(parts) or "corpo"


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    field = _field_name(exc.errors()[0])
    return JSONResponse(status_code=422, content={"detail": f"Richiesta non valida: {field}"})
