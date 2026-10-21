from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Persona(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    role: str
    sector: str
    company_size: Literal["micro", "piccola", "media"]
    region: str
    profile: str


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


class Report(BaseModel):
    model_config = ConfigDict(frozen=True)

    test_id: str
    simulated: Literal[True]
    summary: str
    items: list[ReportItem]


class Variant(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str = Field(min_length=1)
    text: str = Field(min_length=1)


class PostTestRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["post"]
    variants: list[Variant] = Field(min_length=2, max_length=5)

    @field_validator("variants")
    @classmethod
    def labels_are_unique(cls, variants: list[Variant]) -> list[Variant]:
        labels = [v.label.lower() for v in variants]
        if len(set(labels)) != len(labels):
            raise ValueError("etichette duplicate")
        return variants


class PrototypeTestRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["prototype"]
    flow_ids: list[str] = Field(min_length=1)

    @field_validator("flow_ids")
    @classmethod
    def flow_ids_are_unique(cls, flow_ids: list[str]) -> list[str]:
        if len(set(flow_ids)) != len(flow_ids):
            raise ValueError("flussi duplicati")
        return flow_ids


CreateTestRequest = Annotated[PostTestRequest | PrototypeTestRequest, Field(discriminator="kind")]
