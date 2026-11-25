import base64
import io
import json
import random
from typing import Any, Protocol

import httpx
import pypdfium2 as pdfium
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


_ACTIONS = ("react", "comment", "share", "scroll")
_MISUNDERSTOOD = ("Non capisco cosa succede se clicco qui", "Il prezzo è mensile o annuale?")
_REACTIONS = ("consiglio", "festeggio", "sostengo", "adoro", "perspicace", "divertente")


class Responder(Protocol):
    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response: ...


class FakeResponder:
    """Risposte deterministiche (stesso persona e stimolo, stesso esito), nessuna rete."""

    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response:
        rng = random.Random(f"{persona.id}|{stimulus.id}")
        action = rng.choice(_ACTIONS) if stimulus.kind == "post" else None
        screen = rng.choice([0, 0, 1]) if stimulus.kind == "prototype_screen" else None
        return Response(
            persona_id=persona.id,
            stimulus_id=stimulus.id,
            thought=rng.choice(_THOUGHTS),
            said=rng.choice(_SAID),
            score=rng.randint(1, 5),
            objections=rng.sample(_OBJECTIONS, k=rng.choice([0, 0, 1, 2])),
            action=action,
            reaction=rng.choice(_REACTIONS) if action == "react" else None,
            misunderstood=None if screen is None else rng.sample(_MISUNDERSTOOD, k=screen),
            would_abandon=None if screen is None else rng.random() < 0.3,
        )


_IDS = frozenset({"persona_id", "stimulus_id"})
_FULL_SCHEMA = json.loads(
    (REPO_ROOT / "shared" / "schemas" / "response.schema.json").read_text("utf-8")
)
# Lo schema inviato al modello non chiede gli id: li aggiunge il codice.
# Ordine di generazione: il gesto d'istinto viene deciso prima di formulare cosa si dice,
# altrimenti said ("cosa scriveresti") trascina action verso il commento.
_FIELD_ORDER = ("thought", "action", "reaction", "said", "score", "objections")
_MODEL_PROPERTIES = {k: v for k, v in _FULL_SCHEMA["properties"].items() if k not in _IDS}
_MODEL_SCHEMA = {
    **_FULL_SCHEMA,
    "properties": {
        **{k: _MODEL_PROPERTIES[k] for k in _FIELD_ORDER},
        **{k: v for k, v in _MODEL_PROPERTIES.items() if k not in _FIELD_ORDER},
    },
    "required": [r for r in _FULL_SCHEMA["required"] if r not in _IDS],
}
_IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
_PDF_SUFFIX = ".pdf"
# Un carosello LinkedIn si capisce dalle prime pagine; di più allunga solo il prompt.
MAX_PDF_PAGES = 4
_PDF_SCALE = 1.5  # circa 108 dpi: testo leggibile, immagini leggere
_PDF_MAX_SIDE = 2000  # pixel: una pagina enorme non deve diventare una bitmap da GB
_PDF_ERROR = "Il PDF allegato non è leggibile."
_FILES_PREFIX = "/files/"
_IMAGE_ERROR = "Immagine dello stimolo non disponibile."
_INVALID_OUTPUT = "La risposta della persona non è valida."


def _persona_text(persona: Persona) -> str:
    return (
        f"{persona.role}, {persona.sector}, azienda {persona.company_size} in {persona.region}.\n"
        f"{persona.profile}"
    )


def _data_url_block(mime: str, data: bytes) -> dict[str, Any]:
    encoded = base64.b64encode(data).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}


def _pdf_pages(data: bytes) -> list[bytes]:
    """Prime pagine del PDF come PNG: i modelli locali leggono immagini, non documenti."""
    try:
        document = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        raise LlmError(_PDF_ERROR) from exc
    try:
        images = []
        for i in range(min(len(document), MAX_PDF_PAGES)):
            page = document[i]
            scale = min(_PDF_SCALE, _PDF_MAX_SIDE / max(page.get_size()))
            images.append(page.render(scale=scale).to_pil())
    except pdfium.PdfiumError as exc:
        raise LlmError(_PDF_ERROR) from exc
    finally:
        document.close()
    encoded = []
    for image in images:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded.append(buffer.getvalue())
    return encoded


def _attachment_blocks(image_url: str) -> list[dict[str, Any]]:
    if not image_url.startswith(_FILES_PREFIX):
        raise LlmError(_IMAGE_ERROR)
    path = find_upload(image_url.removeprefix(_FILES_PREFIX))
    if path is None or path.suffix not in {*_IMAGE_TYPES, _PDF_SUFFIX}:
        raise LlmError(_IMAGE_ERROR)
    if path.suffix == _PDF_SUFFIX:
        return [_data_url_block("image/png", page) for page in _pdf_pages(path.read_bytes())]
    return [_data_url_block(_IMAGE_TYPES[path.suffix], path.read_bytes())]


def _stimulus_text(stimulus: Stimulus) -> str:
    if stimulus.kind == "prototype_screen":
        return load_prompt("prototype_screen.md").format(
            step=(stimulus.screen_index or 0) + 1,
            name=stimulus.page_structure or "",
            task=stimulus.task or "",
        )
    return stimulus.text or ""


def _messages(persona: Persona, stimulus: Stimulus) -> list[dict[str, Any]]:
    text = load_prompt("persona_response.md").format(
        persona=_persona_text(persona), stimulus=_stimulus_text(stimulus)
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if stimulus.image_url is not None:
        content.extend(_attachment_blocks(stimulus.image_url))
    return [{"role": "user", "content": content}]


# Facoltativi nello schema condiviso perché valgono solo per un tipo di stimolo: al modello
# si impongono per il tipo giusto, altrimenti un modello locale li omette sempre.
_REQUIRED_BY_KIND = {"post": ("action",), "prototype_screen": ("would_abandon", "misunderstood")}


# Per i post il modello sceglie sempre una reazione, anche "nessuna": facoltativa la saltava
# pure quando reagiva. Il segnaposto non esce dal responder.
_NO_REACTION = "nessuna"
_POST_REACTION = {
    **_MODEL_PROPERTIES["reaction"],
    "enum": [*_MODEL_PROPERTIES["reaction"]["enum"], _NO_REACTION],
}


def _schema_for(stimulus: Stimulus) -> dict[str, Any]:
    extra = _REQUIRED_BY_KIND.get(stimulus.kind, ())
    schema = {**_MODEL_SCHEMA, "required": [*_MODEL_SCHEMA["required"], *extra]}
    if stimulus.kind != "post":
        return schema
    properties = {**schema["properties"], "reaction": _POST_REACTION}
    return {**schema, "properties": properties, "required": [*schema["required"], "reaction"]}


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    """Una reazione vale solo con action react; il segnaposto "nessuna" non si salva."""
    keep = data.get("action") == "react" and data.get("reaction") != _NO_REACTION
    return {k: v for k, v in data.items() if k not in _IDS and (k != "reaction" or keep)}


class LlmResponder:
    def __init__(self, client: httpx.AsyncClient | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model

    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response:
        data = await chat_json(
            self._client or shared_client(),
            model=self._model or settings.persona_model,
            messages=_messages(persona, stimulus),
            schema_name="persona_response",
            schema=_schema_for(stimulus),
        )
        fields = _clean(data)
        try:
            return Response(persona_id=persona.id, stimulus_id=stimulus.id, **fields)
        except ValidationError as exc:
            raise LlmError(_INVALID_OUTPUT) from exc


def build_responder() -> Responder:
    return LlmResponder() if settings.responder == "llm" else FakeResponder()
