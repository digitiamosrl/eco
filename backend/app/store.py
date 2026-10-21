from app.models import Test

# shortcut: in-memory, passare a SQLite con il runner reale (B3)
_TESTS: dict[str, Test] = {}


def reset() -> None:
    _TESTS.clear()


def add(test: Test) -> None:
    _TESTS[test.id] = test


def get(test_id: str) -> Test | None:
    return _TESTS.get(test_id)


def list_most_recent_first() -> list[Test]:
    return list(reversed(_TESTS.values()))


def has_active() -> bool:
    return any(t.status in ("queued", "running") for t in _TESTS.values())


def update(test_id: str, **changes: object) -> Test:
    updated = _TESTS[test_id].model_copy(update=changes)
    _TESTS[test_id] = updated
    return updated
