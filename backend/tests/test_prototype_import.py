import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.prototypes import figma, service
from app.prototypes.raw import RawPrototype, RawScreen, RawStart
from app.prototypes.source import check_artifact_url, parse_figma_url

client = TestClient(app)
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
ARTIFACT = "https://claude.ai/public/artifacts/abc-123"


def _raw() -> RawPrototype:
    screens = tuple(RawScreen(f"Schermata {i}", PNG) for i in (1, 2, 3))
    return RawPrototype(name="Demo", starts=(RawStart("Percorso 1", screens),))


@pytest.fixture
def fake_artifact(monkeypatch):
    async def capture(*, url=None, html=None):
        return _raw()

    monkeypatch.setattr(service, "import_artifact", capture)


def test_figma_url_is_parsed_and_node_id_is_normalised() -> None:
    assert parse_figma_url("https://www.figma.com/proto/AbC123/Nome?node-id=1-2") == (
        "AbC123",
        "1:2",
    )
    assert parse_figma_url("https://figma.com/design/Key9/x") == ("Key9", None)


@pytest.mark.parametrize(
    "url",
    ["http://www.figma.com/proto/Key/x", "https://evil.com/proto/Key/x", "https://figma.com/", "x"],
)
def test_invalid_figma_links_are_rejected(url: str) -> None:
    with pytest.raises(HTTPException) as error:
        parse_figma_url(url)
    assert error.value.status_code == 422


def test_artifact_urls_accept_only_public_claude_artifacts() -> None:
    assert check_artifact_url(ARTIFACT) == ARTIFACT
    for url in (
        "https://claude.ai/chat/1",
        "https://evil.com/public/artifacts/x",
        "https://claude.ai/public/artifacts/",
    ):
        with pytest.raises(HTTPException):
            check_artifact_url(url)


def _frame(node_id: str, name: str, goes_to: str | None = None) -> dict:
    child = []
    if goes_to:
        child = [
            {
                "id": f"{node_id}-btn",
                "type": "RECTANGLE",
                "interactions": [{"actions": [{"type": "NODE", "destinationId": goes_to}]}],
            }
        ]
    return {"id": node_id, "name": name, "type": "FRAME", "children": child}


def _figma_handler(status: int = 200):
    document = {
        "id": "0:0",
        "type": "DOCUMENT",
        "children": [
            {
                "id": "0:1",
                "type": "CANVAS",
                "flowStartingPoints": [{"nodeId": "1:1", "name": "Onboarding"}],
                "children": [
                    _frame("1:1", "Home", "1:2"),
                    _frame("1:2", "Dettaglio", "1:3"),
                    _frame("1:3", "Fine"),
                ],
            }
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status)
        if request.url.path.startswith("/v1/files/"):
            assert request.headers["X-Figma-Token"] == "tok"
            return httpx.Response(200, json={"name": "App", "document": document})
        if request.url.path.startswith("/v1/images/"):
            ids = request.url.params["ids"].split(",")
            return httpx.Response(
                200, json={"images": {i: f"https://img.test/{i}.png" for i in ids}}
            )
        return httpx.Response(200, content=PNG)

    return handler


async def _figma(status: int = 200) -> RawPrototype:
    async with httpx.AsyncClient(transport=httpx.MockTransport(_figma_handler(status))) as http:
        return await figma.import_figma("https://www.figma.com/proto/Key1/x", http)


@pytest.mark.anyio
async def test_figma_follows_prototype_links_from_the_starting_point(monkeypatch) -> None:
    monkeypatch.setattr(settings, "figma_token", "tok")
    raw = await _figma()
    assert raw.name == "App"
    [start] = raw.starts
    assert start.name == "Onboarding"
    assert [s.name for s in start.screens] == ["Home", "Dettaglio", "Fine"]
    assert all(s.png == PNG for s in start.screens)


@pytest.mark.anyio
async def test_private_figma_file_gets_the_agreed_message(monkeypatch) -> None:
    monkeypatch.setattr(settings, "figma_token", "tok")
    with pytest.raises(HTTPException) as error:
        await _figma(status=403)
    assert error.value.status_code == 403
    assert error.value.detail == figma.PRIVATE_FILE


@pytest.mark.anyio
async def test_figma_failure_and_missing_token_are_502(monkeypatch) -> None:
    monkeypatch.setattr(settings, "figma_token", "tok")
    with pytest.raises(HTTPException) as error:
        await _figma(status=500)
    assert error.value.status_code == 502
    monkeypatch.setattr(settings, "figma_token", "")
    with pytest.raises(HTTPException) as error:
        await _figma()
    assert error.value.detail == figma.NO_TOKEN


def test_artifact_link_import_returns_a_valid_prototype(fake_artifact, validate) -> None:
    response = client.post("/prototypes/import", json={"source": "artifact", "url": ARTIFACT})
    assert response.status_code == 201
    prototype = response.json()
    validate("prototype.schema.json", prototype)
    assert prototype["source"] == "artifact"
    [start] = prototype["starts"]
    assert [s["index"] for s in start["screens"]] == [0, 1, 2]
    assert client.get(start["screens"][0]["image_url"]).content == PNG


def test_artifact_file_import(fake_artifact, validate) -> None:
    files = {"source": (None, "artifact"), "file": ("a.html", b"<h1>Ciao</h1>", "text/html")}
    response = client.post("/prototypes/import", files=files)
    assert response.status_code == 201
    validate("prototype.schema.json", response.json())


def test_import_rejects_bad_input() -> None:
    bad_link = client.post(
        "/prototypes/import", json={"source": "figma", "url": "https://evil.com/x"}
    )
    assert (bad_link.status_code, bad_link.json()["detail"]) == (
        422,
        "Link non valido: usa un link Figma o un artifact Claude pubblico.",
    )
    assert (
        client.post("/prototypes/import", json={"source": "altro", "url": "x"}).status_code == 422
    )
    assert client.post("/prototypes/import", content=b"non json").status_code == 422
    figma_file = {"source": (None, "figma"), "file": ("a.html", b"x", "text/html")}
    assert client.post("/prototypes/import", files=figma_file).status_code == 422


def _imported(fake_artifact_client=client) -> dict:
    return client.post("/prototypes/import", json={"source": "artifact", "url": ARTIFACT}).json()


def test_prototype_test_uses_the_chosen_screens_and_runs_on_the_panel(fake_artifact) -> None:
    proto = _imported()
    body = {
        "kind": "prototype",
        "prototype_id": proto["id"],
        "paths": [{"start_id": "s1", "screen_indexes": [0, 2]}],
    }
    created = client.post("/tests", json=body)
    assert created.status_code == 201
    stimuli = created.json()["stimuli"]
    assert [s["screen_index"] for s in stimuli] == [0, 2]
    assert all(s["kind"] == "prototype_screen" and s["image_url"] for s in stimuli)
    done = client.get(f"/tests/{created.json()['id']}").json()
    assert done["status"] == "done"
    assert done["done_count"] == done["total_count"] > 0


def test_prototype_test_rejects_unknown_or_inconsistent_input(fake_artifact) -> None:
    proto = _imported()
    path = {"start_id": "s1", "screen_indexes": [0]}
    cases = [
        {"kind": "prototype", "prototype_id": "nope", "paths": [path]},
        {
            "kind": "prototype",
            "prototype_id": proto["id"],
            "paths": [{"start_id": "s9", "screen_indexes": [0]}],
        },
        {
            "kind": "prototype",
            "prototype_id": proto["id"],
            "paths": [{"start_id": "s1", "screen_indexes": [7]}],
        },
        {"kind": "prototype", "prototype_id": proto["id"], "paths": [path, path]},
        {"kind": "prototype", "prototype_id": proto["id"], "paths": [path] * 4},
        {"kind": "prototype", "prototype_id": proto["id"], "paths": [path], "flow_ids": ["x"]},
        {"kind": "prototype"},
    ]
    assert [client.post("/tests", json=c).status_code for c in cases] == [422] * len(cases)
