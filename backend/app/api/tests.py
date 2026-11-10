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
    PrototypePath,
    PrototypeTestRequest,
    Stimulus,
    Test,
)
from app.uploads import Upload, attachment_kind, delete_uploads, save_uploads, upload_url

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
            attachment_kind=attachment_kind(uploads[index]) if uploads else None,
        )
        for index, variant in enumerate(body.variants)
    ]


def _flow_stimuli(flow_ids: list[str]) -> list[Stimulus]:
    unknown = [flow_id for flow_id in flow_ids if flow_id not in FLOWS_BY_ID]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Flusso non trovato: {', '.join(unknown)}")
    return [
        Stimulus(
            id=f"{flow_id}-{index}",
            kind="prototype_screen",
            flow_id=flow_id,
            screen_index=index,
        )
        for flow_id in flow_ids
        for index in range(FLOWS_BY_ID[flow_id].screen_count)
    ]


def _imported_stimuli(prototype_id: str, paths: list[PrototypePath]) -> list[Stimulus]:
    prototype = store.get_prototype(prototype_id)
    if prototype is None:
        raise HTTPException(status_code=422, detail="Prototipo non trovato")
    starts = {start.id: start for start in prototype.starts}
    stimuli: list[Stimulus] = []
    for path in paths:
        start = starts.get(path.start_id)
        screens = {screen.index: screen for screen in start.screens} if start else {}
        if start is None or any(i not in screens for i in path.screen_indexes):
            raise HTTPException(status_code=422, detail="Percorso non valido per questo prototipo")
        stimuli += [
            Stimulus(
                id=f"{prototype_id}-{start.id}-{i}",
                kind="prototype_screen",
                flow_id=f"{prototype_id}:{start.id}",
                screen_index=i,
                image_url=screens[i].image_url,
                page_structure=screens[i].name,
            )
            for i in dict.fromkeys(path.screen_indexes)
        ]
    return stimuli


def _prototype_stimuli(body: PrototypeTestRequest) -> list[Stimulus]:
    if body.flow_ids is not None:
        return _flow_stimuli(body.flow_ids)
    return _imported_stimuli(body.prototype_id or "", body.paths or [])


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


def _uses_panel(body: CreateTestRequest) -> bool:
    """Post e prototipi importati passano dalle personas; i flussi catturati restano a fixture."""
    return isinstance(body, PostTestRequest) or body.prototype_id is not None


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
    if _uses_panel(body):
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
