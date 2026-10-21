from fastapi import APIRouter, HTTPException

from app import store
from app.loaders import load_one
from app.models import Report, Test

router = APIRouter()

REPORT_POST = load_one("report_post.json", Report)


def _post_report(test: Test) -> Report:
    template = REPORT_POST.items[0]
    items = [
        template.model_copy(
            update={
                "stimulus_id": stimulus.id,
                "rank": rank,
                "responses": [
                    response.model_copy(update={"stimulus_id": stimulus.id})
                    for response in template.responses
                ],
            }
        )
        for rank, stimulus in enumerate(test.stimuli, start=1)
    ]
    return REPORT_POST.model_copy(update={"test_id": test.id, "items": items})


@router.get(
    "/tests/{test_id}/report",
    response_model=Report,
    response_model_exclude_none=True,
)
def get_report(test_id: str) -> Report:
    test = store.get(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test non trovato")
    if test.status != "done":
        raise HTTPException(status_code=409, detail="Il test non è ancora completato")
    if test.kind == "prototype":
        raise HTTPException(status_code=501, detail="Report del prototipo non ancora disponibile")
    return _post_report(test)
