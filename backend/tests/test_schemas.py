import json

import pytest
from pydantic import ValidationError

from app import models
from app.loaders import FIXTURES_DIR

FIXTURE_SCHEMAS = {
    "personas.json": "persona.schema.json",
    "flows.json": "flow.schema.json",
    "report_post.json": "report.schema.json",
}


def _load(name: str) -> object:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(("fixture", "schema"), FIXTURE_SCHEMAS.items())
def test_fixture_matches_schema(validate, fixture: str, schema: str) -> None:
    data = _load(fixture)
    items = data if isinstance(data, list) else [data]
    for item in items:
        validate(schema, item)


def test_personas_fixture_has_six_distinct_personas() -> None:
    personas = _load("personas.json")
    assert len(personas) >= 6
    assert len({p["id"] for p in personas}) == len(personas)


def test_flows_fixture_has_onboarding_and_preventivo() -> None:
    ids = {f["id"] for f in _load("flows.json")}
    assert {"onboarding", "preventivo"} <= ids


def test_model_dumps_match_schemas(validate) -> None:
    persona = models.Persona(
        id="p9",
        role="Titolare",
        sector="Edilizia",
        company_size="micro",
        region="Veneto",
        profile="Gestisce il cantiere e la parte commerciale.",
    )
    stimulus = models.Stimulus(id="variante-a", kind="post", variant_label="A", text="Testo.")
    screen = models.Stimulus(
        id="onboarding-0", kind="prototype_screen", flow_id="onboarding", screen_index=0
    )
    response = models.Response(
        persona_id="p9",
        stimulus_id="variante-a",
        thought="Interessante.",
        said="Interessante.",
        score=4,
        objections=[],
    )
    flow = models.Flow(
        id="onboarding", name="Onboarding", screen_count=4, captured_at="2026-10-01T09:00:00+00:00"
    )
    report = models.Report(
        test_id="t1",
        simulated=True,
        summary="Esempio.",
        items=[
            models.ReportItem(
                stimulus_id="variante-a",
                rank=1,
                mean_score=4.0,
                score_distribution={"4": 1},
                objections=[],
                said_summary="Ok.",
                thought_summary="Ok.",
                responses=[response],
            )
        ],
    )
    validate("persona.schema.json", persona.model_dump(mode="json", exclude_none=True))
    validate("stimulus.schema.json", stimulus.model_dump(mode="json", exclude_none=True))
    validate("stimulus.schema.json", screen.model_dump(mode="json", exclude_none=True))
    validate("response.schema.json", response.model_dump(mode="json", exclude_none=True))
    validate("flow.schema.json", flow.model_dump(mode="json", exclude_none=True))
    validate("report.schema.json", report.model_dump(mode="json", exclude_none=True))


def test_persona_rejects_unknown_company_size() -> None:
    with pytest.raises(ValidationError):
        models.Persona(
            id="p9",
            role="Titolare",
            sector="Edilizia",
            company_size="grande",
            region="Veneto",
            profile="Profilo.",
        )
