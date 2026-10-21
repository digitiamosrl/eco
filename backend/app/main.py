from fastapi import FastAPI

from app.api.flows import router as flows_router
from app.api.health import router as health_router
from app.api.personas import router as personas_router
from app.api.tests import router as tests_router

app = FastAPI(title="eco")
app.include_router(health_router)
app.include_router(personas_router)
app.include_router(flows_router)
app.include_router(tests_router)
