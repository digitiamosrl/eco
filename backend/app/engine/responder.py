import random
from typing import Protocol

from app.config import settings
from app.models import Persona, Response, Stimulus

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


class LlmResponder:
    # shortcut: stub senza provider, sostituire con il provider AI (parte AI, dopo il backend)
    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response:
        raise NotImplementedError("Provider AI non ancora configurato")


def build_responder() -> Responder:
    return LlmResponder() if settings.responder == "llm" else FakeResponder()
