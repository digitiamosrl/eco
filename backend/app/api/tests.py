import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app import store
from app.api.create_request import read_create_request
from app.api.personas import PERSONAS
from app.config import settings
from app.engine.responder import build_responder
from app.engine.runner import run_post_test
from app.loaders import load_list
from app.models import (
    CreateTestRequest,
    Flow,
    PostTestRequest,
    PrototypeTestRequest,
    Stimulus,
    Test,
)
from app.uploads import Upload, delete_uploads, save_uploads, upload_url

router = APIRouter()

FLOWS_BY_ID = {flow.id: flow for flow in load_list("flows.json", Flow)}


def _post_stimuli(body: PostTestRequest, uploads: tuple[Upload | None, ...]) -> list[Stimulus]:
    return [
        Stimulus(
            id=f"variante-{variant.label.lower()}",
            kind="post",
            variant_label=variant.label,
            text=variant.text,
            image_url=upload_url(uploads[index]) if uploads else None,
        )
        for index, variant in enumerate(body.variants)
    ]


def _prototype_stimuli(body: PrototypeTestRequest) -> list[Stimulus]:
    unknown = [flow_id for flow_id in body.flow_ids if flow_id not in FLOWS_BY_ID]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Flusso non trovato: {', '.join(unknown)}")
    return [
        Stimulus(
            id=f"{flow_id}-{index}",
            kind="prototype_screen",
            flow_id=flow_id,
            screen_index=index,
        )
        for flow_id in body.flow_ids
        for index in range(FLOWS_BY_ID[flow_id].screen_count)
    ]


def _build_test(body: CreateTestRequest, uploads: tuple[Upload | None, ...]) -> Test:
    if isinstance(body, PostTestRequest):
        stimuli = _post_stimuli(body, uploads)
    else:
        stimuli = _prototype_stimuli(body)
    return Test(
        id=uuid4().hex,
        kind=body.kind,
        status="queued",
        created_at=datetime.now(UTC).isoformat(),
        done_count=0,
        total_count=len(PERSONAS) * len(stimuli),
        stimuli=stimuli,
    )


def run_test(test_id: str) -> None:
    test = store.update(test_id, status="running")
    pause = settings.fixture_delay_seconds / test.total_count
    for done in range(1, test.total_count + 1):
        time.sleep(pause)
        store.update(test_id, done_count=done)
    store.update(test_id, status="done")


@router.post(
    "/tests",
    status_code=201,
    response_model=Test,
    response_model_exclude_none=True,
)
async def create_test(request: Request, background_tasks: BackgroundTasks) -> Test:
    body, uploads = await read_create_request(request)
    test = _build_test(body, uploads)
    save_uploads(uploads)
    if not store.add_if_idle(test):
        delete_uploads(uploads)
        raise HTTPException(status_code=409, detail="Un test è già in corso")
    if test.kind == "post":
        background_tasks.add_task(run_post_test, test.id, build_responder(), PERSONAS)
    else:
        background_tasks.add_task(run_test, test.id)
    return test


@router.get("/tests", response_model=list[Test], response_model_exclude_none=True)
def list_tests() -> list[Test]:
    return store.list_most_recent_first()


@router.get("/tests/{test_id}", response_model=Test, response_model_exclude_none=True)
def get_test(test_id: str) -> Test:
    test = store.get(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test non trovato")
    return test
