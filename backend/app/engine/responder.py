import base64
import json
import random
from typing import Any, Protocol

import httpx
from pydantic import ValidationError

from app.config import REPO_ROOT, settings
from app.engine.llm_client import LlmError, chat_json, load_prompt, shared_client
from app.models import Persona, Response, Stimulus
from app.uploads import find_upload

_THOUGHTS = (
    "Non capisco bene a chi si rivolge.",
    "Mi sembra una cosa già vista.",
    "Ci penserei un attimo prima di rispondere.",
    "Questo mi interessa, ma non mi convince del tutto.",
)
_SAID = (
    "Interessante, vediamo come va.",
    "Non sono sicuro che faccia per noi.",
    "Chiaro, anche se manca qualcosa.",
    "Lo condividerei con il team.",
)
_OBJECTIONS = (
    "Non si capisce il beneficio.",
    "Il tono è troppo generico.",
    "Manca un riferimento concreto.",
)


class Responder(Protocol):
    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response: ...


class FakeResponder:
    """Risposte deterministiche (stesso persona e stimolo, stesso esito), nessuna rete."""

    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response:
        rng = random.Random(f"{persona.id}|{stimulus.id}")
        return Response(
            persona_id=persona.id,
            stimulus_id=stimulus.id,
            thought=rng.choice(_THOUGHTS),
            said=rng.choice(_SAID),
            score=rng.randint(1, 5),
            objections=rng.sample(_OBJECTIONS, k=rng.choice([0, 0, 1, 2])),
        )


_IDS = frozenset({"persona_id", "stimulus_id"})
_FULL_SCHEMA = json.loads(
    (REPO_ROOT / "shared" / "schemas" / "response.schema.json").read_text("utf-8")
)
# Lo schema inviato al modello non chiede gli id: li aggiunge il codice.
_MODEL_SCHEMA = {
    **_FULL_SCHEMA,
    "properties": {k: v for k, v in _FULL_SCHEMA["properties"].items() if k not in _IDS},
    "required": [r for r in _FULL_SCHEMA["required"] if r not in _IDS],
}
_IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
_FILES_PREFIX = "/files/"
_IMAGE_ERROR = "Immagine dello stimolo non disponibile."
_INVALID_OUTPUT = "La risposta della persona non è valida."


def _persona_text(persona: Persona) -> str:
    return (
        f"{persona.role}, {persona.sector}, azienda {persona.company_size} in {persona.region}.\n"
        f"{persona.profile}"
    )


def _image_block(image_url: str) -> dict[str, Any]:
    if not image_url.startswith(_FILES_PREFIX):
        raise LlmError(_IMAGE_ERROR)
    path = find_upload(image_url.removeprefix(_FILES_PREFIX))
    if path is None or path.suffix not in _IMAGE_TYPES:
        raise LlmError(_IMAGE_ERROR)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{_IMAGE_TYPES[path.suffix]};base64,{encoded}"},
    }


def _messages(persona: Persona, stimulus: Stimulus) -> list[dict[str, Any]]:
    text = load_prompt("persona_response.md").format(
        persona=_persona_text(persona),
        stimulus=stimulus.text or stimulus.page_structure or "",
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if stimulus.image_url is not None:
        content.append(_image_block(stimulus.image_url))
    return [{"role": "user", "content": content}]


class LlmResponder:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response:
        data = await chat_json(
            self._client or shared_client(),
            model=settings.persona_model,
            messages=_messages(persona, stimulus),
            schema_name="persona_response",
            schema=_MODEL_SCHEMA,
        )
        fields = {k: v for k, v in data.items() if k not in _IDS}
        try:
            return Response(persona_id=persona.id, stimulus_id=stimulus.id, **fields)
        except ValidationError as exc:
            raise LlmError(_INVALID_OUTPUT) from exc


def build_responder() -> Responder:
    return LlmResponder() if settings.responder == "llm" else FakeResponder()
