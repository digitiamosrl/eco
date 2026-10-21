from fastapi.testclient import TestClient

from app import models, store
from app.main import app


def _test(
    test_id: str = "t1", status: str = "queued", done: int = 0, total: int = 2
) -> models.Test:
    return models.Test(
        id=test_id,
        kind="post",
        status=status,
        created_at="2026-10-21T10:00:00+00:00",
        done_count=done,
        total_count=total,
        stimuli=[models.Stimulus(id="variante-a", kind="post", variant_label="A", text="Testo")],
    )


def test_added_test_is_read_back_unchanged() -> None:
    assert store.add_if_idle(_test())
    assert store.get("t1") == _test()


def test_get_unknown_test_returns_none() -> None:
    assert store.get("non-esiste") is None


def test_list_is_most_recent_first() -> None:
    store.add_if_idle(_test("t1", status="done"))
    store.add_if_idle(_test("t2", status="done"))
    assert [t.id for t in store.list_most_recent_first()] == ["t2", "t1"]


def test_add_is_refused_while_a_test_is_active() -> None:
    assert store.add_if_idle(_test("t1", status="queued"))
    assert not store.add_if_idle(_test("t2"))
    store.update("t1", status="done")
    assert store.add_if_idle(_test("t3"))


def test_update_changes_only_the_given_fields() -> None:
    store.add_if_idle(_test("t1"))
    updated = store.update("t1", status="running", done_count=1)
    assert (updated.status, updated.done_count, updated.total_count) == ("running", 1, 2)
    assert store.get("t1") == updated


def test_mark_interrupted_moves_only_active_tests_to_error() -> None:
    store.add_if_idle(_test("t0", status="done"))
    store.add_if_idle(_test("t1", status="running"))
    store.mark_interrupted()
    assert store.get("t0").status == "done"
    interrupted = store.get("t1")
    assert interrupted.status == "error"
    assert interrupted.error == "Il server è stato riavviato durante il test"


def test_startup_marks_interrupted_tests_as_error() -> None:
    store.add_if_idle(_test("t1", status="running"))
    with TestClient(app):
        pass
    assert store.get("t1").status == "error"
