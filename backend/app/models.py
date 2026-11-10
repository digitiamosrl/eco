from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Persona(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    role: str
    sector: str
    company_size: Literal["micro", "piccola", "media", "grande"]
    region: str
    profile: str
    ai_attitude: (
        Literal["entusiasta", "curiosa", "pragmatica", "scettica", "indifferente"] | None
    ) = None
    linkedin_use: Literal["legge", "ogni_tanto", "partecipa", "solo_contatti"] | None = None


class Stimulus(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: Literal["post", "prototype_screen"]
    variant_label: str | None = None
    text: str | None = None
    image_url: str | None = None
    flow_id: str | None = None
    screen_index: int | None = Field(default=None, ge=0)
    page_structure: str | None = None
    attachment_kind: Literal["image", "pdf"] | None = None


class Response(BaseModel):
    model_config = ConfigDict(frozen=True)

    persona_id: str
    stimulus_id: str
    thought: str
    said: str
    score: int = Field(ge=1, le=5)
    objections: list[str]
    misunderstood: list[str] | None = None
    would_abandon: bool | None = None
    action: Literal["react", "comment", "share", "scroll"] | None = None
    reaction: (
        Literal["consiglio", "festeggio", "sostengo", "adoro", "perspicace", "divertente"] | None
    ) = None


class Test(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: Literal["post", "prototype"]
    status: Literal["queued", "running", "done", "error"]
    created_at: str
    done_count: int = Field(ge=0)
    total_count: int = Field(ge=0)
    stimuli: list[Stimulus]
    error: str | None = None


class Flow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    screen_count: int = Field(ge=1)
    captured_at: str


class ReportItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    stimulus_id: str
    rank: int = Field(ge=1)
    mean_score: float
    score_distribution: dict[str, int]
    objections: list[str]
    said_summary: str
    thought_summary: str
    responses: list[Response]
    divergent_persona_ids: list[str]


class Fidelity(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=-1, le=1)
    basis: str = Field(min_length=1)


class Report(BaseModel):
    model_config = ConfigDict(frozen=True)

    test_id: str
    simulated: Literal[True]
    summary: str
    items: list[ReportItem]
    fidelity: Fidelity | None = None


class Variant(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str = Field(min_length=1)
    text: str = Field(min_length=1)


class PrototypeScreen(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=0)
    name: str
    image_url: str


class PrototypeStart(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    screens: list[PrototypeScreen]


class Prototype(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    source: Literal["figma", "artifact"]
    name: str
    imported_at: str
    starts: list[PrototypeStart]


class PostTestRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["post"]
    variants: list[Variant] = Field(min_length=1, max_length=5)

    @field_validator("variants")
    @classmethod
    def labels_are_unique(cls, variants: list[Variant]) -> list[Variant]:
        labels = [v.label.lower() for v in variants]
        if len(set(labels)) != len(labels):
            raise ValueError("etichette duplicate")
        return variants


class PrototypePath(BaseModel):
    model_config = ConfigDict(frozen=True)

    start_id: str
    screen_indexes: list[Annotated[int, Field(ge=0)]] = Field(min_length=1, max_length=8)


class PrototypeTestRequest(BaseModel):
    """Prototipo importato (`prototype_id` e `paths`) oppure flusso già catturato (`flow_ids`)."""

    model_config = ConfigDict(frozen=True)

    kind: Literal["prototype"]
    prototype_id: str | None = None
    paths: list[PrototypePath] | None = Field(default=None, min_length=1, max_length=3)
    flow_ids: list[str] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def one_source(self) -> "PrototypeTestRequest":
        imported = self.prototype_id is not None and self.paths is not None
        if imported == (self.flow_ids is not None):
            raise ValueError("indica prototype_id e paths, oppure flow_ids")
        if self.paths is not None:
            starts = [p.start_id for p in self.paths]
            if len(set(starts)) != len(starts):
                raise ValueError("percorsi duplicati")
        return self

    @field_validator("flow_ids")
    @classmethod
    def flow_ids_are_unique(cls, flow_ids: list[str] | None) -> list[str] | None:
        if flow_ids is not None and len(set(flow_ids)) != len(flow_ids):
            raise ValueError("flussi duplicati")
        return flow_ids


CreateTestRequest = Annotated[PostTestRequest | PrototypeTestRequest, Field(discriminator="kind")]
